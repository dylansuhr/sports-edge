# SportsEdge - Project Context for Claude Code

**Last Updated:** October 10, 2025
**Status:** Production-Ready with Autonomous Learning System (Self-optimizing ✅)

---

## Project Overview

SportsEdge is an **AI-assisted sports betting research platform** for analyzing betting opportunities with human-in-the-loop decision making. **No automated bet placement** - this is a signals-only system for responsible betting research.

**Key Principle:** Generate signals → Human reviews → Manual bet placement → Track results

---

## Tech Stack

- **Backend:** Python 3.10+ (ETL, modeling, signal generation)
- **Frontend:** Next.js 14 (read-only dashboard)
- **Database:** PostgreSQL (Neon) - 11 tables
- **Data Source:** The Odds API (ToS-compliant)
- **Automation:** Makefile commands, GitHub Actions (active)

---

## Quick Reference

### Essential Commands

```bash
# Daily operations (with venv activated)
make etl         # Fetch latest odds (NFL, NBA, NHL)
make signals     # Generate betting signals (14-day window, with vig removal)
make dashboard   # Start dashboard (localhost:3000)
make settle      # Settle completed games and update ELO
make clv         # Capture closing lines (run 10-30 min before games)
make clv-report  # Generate CLV performance report

# Database
make migrate     # Run migrations
make db-ping     # Test connection

# Development
make install     # Install all dependencies
make verify      # Verify system health
```

### Environment Variables

**Required:**
- `DATABASE_URL` - Write access (ETL/signals)
- `DATABASE_READONLY_URL` - Read-only (dashboard)
- `THE_ODDS_API_KEY` - From the-odds-api.com
- `USE_API=true`
- `LEAGUES=nfl,nba,nhl`

**Configuration:**
- `SIGNAL_LOOKAHEAD_HOURS=336` (14 days)
- `EDGE_SIDES=0.02` (2% min edge)
- `KELLY_FRACTION=0.25` (¼-Kelly)
- `BANKROLL=1000.0`

---

## Architecture Principles

### 1. API-Only Data Flow

```
The Odds API → ETL → Database → Signal Generation → Dashboard
                                        ↓
                                 Settlement → ELO Updates
```

**No CSV fallbacks** - If API fails, log error and exit.

### 2. Database Layer - Idempotent Operations

All writes go through `packages/shared/shared/db.py`:
- `upsert_team()`, `upsert_game()`, `upsert_market()` - Prevent duplicates
- `bulk_insert_odds_snapshots()` - Batch inserts
- `insert_signal()` - Write betting signals
- Safe to re-run scripts without creating duplicates

### 3. Signal Generation Flow

```
Odds → ELO Model → Fair Probability → Edge Calculation → Signal (if ≥ threshold)
```

**Per-Selection Fair Probabilities:**
- Moneyline: `p_home` for home, `p_away = 1 - p_home` for away
- Spread: Team-specific cover probability
- Total: `P(Over)` for Over, `P(Under)` for Under

**Key Fix (Oct 8):** Each selection gets its own fair probability (was causing 40%+ edges, now 11%)

### 4. Sport-Specific Risk Management

- **NFL:** Signals expire 48h before game (injury volatility)
- **NBA:** Signals expire 24h before game (lineup changes)
- **NHL:** Signals expire 36h before game (balanced)

### 5. ELO Rating System

- Initial: 1500
- K-factor: 20
- Home advantage: +25 points
- Updates after each settlement
- Tracked in `elo_history` table

### 6. Automated Workflows (GitHub Actions)

**Active Automation:**
- **Odds ETL:** Every 15 minutes, 7 days/week (NFL, NBA, NHL)
- **Signal Generation:** Every 20 minutes, 7 days/week (all sports)
- **Settlement:** Daily at 2 AM ET (settles bets, updates ELO + team ratings)
- **CLV Capture:** Every 30 minutes (closing lines before games start)
- **Performance Analysis:** Sundays 9 AM ET (weekly analysis + auto-tuning recommendations)

**Configuration:** Workflows in `.github/workflows/` use GitHub Secrets for credentials

### 7. Dashboard UI

- **Framework:** Next.js 14 with CSS Modules, Recharts for visualization
- **Pages:**
  - `/signals` - Sortable signal table with sport tabs, automation status timers
  - `/performance` - Model performance dashboard with line charts and readiness indicator
  - `/bets` - Manual bet tracking (placeholder)
- **Features:**
  - Model Readiness Card: Visual status (Ready/Monitor/Not Ready/Insufficient Data)
  - CLV Trend Chart: 30-day performance history
  - Beat Closing % Chart: Track market-beating percentage
  - Performance by Sport/Market: Bar charts showing segment-level CLV
  - Navigation bar with active page highlighting
- **Styling:** Dark theme with terminal aesthetic, monospace fonts, color-coded signals/charts

---

## File Structure

### Python Packages (Backend)

```
packages/
├── providers/
│   ├── theoddsapi.py       # The Odds API integration
│   └── results.py           # Game results provider
├── shared/shared/
│   ├── db.py                # Database operations (idempotent)
│   ├── odds_math.py         # Probability calculations
│   └── utils.py             # Error handling utilities
└── models/models/
    ├── features.py          # ELO system, feature generation
    └── prop_models.py       # Fair probability models
```

###

 Scripts (Operations)

```
ops/scripts/
├── odds_etl_v2.py           # **USE THIS** - API-only ETL
├── generate_signals_v2.py   # **USE THIS** - Signal generation
├── settle_results_v2.py     # Bet settlement + ELO updates
└── verify_setup.py          # System health check
```

### Dashboard (Frontend)

```
apps/dashboard/
├── app/
│   ├── signals/
│   │   ├── page.tsx         # Server component (data fetching)
│   │   └── SignalsClient.tsx # Client component (sortable table, tabs)
│   ├── globals.css          # Dark theme CSS variables
│   └── bets/page.tsx        # Bet history (placeholder)
├── components/
│   ├── AutomationStatus.tsx # Live countdown timers for workflows
│   └── AutomationStatus.module.css # CSS Module styling
├── actions/
│   └── signals.ts           # Database queries (read-only)
└── lib/
    └── db.ts                # Read-only connection
```

### Infrastructure

```
infra/migrations/
├── 0001_init.sql            # Full schema (11 tables)
└── 0004_add_selection_to_odds.sql  # Selection tracking (critical fix)

.github/workflows/
├── odds_etl.yml             # Automated odds fetching (15 min)
├── generate_signals.yml     # Automated signal generation (20 min)
└── settle_results.yml       # Automated settlement (daily 2 AM ET)
```

### Documentation

```
CLAUDE.md                    # This file - high-level overview
COMPLIANCE.md                # Legal and ToS compliance
claude/ROADMAP.md            # Detailed roadmap, current status, next steps
```

---

## Current System Status

### ✅ What's Working (100% Operational)

1. **Multi-Sport ETL** - NFL, NBA, NHL odds from The Odds API
2. **Per-Selection Fair Probabilities** - Each selection gets accurate probability
3. **Vig Removal** - Multiplicative devigging (1.26% avg reduction)
4. **Team-Specific Totals** - Exponential moving average offensive/defensive ratings
5. **Signal Generation** - 800+ active signals with early-season filters
6. **Sport-Specific Expiry** - Risk-aware signal lifetimes
7. **CLV Tracking** - Closing line capture + performance analysis
8. **Autonomous Learning** - Self-analyzing, self-tuning model
9. **Performance Dashboard** - Visual readiness indicator + trend charts
10. **ELO System** - Dynamic ratings that update on settlement

### ⚠️ Model Calibration Period

1. **High edges (10-11% avg)** - Expected until ELOs diverge (need 50+ settled games per team)
2. **Team ratings initializing** - Offensive/defensive ratings improve after each game
3. **Waiting for CLV data** - Need 100+ settled signals for reliable readiness indicator
4. **Do not bet yet** - Let model learn autonomously until performance dashboard shows "Ready"

---

## Key Design Decisions

### Why These Choices?

**¼-Kelly over full Kelly:** Reduces variance, safer for small bankrolls
**1% max stake:** Prevents over-betting even when Kelly suggests more
**20% edge cap:** Flags outliers for manual review (likely model errors)
**14-day window:** Balances early line value with signal freshness
**Per-selection probabilities:** Critical for accurate edge calculations
**Idempotent operations:** Safe to re-run scripts anytime

---

## Critical Rules - DO NOT VIOLATE

### Compliance

1. **NO automated bet placement code paths**
2. Dashboard uses `DATABASE_READONLY_URL` (separate read-only role)
3. **NEVER log or commit API keys**
4. Respect The Odds API quota (500 req/month free tier)
5. Rate limit: 6s minimum between requests

### Code Quality

1. **All database writes through `db.py`** (no raw SQL inserts in scripts)
2. **Idempotent operations** - scripts must be safe to re-run
3. **Per-selection fair probabilities** - never share probs across selections
4. **Environment-based config** - no hardcoded thresholds
5. **Immutable odds_snapshots** - NEVER UPDATE, always INSERT

### Security

1. **Secrets in `.env` only** (never committed)
2. **Read-only role for dashboard** (separate credentials)
3. **No credentials in logs** (mask with `xxxxx...`)

---

## Common Tasks

### Adding a New Sport

1. Add sport key to `theoddsapi.py` sport mapping
2. Run ETL: `make etl` or `python ops/scripts/odds_etl_v2.py --leagues <sport>`
3. Generate signals: `make signals`
4. Update `LEAGUES` in `.env` for automation

### Debugging No Signals

1. Check `odds_snapshots` has recent data: `SELECT COUNT(*) FROM odds_snapshots WHERE fetched_at > NOW() - INTERVAL '24 hours'`
2. Check games in window: `SELECT COUNT(*) FROM games WHERE scheduled_at BETWEEN NOW() AND NOW() + INTERVAL '14 days'`
3. Lower threshold for testing: `EDGE_SIDES=0.01 make signals`
4. Check model logs for "No model available" errors

### Updating Models

- **ELO parameters:** Edit `packages/models/models/features.py` (K-factor, home advantage)
- **Fair probability logic:** Edit `ops/scripts/generate_signals_v2.py` (`calculate_fair_probability()` method)
- **Edge thresholds:** Update `.env` (`EDGE_SIDES`, `EDGE_PROPS`)

---

## Performance Expectations

### Runtime

- **ETL:** ~30 seconds per sport
- **Signal Generation:** 1-3 minutes per sport (5-8 min for all three)
- **Settlement:** ~10 seconds
- **Dashboard load:** <2 seconds

### Volume

- **Signals per day:** 800-1500 (depends on schedule)
- **API requests per ETL run:** ~10-15 (3 leagues × 3 markets)
- **Database growth:** ~2MB per day (odds snapshots)

---

## Error Handling Philosophy

1. **Fail fast on critical errors** (missing API key, DB connection)
2. **Graceful degradation on non-critical errors** (skip one game, continue processing)
3. **Structured logging** (include context: game, market, sportsbook)
4. **Retry with backoff** (3 attempts, exponential backoff)

---

## Next Steps (Phase 1 Enhancements)

See `claude/ROADMAP.md` for full details. Top priorities:

1. **Vig Removal** - Implement paired vig removal (reduces edges 2-4%)
2. **Team-Specific Total Models** - Replace league averages with team offensive/defensive ratings
3. **Weather & Injury Integration** - Real-time data for NFL

---

## Resources

- **The Odds API Docs:** https://the-odds-api.com/liveapi/guides/v4/
- **PostgreSQL NUMERIC Types:** https://www.postgresql.org/docs/current/datatype-numeric.html
- **Kelly Criterion:** https://www.investopedia.com/articles/trading/04/091504.asp
- **CLV Explained:** https://www.pinnacle.com/en/betting-articles/betting-strategy/what-is-closing-line-value

---

## Support & Troubleshooting

**Full troubleshooting guide:** See `claude/ROADMAP.md` section "Troubleshooting"

**Quick diagnostics:**
```bash
make verify      # System health check
make db-ping     # Test database connection
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM signals WHERE status='active'"  # Check signals
```

---

**Built with:** Python 3.10+, PostgreSQL, Next.js 14, The Odds API
**License:** Private (not for redistribution)
**Maintainer:** Dylan Suhr
