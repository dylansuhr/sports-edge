# SportsEdge - Project Context for Claude Code

**Last Updated:** October 15, 2025
**Status:** Production-Ready with Paper Betting System (AI-Powered Mock Betting ✅)
**Recent Fixes:** Dashboard performance optimization, PostgreSQL NUMERIC type handling, CI/CD automation fixes
**New Feature:** 🎁 Promo tracking system planned for Phase 3 (Month 9)

---

## Project Overview

SportsEdge is an **AI-assisted sports betting research platform** with autonomous paper betting validation. The system includes:
1. **Signal Generation** - AI analyzes odds and generates betting opportunities
2. **Paper Betting** - AI autonomously places mock bets with $0 risk to validate the system
3. **Human-in-the-loop** - Once validated, human reviews signals and places real bets manually

**Research-Aligned Approach (8.5/10 Alignment Score):**
- Following best practices from profitable betting research
- Single-sport focus (NFL) until edge is statistically validated
- Paper betting for zero-risk validation before real money
- Kelly Criterion + conservative sizing (1% max stake)
- CLV tracking as primary performance metric

**Current Phase: Phase 1A - Quick Wins & Validation**
- **Now:** NFL-only focus, paper betting accumulation
- **Next:** Line shopping implementation, historical backtesting
- **Future:** Add NBA/NHL after NFL edge validated (6+ months)

**No automated real-money betting** - Paper betting is mock-only for system validation.

---

## Tech Stack

- **Backend:** Python 3.10+ (ETL, modeling, signal generation, paper betting AI)
- **Frontend:** Next.js 14 (dashboard with paper betting UI)
- **Database:** PostgreSQL (Neon) - 15 tables (added paper betting tables)
- **Data Source:** The Odds API (ToS-compliant)
- **Automation:** GitHub Actions (odds ETL, signals, paper betting, settlement)

---

## Quick Reference

### Essential Commands

```bash
# Daily operations (with venv activated)
make etl         # Fetch latest odds (NFL only - single-sport focus)
make signals     # Generate betting signals (14-day window, with vig removal)
make dashboard   # Start dashboard (localhost:3000)
make settle      # Settle completed games and update ELO
make clv         # Capture closing lines (run 10-30 min before games)
make clv-report  # Generate CLV performance report

# Paper betting
.venv/bin/python ops/scripts/paper_bet_agent.py --strategy Conservative --max-bets 10
.venv/bin/python ops/scripts/settle_paper_bets.py

# Progress tracking
make milestone-check  # Check milestone criteria status

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
- `LEAGUES=nfl` (single-sport focus per research recommendations)

**Configuration:**
- `SIGNAL_LOOKAHEAD_HOURS=336` (14 days)
- `EDGE_SIDES=0.02` (2% min edge)
- `KELLY_FRACTION=0.25` (¼-Kelly)
- `BANKROLL=1000.0`

---

## Architecture Principles

### 1. Single-Sport Focus (Research-Aligned)

**Current:** NFL only until edge is statistically validated
**Rationale:** Research shows "focus on just one sport rather than betting on multiple"
**Data Validates This:** 97.8% of signals were already NFL (834 of 853)

**Benefits:**
- Deep expertise in NFL betting markets
- Better model calibration (more data concentration)
- Reduced API quota usage (480 vs 1,440 credits/month for 3 sports)
- Simpler decision-making and analysis

**Sport Addition Criteria (Automated Milestone Detection):**
- ✅ 1,000+ paper bets settled (NFL)
- ✅ ROI > 3% sustained over 3+ months
- ✅ CLV > 1% average
- ✅ p-value < 0.01 (99% confidence)
- ✅ Backtesting confirms edge
- ✅ Line shopping implemented

**Timeline:** Add NBA/NHL after 6-9 months when NFL edge is proven

### 2. API-Only Data Flow

```
The Odds API → ETL → Database → Signal Generation → Dashboard
                                        ↓
                              AI Paper Betting Agent (autonomous)
                                        ↓
                            Paper Bets → Settlement → ELO Updates
                                        ↓
                            Performance Feedback → Model Improvement
                                        ↓
                              Milestone Tracking → Sport Addition Alerts
```

**No CSV fallbacks** - If API fails, log error and exit.

### 3. Database Layer - Idempotent Operations

All writes go through `packages/shared/shared/db.py`:
- `upsert_team()`, `upsert_game()`, `upsert_market()` - Prevent duplicates
- `bulk_insert_odds_snapshots()` - Batch inserts
- `insert_signal()` - Write betting signals
- Safe to re-run scripts without creating duplicates

### 4. Line Shopping (Priority 0 - ✅ IMPLEMENTED)

**Status:** ✅ Implemented (Oct 12, 2025)
**Impact:** +1-2% ROI improvement immediately

**Implementation:**
- `packages/shared/shared/line_shopping.py` - Standalone module with 3 functions
- Integrated into `ops/scripts/generate_signals_v2.py`
- Compares all 9 sportsbooks, selects highest decimal odds (best value for bettor)
- Tracks odds improvement percentage vs average
- Logs line shopping benefits when >0.5% improvement

**How It Works:**
```python
# Groups odds by (market_id, selection)
# Selects best odds (highest decimal = best value)
odds_list_sorted = sorted(odds_list, key=lambda x: float(x['odds_decimal']), reverse=True)
best_odds = odds_list_sorted[0]
odds_improvement_pct = ((best_odds_decimal - avg_odds) / avg_odds) * 100
```

**Research Quote:** "Line shopping for best odds" is a core edge component ✅ COMPLETE

### 5. Signal Generation Flow

```
Odds → ELO Model → Fair Probability → Edge Calculation → Signal (if ≥ threshold)
```

**Per-Selection Fair Probabilities:**
- Moneyline: `p_home` for home, `p_away = 1 - p_home` for away
- Spread: Team-specific cover probability
- Total: `P(Over)` for Over, `P(Under)` for Under

**Key Fix (Oct 8):** Each selection gets its own fair probability (was causing 40%+ edges, now 11%)

### 6. Sport-Specific Risk Management

- **NFL:** Signals expire 48h before game (injury volatility)
- **NBA:** Signals expire 24h before game (lineup changes) - PAUSED until NFL validated
- **NHL:** Signals expire 36h before game (balanced) - PAUSED until NFL validated

### 7. ELO Rating System

- Initial: 1500
- K-factor: 20
- Home advantage: +25 points
- Updates after each settlement
- Tracked in `elo_history` table

### 8. Paper Betting System (AI-Powered Mock Betting)

**Purpose:** Validate system performance with $0 risk before placing real bets

**How It Works:**
1. **AI Agent** evaluates signals every 30 minutes using multi-factor decision logic
2. **Smart Selection** considers edge quality, confidence, bankroll, correlation risk, exposure limits
3. **Kelly Sizing** uses ¼-Kelly with confidence adjustments (max 1% of bankroll per bet)
4. **Transparent Logging** every decision (place/skip) recorded with reasoning
5. **Auto Settlement** paper bets settle when games complete, updating virtual bankroll
6. **Performance Tracking** ROI, win rate, CLV, market performance metrics

**Decision Factors:**
- Edge magnitude (3%+ minimum for conservative strategy)
- Model confidence level (high/medium/low)
- CLV history for sportsbook/market combination
- Time until game (closer = more reliable)
- Market type (moneyline > spread > totals reliability)
- Correlation risk (avoids multiple bets on same game)
- Exposure limits (max 3% of bankroll per game, 30% total)

**Database Tables:**
- `paper_bets` - All AI-placed mock bets with results
- `paper_bankroll` - Running balance, ROI, win rate, avg CLV
- `paper_bet_decisions` - Decision log with AI reasoning (placed + skipped)
- `paper_betting_strategies` - Configurable strategies for A/B testing

**Starting Bankroll:** $10,000 virtual
**Strategy:** Conservative (3% min edge, medium confidence, ¼-Kelly)
**Goal:** Positive ROI + positive CLV = system is beating the market

### 9. Automated Workflows (GitHub Actions)

**Active Automation:**
- **Odds ETL:** 16 runs/day (every 2 hours + 4 strategic times) - NFL only
- **Signal Generation:** Every 20 minutes, 7 days/week (NFL only)
- **Paper Betting:** Every 30 minutes (AI places mock bets + settles completed)
- **Settlement:** Daily at 2 AM ET (settles bets, updates ELO + team ratings)
- **CLV Capture:** Every 30 minutes (closing lines before games start)
- **Performance Analysis:** Sundays 9 AM ET (weekly analysis + auto-tuning recommendations)
- **Milestone Checking:** Daily at 8 AM ET (checks readiness for phase advancement + sport addition)
- **System Monitoring:** Paused until Nov 1, 2025 (resumes hourly after credit reset)

**API Quota Management:**
- Free tier: 500 credits/month (The Odds API)
- NFL-only schedule: 480 credits/month (20 credit buffer, 96% utilization)
- API usage tracked in `api_usage_log` table
- Quota exhaustion alerts loudly (not silent failures)

**Configuration:** Workflows in `.github/workflows/` use GitHub Secrets for credentials

### 10. Dashboard UI

- **Framework:** Next.js 14 with CSS Modules, Recharts for visualization
- **Pages:**
  - `/signals` - Sortable signal table with sport tabs, automation status timers
  - `/performance` - Model performance dashboard with line charts and readiness indicator
  - `/progress` - **NEW** Milestone timeline with phase tracking and sport addition alerts
  - `/paper-betting` - AI paper betting dashboard with P&L tracking, decision log, performance charts
  - `/bets` - Manual bet tracking (placeholder for future real-money bets)
- **Features:**
  - Model Readiness Card: Visual status (Ready/Monitor/Not Ready/Insufficient Data)
  - Milestone Timeline: Phase progress, criteria checklist, sport addition alerts
  - CLV Trend Chart: 30-day performance history
  - Beat Closing % Chart: Track market-beating percentage
  - Performance by Sport/Market: Bar charts showing segment-level CLV
  - Paper Betting Dashboard: Real-time bankroll, win rate, ROI, CLV, AI decision transparency
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
├── odds_etl_v2.py              # **USE THIS** - API-only ETL
├── generate_signals_v2.py      # **USE THIS** - Signal generation
├── settle_results_v2.py        # Bet settlement + ELO updates
├── paper_bet_agent.py          # **NEW** - AI paper betting agent
├── settle_paper_bets.py        # **NEW** - Paper bet settlement
├── auto_analyze_performance.py # Weekly CLV analysis + recommendations
├── auto_tune_parameters.py     # Autonomous parameter tuning
├── capture_closing_lines.py    # CLV capture before games
├── clv_report.py               # CLV reporting
└── verify_setup.py             # System health check
```

### Dashboard (Frontend)

```
apps/dashboard/
├── app/
│   ├── signals/
│   │   ├── page.tsx         # Server component (data fetching)
│   │   └── SignalsClient.tsx # Client component (sortable table, tabs)
│   ├── performance/
│   │   ├── page.tsx         # Performance dashboard server component
│   │   └── PerformanceCharts.tsx # CLV charts and metrics
│   ├── paper-betting/       # **NEW**
│   │   ├── page.tsx         # Paper betting server component
│   │   ├── PaperBettingClient.tsx # Paper betting UI with tabs
│   │   └── PaperBetting.module.css # Paper betting styles
│   ├── globals.css          # Dark theme CSS variables
│   └── bets/page.tsx        # Manual bet tracking (placeholder)
├── components/
│   ├── AutomationStatus.tsx # Live countdown timers for workflows
│   ├── Navigation.tsx       # Navigation bar
│   └── ModelReadinessCard.tsx # Model status indicator
├── actions/
│   ├── signals.ts           # Signal queries (read-only)
│   ├── performance.ts       # Performance/CLV queries
│   └── paper-betting.ts     # **NEW** Paper betting queries
└── lib/
    └── db.ts                # Read-only connection
```

### Infrastructure

```
infra/migrations/
├── 0001_init.sql                    # Full schema (11 base tables)
├── 0004_add_selection_to_odds.sql   # Selection tracking (critical fix)
├── 0005_add_raw_implied_prob.sql    # Vig removal support
├── 0006_add_signal_clv_tracking.sql # CLV tracking
├── 0007_add_performance_indexes.sql # Performance optimization
└── 0008_add_paper_betting.sql       # **NEW** Paper betting tables (4 tables)

.github/workflows/
├── odds_etl.yml                # Automated odds fetching (15 min)
├── generate_signals.yml        # Automated signal generation (20 min)
├── paper_betting.yml           # **NEW** AI paper betting (30 min)
├── settle_results.yml          # Automated settlement (daily 2 AM ET)
├── capture_closing_lines.yml   # CLV capture (30 min)
└── weekly_performance_analysis.yml # Performance analysis (Sundays 9 AM ET)
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

1. **NFL-Only ETL** - Single-sport focus per research recommendations (97.8% of signals were already NFL)
2. **Per-Selection Fair Probabilities** - Each selection gets accurate probability
3. **Vig Removal** - Multiplicative devigging (1.26% avg reduction)
4. **Team-Specific Totals** - Exponential moving average offensive/defensive ratings
5. **Signal Generation** - 800+ active NFL signals with early-season filters
6. **Sport-Specific Expiry** - Risk-aware signal lifetimes (48h for NFL)
7. **CLV Tracking** - Closing line capture + performance analysis
8. **Autonomous Learning** - Self-analyzing, self-tuning model
9. **Performance Dashboard** - Visual readiness indicator + trend charts
10. **ELO System** - Dynamic ratings that update on settlement
11. **Paper Betting System** - AI autonomously places mock bets with $10,000 virtual bankroll
12. **Game Time Display** - Shows game date/time in Eastern Time with day of week
13. **Duplicate Prevention** - Unique index prevents duplicate signals at database level
14. **Milestone Tracking** - Automated phase advancement detection + sport addition alerts

### ⚠️ Recent Fixes

**Oct 12, 2025:**
1. **PostgreSQL NUMERIC Type Handling** - Fixed runtime errors across all dashboard pages
   - Added Number() conversion for all numeric fields in database queries
   - Affects: signals, kpis, performance, bets, paper-betting actions
   - Error: "toFixed is not a function" resolved
2. **CI/CD Build Fixes** - Resolved GitHub Actions failures
   - Created missing `apps/dashboard/lib/db.ts` database utility
   - Fixed .gitignore to allow dashboard lib directory
   - Added `export const dynamic = 'force-dynamic'` to prevent static generation
3. **Signal Generation Automation** - Fixed timezone comparison error
   - Added timezone-awareness check in calculate_expiry_time()
   - Workflow now runs successfully every 20 minutes
4. **Performance Optimizations** - Faster dashboard loads
   - SWC minification, tree-shaking, image optimization
   - Reduced initial page size (50→25 items)
   - Added 7 database indices for common queries
   - Created skeleton loading screen

**Oct 11, 2025:**
1. **Duplicate Signals Fixed** - Removed 137,306 duplicate signals (139k → 1,695 unique)
2. **Paper Betting Correlation Bug Fixed** - AI now diversifies bets across multiple games
3. **Game Time Display** - Added Eastern Time with day of week to all displays

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

1. **NO automated real-money bet placement** - Paper betting is mock-only for validation
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

## Next Steps (Research-Aligned Roadmap)

See `claude/ROADMAP.md` and `claude/RESEARCH_ALIGNMENT.md` for full details.

### **Phase 1A: Quick Wins & Validation** (Weeks 1-4) ← YOU ARE HERE

**✅ Week 1-2: Line Shopping** (COMPLETE - Oct 12, 2025)
- Implemented best-odds selection across 9 sportsbooks
- Expected impact: +1-2% ROI immediately
- See: `packages/shared/shared/line_shopping.py`

**⏳ Week 3-4: Historical Backtesting** (NEXT)
- Validate edge on 2+ years historical data
- Target: 1000+ bets, ROI >3%, p-value <0.01

**Ongoing: Paper Betting Accumulation**
- Target: 1,000+ settled bets by end of Month 6
- Monitor: ROI, CLV, win rate via `/progress` dashboard

### **Phase 1B: Model Refinement** (Months 2-3)
- Weather & injury integration for NFL
- Early-season validation

### **Phase 2: ML Enhancement & Expansion** (Months 4-9)
- ML model development (gradient boosting)
- A/B testing vs ELO baseline
- Props and college football exploration

### **Phase 3: Real Money Deployment** (Months 10-12)
- Only after "Validated Edge" milestone met
- Multi-account strategy
- Manual bet placement

### **When to Add Sports:**
**Automated detection** via milestone tracking system alerts when:
- ✅ NFL edge validated (all 6 criteria met)
- ✅ Appropriate season timing (NBA October, NHL October)
- Dashboard shows: "🎉 Ready to add NBA"

---

## Resources

- **The Odds API Docs:** https://the-odds-api.com/liveapi/guides/v4/
- **PostgreSQL NUMERIC Types:** https://www.postgresql.org/docs/current/datatype-numeric.html
- **Kelly Criterion:** https://www.investopedia.com/articles/trading/04/091504.asp
- **CLV Explained:** https://www.pinnacle.com/en/betting-articles/betting-strategy/what-is-closing-line-value

---

## Support & Troubleshooting

**Full troubleshooting guide:** See `claude/ROADMAP.md` section "Troubleshooting"

**Session summaries:** See `claude/SESSION_*.md` for detailed fix documentation

**Quick diagnostics:**
```bash
make verify      # System health check
make db-ping     # Test database connection
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM signals WHERE status='active'"  # Check signals
```

### Common Issues

**".toFixed is not a function" errors:**
- **Cause:** PostgreSQL NUMERIC/DECIMAL types returned as strings
- **Fix:** Convert with `Number(value)` in database action queries
- **See:** `claude/SESSION_OCT12_2025.md` for detailed fix pattern

**"Module not found: @/lib/db":**
- **Cause:** Missing database utility or .gitignore blocking lib directory
- **Fix:** Ensure `apps/dashboard/lib/db.ts` exists, .gitignore allows it
- **See:** `claude/SESSION_OCT12_2025.md` section 2

**Next.js build trying to connect to database:**
- **Cause:** Static generation attempting to render pages at build time
- **Fix:** Add `export const dynamic = 'force-dynamic'` to page
- **See:** `claude/SESSION_OCT12_2025.md` section 3

**Signal generation timezone errors:**
- **Cause:** Comparing timezone-naive with timezone-aware datetimes
- **Fix:** Check `tzinfo` and convert to UTC before comparison
- **See:** `claude/SESSION_OCT12_2025.md` section 4

---

**Built with:** Python 3.10+, PostgreSQL, Next.js 14, The Odds API
**License:** Private (not for redistribution)
**Maintainer:** Dylan Suhr
