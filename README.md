# sports-edge

End-to-end starter scaffold for AI-assisted sports betting **research & tracking** (no automated bet placement).  
Designed so you can hand this to **Claude Code** and start implementing immediately.

## What you get
- **Next.js dashboard** (Vercel-ready) for read-only analytics
- **Python ETL & modeling** package with sample data
- **Postgres schema** migration
- **GitHub Actions** cron workflows (ETL, models, signals, settlement)
- **Docs** that map to your plan

## Quickstart

### 1) Prereqs
- Node 18+ and pnpm (or npm)
- Python 3.10+
- Postgres (Neon/Supabase recommended)

### 2) Setup env
Copy `.env.template` to `.env` in root AND to `apps/dashboard/.env.local`, then fill values.

```bash
cp .env.template .env
cp .env.template apps/dashboard/.env.local
```

### 3) Install deps
```bash
# JS deps
cd apps/dashboard
npm install
cd ../..

# Python deps
python3 -m venv .venv
source .venv/bin/activate
pip install -r packages/models/requirements.txt
```

### 4) Create DB schema
Run the SQL in `infra/migrations/0001_init.sql` against your Postgres.  
For Supabase/Neon, paste into the SQL editor or run via psql.

### 5) Seed sample data (optional)
```bash
python ops/scripts/odds_etl.py --from-csv data/sample_odds.csv
python ops/scripts/generate_signals.py
python ops/scripts/settle_results.py --from-csv data/sample_results.csv
```

### 6) Start dashboard (local)
```bash
cd apps/dashboard
npm run dev
```
Open http://localhost:3000

### 7) Deploy
- **Dashboard:** push to GitHub → import repo in Vercel → set env vars → deploy
- **Cron jobs:** GitHub Actions workflows in `ops/workflows/` (adjust schedules and secrets)

---

## Where Claude Code should start

1. **Back end**
   - Implement real odds ingestion adapters (ToS-compliant) in `ops/scripts/odds_etl.py`.
   - Build model feature generation in `packages/models/models/features.py`.
   - Implement baseline models in `packages/models/models/prop_models.py`.
2. **Front end**
   - Wire `/signals` and `/bets` pages to Postgres (read-only).
   - Build charts (CLV trends) using Recharts.

See `docs/` for split plan files.
