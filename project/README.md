# Aware Analytical Tool for Safe Driving Speed in Adverse Weather Conditions

Full-stack ML-powered web app that recommends a safe driving speed in real time based on live weather, traffic, and road conditions — with an explainable-AI (XAI) breakdown of *why*.

```
project/
├── backend/       FastAPI REST + WebSocket API, JWT auth, PostgreSQL
├── ml_model/       Trained ML models (Gradient Boosting, 97.97% R²) + SHAP explainer
├── frontend/       React + TypeScript dashboard, live map-ready, real-time via WebSocket
└── docker-compose.yml   Runs all three together
```

---

## Fastest way to run this — Docker (recommended)

You need Docker Desktop installed (docker.com/products/docker-desktop) — that's it, no Python/Node setup needed.

1. In the project root, create a file named `.env` with:
   ```
   SECRET_KEY=<run: python -c "import secrets; print(secrets.token_hex(32))">
   OPENWEATHER_API_KEY=<from openweathermap.org/api>
   TOMTOM_API_KEY=<from developer.tomtom.com>
   ```
2. Run:
   ```bash
   docker compose up --build
   ```
3. Open:
   - Frontend: **http://localhost**
   - API docs: **http://localhost:8000/docs**

That's it — Postgres, the FastAPI backend, and the React frontend all start together, wired to each other, with the pre-trained ML model already loaded.

**This already gives you "real-time" and "24/7":**
- Real-time: the dashboard opens a WebSocket to `/api/ws/predict` and streams live speed recommendations as your (browser) GPS position updates
- 24/7: every service in `docker-compose.yml` has `restart: always` — if a container crashes, Docker restarts it automatically. As long as the machine running Docker stays on, the app stays up.

---

## Running without Docker (manual, for development)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # fill in SECRET_KEY, DATABASE_URL, API keys
uvicorn app.main:app --reload
```

**Frontend** (separate terminal):
```bash
cd frontend
npm install
npm run dev
```
Open **http://localhost:5173** — Vite's dev server proxies `/api` calls to the backend automatically (see `frontend/vite.config.ts`).

---

## Making it available 24/7 on the internet (not just your laptop)

Your laptop being on isn't a real "24/7" deployment — for that, you need a hosting provider. This is the one part that needs your own account (I can't create accounts on your behalf). Steps:

1. **Database** — supabase.com → New Project → free tier → copy the connection string from Project Settings → Database
2. **Backend** — railway.app or render.com → New → Deploy from GitHub (push this `backend/` folder to a GitHub repo first) → set the same environment variables as your local `.env`, pointing `DATABASE_URL` at Supabase → these platforms keep your app running continuously and auto-restart it on crash
3. **Frontend** — vercel.com → Import your GitHub repo → set root directory to `frontend/` → Vercel builds and hosts it globally, always-on, free tier
4. **Keep the free-tier backend awake** — Render/Railway free tiers can sleep after inactivity. Add a free uptimerobot.com monitor pinging your `/health` endpoint every 5 minutes — this keeps it warm and also alerts you by email if it ever actually goes down

I'll walk through each of these in detail (exact click-by-click) whenever you're ready to deploy — Phase 7 of the original plan.

---

## What's built and tested right now

- ✅ Backend: 13 REST endpoints + 1 WebSocket route, all verified against the OpenAPI schema
- ✅ ML: 4 models trained and compared, Gradient Boosting selected (R²=0.98, MAE=2.47 km/h), SHAP explainer verified on a real scenario
- ✅ Frontend: builds cleanly with zero TypeScript errors (`npm run build` passes), login/register/dashboard/history pages, live WebSocket dashboard, CSV export
- ⏳ Not yet built: live map (Leaflet) with route overlays, admin panel UI, automated tests, CI/CD, full deployment — these are Phases 4 (remainder)–9

## Default login flow to try it
1. Open the app → Register with any name/email/password (8+ chars)
2. You'll land on the Dashboard — it'll ask for location permission (allow it for real GPS, or it defaults to Hyderabad)
3. Watch the "Recommended Safe Speed" update live every 5 seconds
4. Click "Save this prediction" to store it, then check the History page
