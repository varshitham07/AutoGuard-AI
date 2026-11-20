# AutoGuard AI Mechanic

The AI Mechanic page is served by the local FastAPI backend and requires a signed-in user.

## What works without an AI provider key

The built-in guidance mode:
- Explains a limited set of common topics such as brakes, overheating, battery starting issues, warning lights and tyres.
- Looks up the signed-in user's own saved maintenance work orders and tyre checks.
- Can restrict the context to one selected vehicle.
- Clearly identifies when a repair record is missing.

This fallback is intentionally limited. It is not a general-purpose language model and does not diagnose a vehicle.

## Optional generative AI connection

To enable full conversational answers, configure an OpenAI API key in the environment of the machine running FastAPI:

**Windows Command Prompt (for the current terminal session):**

```bat
set OPENAI_API_KEY=your_api_key_here
set AUTOGUARD_AI_MODEL=gpt-4o-mini
START_AUTOGUARD_WINDOWS.bat
```

If the server is already running, stop it with Ctrl+C and restart it from that same Command Prompt after setting the variables. Do not paste an API key into the website, GitHub repository, source code, screenshots or chat messages. Keep it private and rotate it if exposed.

The server sends the question and the relevant vehicle/maintenance context to the configured OpenAI API. It excludes account email, owner name and vehicle registration from the assistant context. Provider usage may incur charges and depends on the provider account and its current limits. A ChatGPT subscription is separate from API billing.

If the provider call is unavailable, the endpoint falls back to built-in guidance. The response mode identifies whether generative AI or built-in guidance answered.

## Safety and privacy

- The endpoint requires authentication and checks vehicle ownership before using a selected vehicle.
- The assistant uses saved work orders and tyre checks as records, not proof of a confirmed mechanical diagnosis.
- It must not invent repair history, fault codes, measurements or manufacturer specifications.
- It is decision support only. For brake/steering faults, damaged tyres, fuel leaks, smoke, overheating or loss of control, prioritise stopping safely and professional inspection.
- Do not enter customer secrets, payment details or other sensitive personal information.
