from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Header
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from pathlib import Path
import sqlite3, os, hashlib, hmac, secrets, time, base64, json, csv, io

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

@app.get("/", response_class=HTMLResponse)
def home():
    return (BASE / "web" / "index.html").read_text(encoding="utf-8")

@app.get("/api/health")
def health():
    return {"status":"ok","product":"AutoGuard AI","mode":"local demonstration"}

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
    return {"vehicles":vehicles,"open_work_orders":orders,"model_status":"Validation pending","recent_work_orders":open_orders}

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
    return {"status":status,"flags":flags,"recommendations":advice,"evidence":{"tyre_position":body.tyre_position,"pressure_psi":body.pressure_psi,"temperature_c":body.temperature_c,"speed_kmh":body.speed_kmh},"method":"Transparent rule-based screening","disclaimer":"Demonstration thresholds are not universal safety limits. Configure using OEM and tyre-maker specifications. This screening cannot predict or rule out sudden tyre failure."}

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
