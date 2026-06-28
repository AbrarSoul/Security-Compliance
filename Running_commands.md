# Running Commands

## 1. Start PostgreSQL

From the repository root:

```bash
docker compose up -d postgres
```

## 2. Backend (first time)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
```

## 3. Backend (run)

```bash
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API: http://localhost:8000  
Docs: http://localhost:8000/docs

## 4. Frontend (first time)

```bash
cd frontend
npm install
copy .env.local.example .env.local
```

## 5. Frontend (run)

```bash
cd frontend
npm run dev
```

App: http://localhost:3000

If you see `Cannot find module './305.js'` (or similar) after logout or hot reload, stop the dev server (Ctrl+C), then:

```bash
cd frontend
npm run dev:clean
```

Do not run `npm run build` while `npm run dev` is already running — that corrupts the `.next` cache.
