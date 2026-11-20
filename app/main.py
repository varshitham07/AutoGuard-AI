from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Header
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from pathlib import Path
import sqlite3, os, hashlib, hmac, secrets, time, base64, json, csv, io
from datetime import date

BASE = Path(__file__).resolve().parent.parent
DB_PATH = os.getenv("DATABASE_PATH", str(BASE / "autoguard.db"))
SECRET = os.getenv("APP_SECRET", "local-demo-secret-change-before-deployment").encode()
app = FastAPI(title="AutoGuard AI", version="1.0.0", description="Explainable vehicle-health screening MVP")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, salt TEXT NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'admin', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS vehicles(id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id), vehicle_name TEXT NOT NULL, registration TEXT UNIQUE NOT NULL, vehicle_type TEXT NOT NULL, make_model TEXT DEFAULT '', odometer REAL DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS work_orders(id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id), vehicle_id INTEGER, title TEXT NOT NULL, priority TEXT NOT NULL, description TEXT DEFAULT '', status TEXT NOT NULL DEFAULT 'Open', created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(vehicle_id) REFERENCES vehicles(id));
        CREATE TABLE IF NOT EXISTS tyre_checks(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), vehicle_id INTEGER, tyre_position TEXT NOT NULL, pressure_psi REAL NOT NULL, temperature_c REAL NOT NULL, speed_kmh REAL NOT NULL DEFAULT 0, status TEXT NOT NULL, flags_json TEXT NOT NULL, recommendations_json TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(vehicle_id) REFERENCES vehicles(id));
        CREATE TABLE IF NOT EXISTS model_predictions(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), filename TEXT NOT NULL, row_count INTEGER NOT NULL, flagged_count INTEGER NOT NULL, results_json TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS service_records(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), vehicle_id INTEGER NOT NULL REFERENCES vehicles(id), service_date TEXT NOT NULL, service_type TEXT NOT NULL, odometer REAL NOT NULL, description TEXT DEFAULT '', parts_cost REAL NOT NULL DEFAULT 0, labour_cost REAL NOT NULL DEFAULT 0, next_service_date TEXT, next_service_odometer REAL, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        """)
        # Upgrade databases created by earlier MVP versions without deleting existing records.
        vehicle_cols = {r["name"] for r in c.execute("PRAGMA table_info(vehicles)")}
        if "user_id" not in vehicle_cols:
            c.execute("ALTER TABLE vehicles ADD COLUMN user_id INTEGER REFERENCES users(id)")
        order_cols = {r["name"] for r in c.execute("PRAGMA table_info(work_orders)")}
        if "user_id" not in order_cols:
            c.execute("ALTER TABLE work_orders ADD COLUMN user_id INTEGER REFERENCES users(id)")
init_db()

def hash_pw(password, salt=None):
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 180000)
    return base64.b64encode(salt).decode(), base64.b64encode(digest).decode()

def verify_pw(password, salt, expected):
    _, got = hash_pw(password, base64.b64decode(salt))
    return hmac.compare_digest(got, expected)

def token_for(user):
    payload = base64.urlsafe_b64encode(json.dumps({"id": user["id"], "email": user["email"], "exp": int(time.time())+86400}).encode()).decode().rstrip("=")
    sig = hmac.new(SECRET, payload.encode(), hashlib.sha256).hexdigest()
    return payload + "." + sig

def current_user(authorization: Optional[str] = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Please sign in")
    token = authorization[7:]
    try:
        payload, sig = token.rsplit(".", 1)
        expected = hmac.new(SECRET, payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected): raise ValueError()
        data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        if data["exp"] < time.time(): raise ValueError()
        with db() as c:
            user = c.execute("SELECT id,name,email,role FROM users WHERE id=?", (data["id"],)).fetchone()
        if not user: raise ValueError()
        return dict(user)
    except Exception:
        raise HTTPException(401, "Session invalid or expired")

class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: str
    password: str = Field(min_length=8, max_length=128)
class LoginIn(BaseModel):
    email: str
    password: str
class VehicleIn(BaseModel):
    vehicle_name: str = Field(min_length=2, max_length=80)
    registration: str = Field(min_length=3, max_length=24)
    vehicle_type: str
    make_model: str = ""
    odometer: float = Field(default=0, ge=0)
class ScreenIn(BaseModel):
    vehicle_id: Optional[int] = None
    tyre_position: str
    pressure_psi: float = Field(ge=0, le=300)
    temperature_c: float = Field(ge=-50, le=250)
    speed_kmh: float = Field(default=0, ge=0, le=400)
    manufacturer_min_psi: Optional[float] = None
    manufacturer_max_psi: Optional[float] = None
class WorkOrderIn(BaseModel):
    vehicle_id: Optional[int] = None
    title: str = Field(min_length=3, max_length=120)
    priority: str = "Medium"
    description: str = ""

class AssistantChatIn(BaseModel):
    message: str = Field(min_length=2, max_length=2000)
    vehicle_id: Optional[int] = None

class ServiceRecordIn(BaseModel):
    vehicle_id: int
    service_date: date
    service_type: str = Field(min_length=2, max_length=80)
    odometer: float = Field(ge=0)
    description: str = Field(default="", max_length=1000)
    parts_cost: float = Field(default=0, ge=0)
    labour_cost: float = Field(default=0, ge=0)
    next_service_date: Optional[date] = None
    next_service_odometer: Optional[float] = Field(default=None, ge=0)

@app.get("/", response_class=HTMLResponse)
def home():
    return (BASE / "web" / "index.html").read_text(encoding="utf-8")

@app.get("/api/health")
def health():
    return {"status":"ok","product":"AutoGuard AI","mode":"local demonstration"}

@app.get("/api/model/status")
def get_model_status(user=Depends(current_user)):
    from app.model_service import model_status
    return model_status()

@app.post("/api/model/predict")
async def predict_aps_csv(file: UploadFile = File(...), user=Depends(current_user)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "Please upload a CSV file")
    raw = await file.read()
    if len(raw) > 10 * 1024 * 1024:
        raise HTTPException(413, "Prediction CSV must be smaller than 10 MB")
    try:
        import pandas as pd
        from app.model_service import predict_frame, load_artifact
        if load_artifact() is None:
            raise HTTPException(503, "APS model is not trained on this installation. Follow docs/MODEL_TRAINING.md.")
        frame = pd.read_csv(io.BytesIO(raw), na_values=["na", "NA", ""])
        if frame.empty:
            raise HTTPException(400, "CSV contains no data rows")
        if len(frame) > 500:
            raise HTTPException(400, "Upload up to 500 rows per prediction request")
        if "class" in frame.columns:
            raise HTTPException(400, "Prediction CSV must not contain the class target column")
        results = predict_frame(frame)
        flagged = sum(1 for row in results if row["flagged"])
        with db() as c:
            c.execute(
                "INSERT INTO model_predictions(user_id,filename,row_count,flagged_count,results_json) VALUES(?,?,?,?,?)",
                (user["id"], file.filename, len(results), flagged, json.dumps(results))
            )
        return {
            "filename": file.filename,
            "row_count": len(results),
            "flagged_count": flagged,
            "model": "Scania APS failure classifier",
            "scope": "Heavy-truck APS dataset context only",
            "results": results,
            "disclaimer": "A model alert is a screening recommendation, not a diagnosis. A low score does not guarantee vehicle safety."
        }
    except HTTPException:
        raise
    except UnicodeDecodeError:
        raise HTTPException(400, "CSV must be UTF-8 encoded")
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:
        raise HTTPException(400, f"Could not process prediction CSV: {exc}")

@app.get("/api/model/history")
def model_prediction_history(user=Depends(current_user), limit: int = 20):
    limit = max(1, min(limit, 50))
    with db() as c:
        rows = c.execute(
            "SELECT id,filename,row_count,flagged_count,created_at FROM model_predictions WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (user["id"], limit)
        ).fetchall()
    return [dict(row) for row in rows]

@app.post("/api/auth/register")
def register(body: RegisterIn):
    email = body.email.strip().lower()
    if "@" not in email: raise HTTPException(400, "Enter a valid email address")
    salt, digest = hash_pw(body.password)
    try:
        with db() as c:
            count = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            role = "admin" if count == 0 else "operator"
            cur = c.execute("INSERT INTO users(name,email,salt,password_hash,role) VALUES(?,?,?,?,?)", (body.name.strip(),email,salt,digest,role))
            user = {"id":cur.lastrowid,"name":body.name.strip(),"email":email,"role":role}
    except sqlite3.IntegrityError: raise HTTPException(409, "An account with this email already exists")
    return {"access_token":token_for(user),"token_type":"bearer","user":user}

@app.post("/api/auth/login")
def login(body: LoginIn):
    with db() as c: user = c.execute("SELECT * FROM users WHERE email=?", (body.email.strip().lower(),)).fetchone()
    if not user or not verify_pw(body.password, user["salt"], user["password_hash"]):
        raise HTTPException(401, "Incorrect email or password")
    u = {"id":user["id"],"name":user["name"],"email":user["email"],"role":user["role"]}
    return {"access_token":token_for(u),"token_type":"bearer","user":u}

@app.get("/api/auth/me")
def me(user=Depends(current_user)): return {"user":user}

@app.get("/api/dashboard/summary")
def summary(user=Depends(current_user)):
    with db() as c:
        vehicles = c.execute("SELECT COUNT(*) FROM vehicles WHERE user_id=?", (user["id"],)).fetchone()[0]
        orders = c.execute("SELECT COUNT(*) FROM work_orders WHERE user_id=? AND status!='Completed'", (user["id"],)).fetchone()[0]
        open_orders = [dict(r) for r in c.execute("SELECT w.*,v.registration FROM work_orders w LEFT JOIN vehicles v ON v.id=w.vehicle_id WHERE w.user_id=? ORDER BY w.id DESC LIMIT 5", (user["id"],))]
    try:
        from app.model_service import model_status as read_model_status
        trained = read_model_status()["available"]
    except Exception:
        trained = False
    return {"vehicles":vehicles,"open_work_orders":orders,"model_status":"Trained" if trained else "Training required","recent_work_orders":open_orders}

@app.get("/api/vehicles")
def list_vehicles(user=Depends(current_user)):
    with db() as c: return [dict(r) for r in c.execute("SELECT * FROM vehicles WHERE user_id=? ORDER BY id DESC", (user["id"],))]
@app.post("/api/vehicles")
def add_vehicle(body: VehicleIn, user=Depends(current_user)):
    try:
        with db() as c:
            cur=c.execute("INSERT INTO vehicles(user_id,vehicle_name,registration,vehicle_type,make_model,odometer) VALUES(?,?,?,?,?,?)",(user["id"],body.vehicle_name,body.registration.upper(),body.vehicle_type,body.make_model,body.odometer))
            row=c.execute("SELECT * FROM vehicles WHERE id=?",(cur.lastrowid,)).fetchone()
        return dict(row)
    except sqlite3.IntegrityError: raise HTTPException(409,"Registration number already exists")
@app.delete("/api/vehicles/{vehicle_id}")
def delete_vehicle(vehicle_id:int,user=Depends(current_user)):
    with db() as c:
        c.execute("DELETE FROM work_orders WHERE vehicle_id=? AND user_id=?",(vehicle_id,user["id"]))
        cur=c.execute("DELETE FROM vehicles WHERE id=? AND user_id=?",(vehicle_id,user["id"]))
        if not cur.rowcount: raise HTTPException(404,"Vehicle not found")
    return {"deleted":True}

@app.post("/api/tyres/screen")
def screen_tyre(body:ScreenIn,user=Depends(current_user)):
    if body.vehicle_id is not None:
        with db() as c:
            owned = c.execute("SELECT 1 FROM vehicles WHERE id=? AND user_id=?", (body.vehicle_id,user["id"])).fetchone()
        if not owned: raise HTTPException(404, "Vehicle not found in your workspace")
    flags=[]; advice=[]
    if body.manufacturer_min_psi is not None and body.manufacturer_max_psi is not None and body.manufacturer_min_psi > body.manufacturer_max_psi:
        raise HTTPException(400, "OEM minimum pressure cannot exceed OEM maximum pressure")
    if body.manufacturer_min_psi is not None and body.pressure_psi < body.manufacturer_min_psi:
        flags.append("Pressure below supplied manufacturer minimum"); advice.append("Arrange a safe pressure check and inspect for leakage.")
    if body.manufacturer_max_psi is not None and body.pressure_psi > body.manufacturer_max_psi:
        flags.append("Pressure above supplied manufacturer maximum"); advice.append("Verify pressure against the tyre/vehicle specification.")
    if body.temperature_c >= 90:
        flags.append("High tyre temperature indicator (demonstration threshold)"); advice.append("Stop in a safe location and arrange an inspection; check load, speed and tyre condition.")
    elif body.temperature_c >= 70:
        flags.append("Elevated tyre temperature indicator (demonstration threshold)"); advice.append("Monitor temperature trend and inspect if it persists.")
    if body.pressure_psi <= 0: flags.append("Invalid pressure reading")
    status = "Inspection required" if flags else "No rule-based warning"
    if not flags: advice.append("Continue routine monitoring and compare with vehicle-specific manufacturer guidance.")
    with db() as c:
        c.execute(
            "INSERT INTO tyre_checks(user_id,vehicle_id,tyre_position,pressure_psi,temperature_c,speed_kmh,status,flags_json,recommendations_json) VALUES(?,?,?,?,?,?,?,?,?)",
            (user["id"], body.vehicle_id, body.tyre_position, body.pressure_psi, body.temperature_c, body.speed_kmh, status, json.dumps(flags), json.dumps(advice))
        )
    return {"status":status,"flags":flags,"recommendations":advice,"evidence":{"tyre_position":body.tyre_position,"pressure_psi":body.pressure_psi,"temperature_c":body.temperature_c,"speed_kmh":body.speed_kmh},"method":"Transparent rule-based screening","disclaimer":"Demonstration thresholds are not universal safety limits. Configure using OEM and tyre-maker specifications. This screening cannot predict or rule out sudden tyre failure."}

@app.get("/api/tyres/history")
def tyre_history(user=Depends(current_user), limit:int=50):
    limit = max(1, min(limit, 100))
    with db() as c:
        rows = c.execute(
            "SELECT t.*, v.registration FROM tyre_checks t LEFT JOIN vehicles v ON v.id=t.vehicle_id WHERE t.user_id=? ORDER BY t.id DESC LIMIT ?",
            (user["id"], limit)
        ).fetchall()
    return [{
        **dict(r),
        "flags": json.loads(r["flags_json"]),
        "recommendations": json.loads(r["recommendations_json"])
    } for r in rows]

@app.post("/api/data/preview")
async def preview_csv(file:UploadFile=File(...), user=Depends(current_user)):
    if not file.filename.lower().endswith(".csv"): raise HTTPException(400,"Please upload a CSV file")
    raw=await file.read()
    if len(raw)>8*1024*1024: raise HTTPException(413,"CSV must be smaller than 8 MB")
    try:
        textdata=raw.decode("utf-8-sig")
        reader=csv.DictReader(io.StringIO(textdata))
        columns=reader.fieldnames or []
        rows=[]
        for i,row in enumerate(reader):
            if i<6: rows.append(row)
        with db() as c: total=sum(1 for _ in csv.DictReader(io.StringIO(textdata)))
        return {"filename":file.filename,"row_count":total,"columns":columns,"preview":rows,"size_bytes":len(raw),"status":"Parsed successfully","note":"This is a schema and preview check. No failure labels or predictive model are inferred."}
    except UnicodeDecodeError: raise HTTPException(400,"CSV must be UTF-8 encoded")
    except csv.Error as e: raise HTTPException(400,f"CSV parsing failed: {e}")

@app.get("/api/work-orders")
def get_orders(user=Depends(current_user)):
    with db() as c: return [dict(r) for r in c.execute("SELECT w.*,v.registration FROM work_orders w LEFT JOIN vehicles v ON v.id=w.vehicle_id WHERE w.user_id=? ORDER BY w.id DESC", (user["id"],))]
@app.post("/api/work-orders")
def create_order(body:WorkOrderIn,user=Depends(current_user)):
    if body.priority not in ("Low","Medium","High","Critical"): raise HTTPException(400,"Invalid priority")
    with db() as c:
        if body.vehicle_id is not None:
            owned = c.execute("SELECT 1 FROM vehicles WHERE id=? AND user_id=?", (body.vehicle_id,user["id"])).fetchone()
            if not owned: raise HTTPException(404, "Vehicle not found in your workspace")
        cur=c.execute("INSERT INTO work_orders(user_id,vehicle_id,title,priority,description) VALUES(?,?,?,?,?)",(user["id"],body.vehicle_id,body.title,body.priority,body.description))
        row=c.execute("SELECT * FROM work_orders WHERE id=?",(cur.lastrowid,)).fetchone()
    return dict(row)
@app.patch("/api/work-orders/{order_id}")
def update_order(order_id:int,status:str,user=Depends(current_user)):
    if status not in ("Open","In progress","Completed"): raise HTTPException(400,"Invalid status")
    with db() as c:
        cur=c.execute("UPDATE work_orders SET status=? WHERE id=? AND user_id=?",(status,order_id,user["id"]))
        if not cur.rowcount: raise HTTPException(404,"Work order not found")
    return {"updated":True,"status":status}


@app.post("/api/assistant/chat")
def assistant_chat(body: AssistantChatIn, user=Depends(current_user)):
    """Answer vehicle-maintenance questions using the signed-in user's own records."""
    with db() as c:
        if body.vehicle_id is not None:
            vehicle = c.execute("SELECT id,vehicle_name,vehicle_type,make_model,odometer FROM vehicles WHERE id=? AND user_id=?", (body.vehicle_id,user["id"])).fetchone()
            if not vehicle:
                raise HTTPException(404, "Vehicle not found in your workspace")
            vehicles = [dict(vehicle)]
        else:
            vehicles = [dict(r) for r in c.execute("SELECT id,vehicle_name,vehicle_type,make_model,odometer FROM vehicles WHERE user_id=? ORDER BY id DESC LIMIT 10", (user["id"],))]
        if body.vehicle_id is not None:
            orders = [dict(r) for r in c.execute("SELECT title,priority,description,status,created_at,vehicle_id FROM work_orders WHERE user_id=? AND vehicle_id=? ORDER BY id DESC LIMIT 12", (user["id"], body.vehicle_id))]
            checks = [dict(r) for r in c.execute("SELECT tyre_position,pressure_psi,temperature_c,status,flags_json,recommendations_json,created_at,vehicle_id FROM tyre_checks WHERE user_id=? AND vehicle_id=? ORDER BY id DESC LIMIT 10", (user["id"], body.vehicle_id))]
        else:
            orders = [dict(r) for r in c.execute("SELECT title,priority,description,status,created_at,vehicle_id FROM work_orders WHERE user_id=? ORDER BY id DESC LIMIT 12", (user["id"],))]
            checks = [dict(r) for r in c.execute("SELECT tyre_position,pressure_psi,temperature_c,status,flags_json,recommendations_json,created_at,vehicle_id FROM tyre_checks WHERE user_id=? ORDER BY id DESC LIMIT 10", (user["id"],))]
    context = {"vehicles":vehicles,"recent_work_orders":orders,"recent_tyre_checks":checks}
    question = body.message.strip()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if api_key:
        try:
            import urllib.request
            model = os.getenv("AUTOGUARD_AI_MODEL", "gpt-4o-mini")
            prompt = (
                "You are AutoGuard AI Mechanic, a careful vehicle-maintenance explainer. "
                "Explain technical topics in simple language. Use the supplied owner records when relevant; "
                "never invent service history, fault codes, measurements, or diagnoses. Distinguish possibilities from facts. "
                "Ask a focused follow-up when needed. For brakes, steering, fuel leaks, overheating, tyre damage, "
                "warning lights with severe symptoms, or loss of control, prioritise stopping safely and professional inspection. "
                "Never tell users to work under an unsupported vehicle, bypass safety systems, or drive an unsafe vehicle. "
                "Do not provide model-specific torque/pressure/specification values unless present in reliable supplied context. "
                "If records do not contain the answer, say so clearly. Keep the answer readable with short headings and steps."
            )
            payload = json.dumps({
                "model": model,
                "messages": [
                    {"role":"system","content":prompt},
                    {"role":"user","content":"Owner records (JSON): " + json.dumps(context) + "\n\nQuestion: " + question}
                ],
                "temperature":0.25,
                "max_tokens":650
            }).encode("utf-8")
            request = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=payload,
                headers={"Authorization":"Bearer " + api_key,"Content-Type":"application/json"},
                method="POST"
            )
            with urllib.request.urlopen(request, timeout=25) as response:
                result = json.loads(response.read().decode("utf-8"))
            answer = result["choices"][0]["message"]["content"].strip()
            return {"answer":answer,"mode":"generative_ai","model":model,"records_used":{"vehicles":len(vehicles),"work_orders":len(orders),"tyre_checks":len(checks)}}
        except Exception:
            # Fall back to local guidance if provider configuration/network is unavailable.
            pass
    lower = question.lower()
    recent_orders = orders[:4]
    recent_checks = checks[:3]
    if any(k in lower for k in ("previous repair","last repair","repair history","service history","what was repaired","last service","previous service")):
        if recent_orders:
            lines = [f"- {o['title']} — {o['status']} ({o['created_at']}); priority {o['priority']}." for o in recent_orders]
            answer = "Here are the latest maintenance work orders saved in your AutoGuard account:\n" + "\n".join(lines) + "\n\nThese are recorded work orders, not proof that every repair was completed. Check the status and notes with your workshop."
        else:
            answer = "I couldn't find any maintenance work orders in your account yet. Add a work order after a repair or inspection, and I can refer to it in future questions."
    elif any(k in lower for k in ("tyre","tire","pressure","puncture")):
        if recent_checks:
            c0 = recent_checks[0]
            flags = ", ".join(json.loads(c0["flags_json"])) or "no rule-based warning recorded"
            answer = f"Your latest saved tyre check was {c0['tyre_position']}: {c0['pressure_psi']} PSI and {c0['temperature_c']} °C on {c0['created_at']}. Result: {c0['status']} ({flags}). Compare pressure with the vehicle maker's specification. If a tyre is visibly damaged, losing pressure, hot, or vibrating, stop safely and arrange an inspection."
        else:
            answer = "I don't see a saved tyre check yet. Record the tyre position, pressure and temperature in TyreGuard first. Use the pressure shown on the vehicle's tyre placard or owner's manual—not a generic internet value."
    elif any(k in lower for k in ("brake","braking","steering","wheel wobble")):
        answer = "Brake or steering symptoms can affect vehicle control. Possible causes depend on the exact symptom and vehicle. If braking feels weak, the vehicle pulls, there is grinding, strong vibration, or steering control changes, stop in a safe place and arrange a professional inspection; don't continue a journey to test it. Tell me the vehicle model and whether you hear squealing, grinding, or feel vibration."
    elif any(k in lower for k in ("overheat","overheating","temperature","coolant")):
        answer = "If the temperature warning is on or steam is visible, pull over safely, switch off the engine and let it cool. Do not open a hot radiator or coolant cap. Possible causes include low coolant, a leak, a cooling fan issue or thermostat trouble. Arrange inspection before driving again if it overheated."
    elif any(k in lower for k in ("battery","starting","start","crank")):
        answer = "A slow or failed start can be related to a weak battery, loose/corroded terminals, starter motor or charging-system issue. Note whether dashboard lights are dim and whether you hear clicking. Avoid repeated long cranking; have the battery and charging system tested."
    elif any(k in lower for k in ("engine light","check engine","warning light","fault code","obd")):
        answer = "A warning light needs its exact symbol, colour and any diagnostic trouble code (DTC) to narrow down. A flashing engine light or severe loss of power/noise needs prompt safe stopping and inspection. Share the code and vehicle model; don't replace parts based only on a generic guess."
    else:
        answer = "I can help explain common vehicle symptoms and review records saved in your AutoGuard workspace. Try asking about a brake noise, overheating, starting problem, tyre warning, or your previous maintenance work orders. Include the vehicle make/model and exact symptoms for more useful guidance."
    if vehicles:
        answer += "\n\nVehicles in your workspace: " + "; ".join(f"{v['vehicle_name']} ({v['make_model'] or v['vehicle_type']}, {v['odometer']} km)" for v in vehicles[:3]) + "."
    return {"answer":answer,"mode":"built_in_guidance","model":None,"records_used":{"vehicles":len(vehicles),"work_orders":len(orders),"tyre_checks":len(checks)},"note":"Connect an OpenAI API key on the backend to enable generative conversations. This built-in mode uses limited topic guidance and saved records."}


@app.get("/api/service-records")
def list_service_records(user=Depends(current_user), limit:int=100):
    limit = max(1, min(limit, 200))
    today = date.today().isoformat()
    with db() as c:
        rows = [dict(r) for r in c.execute(
            "SELECT s.*,v.vehicle_name,v.registration,v.odometer AS current_odometer,v.make_model FROM service_records s JOIN vehicles v ON v.id=s.vehicle_id WHERE s.user_id=? ORDER BY s.service_date DESC,s.id DESC LIMIT ?",
            (user["id"],limit)
        )]
    for row in rows:
        due_date = row.get("next_service_date")
        due_km = row.get("next_service_odometer")
        overdue_date = bool(due_date and due_date <= today)
        overdue_km = bool(due_km is not None and row["current_odometer"] >= due_km)
        row["service_status"] = "Due / overdue" if overdue_date or overdue_km else ("Scheduled" if due_date or due_km is not None else "Logged")
        row["total_cost"] = round(float(row["parts_cost"]) + float(row["labour_cost"]), 2)
    return rows

@app.post("/api/service-records")
def create_service_record(body:ServiceRecordIn,user=Depends(current_user)):
    if body.next_service_date and body.next_service_date < body.service_date:
        raise HTTPException(400,"Next service date cannot be earlier than the recorded service date")
    with db() as c:
        vehicle = c.execute("SELECT id,odometer FROM vehicles WHERE id=? AND user_id=?",(body.vehicle_id,user["id"])).fetchone()
        if not vehicle:
            raise HTTPException(404,"Vehicle not found in your workspace")
        if body.odometer < 0:
            raise HTTPException(400,"Odometer cannot be negative")
        cur = c.execute(
            "INSERT INTO service_records(user_id,vehicle_id,service_date,service_type,odometer,description,parts_cost,labour_cost,next_service_date,next_service_odometer) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (user["id"],body.vehicle_id,body.service_date.isoformat(),body.service_type.strip(),body.odometer,body.description,body.parts_cost,body.labour_cost,body.next_service_date.isoformat() if body.next_service_date else None,body.next_service_odometer)
        )
        row = c.execute("SELECT * FROM service_records WHERE id=?",(cur.lastrowid,)).fetchone()
    return {**dict(row),"total_cost":round(body.parts_cost+body.labour_cost,2),"service_status":"Scheduled" if body.next_service_date or body.next_service_odometer is not None else "Logged"}
