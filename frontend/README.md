# Compliance Dashboard (Frontend)

Next.js dashboard for the Security Compliance API.

## Features

- User authentication (login / signup)
- Upload CSV, JSON, TXT datasets
- Run compliance scans and view risk scores
- Browse findings and recommendations
- Generate and download JSON / PDF reports

## Setup

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Open http://localhost:3000

Ensure the backend is running at http://localhost:8000 with CORS allowing `http://localhost:3000`.

## Scripts

- `npm run dev` — development server (port 3000)
- `npm run build` — production build
- `npm run start` — serve production build
