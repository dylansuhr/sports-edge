# SportsEdge - Complete Roadmap & Status

**Last Updated:** October 8, 2025
**Current Phase:** Production Baseline Complete → Phase 1 Enhancements
**System Status:** ✅ 100% Operational with Full Automation (1120 Active Signals)
**Latest:** GitHub Actions automation live, multi-sport workflows (NFL/NBA/NHL), AutomationStatus component with live countdown timers

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Current System Status](#current-system-status)
3. [What We've Built (Baseline)](#what-weve-built-baseline)
4. [Architecture Deep Dive](#architecture-deep-dive)
5. [Phase 1: Model Refinement](#phase-1-model-refinement-next)
6. [Phase 2: Automation & Monitoring](#phase-2-automation--monitoring)
7. [Phase 3: User Experience](#phase-3-user-experience)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Development Workflow](#development-workflow)

---

## Quick Start

### Prerequisites

- Python 3.10+ with venv
- Node.js 18+
- PostgreSQL database (Neon recommended)
- The Odds API key

### Setup (First Time)

```bash
# 1. Copy environment template
cp .env.template .env
# Edit .env with your actual values

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
make install

# 4. Run migrations
make migrate

# 5. Verify setup
make verify

# 6. Test the system
make etl          # Fetch odds
make signals      # Generate signals
make dashboard    # View at localhost:3000
```

### Daily Operations

```bash
# Activate venv (required for each terminal session)
source .venv/bin/activate

# Fetch latest odds and generate signals
make etl && make signals

# View signals
make dashboard  # localhost:3000/signals

# Settle completed games
make settle
```

---

## Current System Status

### Production Metrics (Oct 8, 2025)

| Metric | Value | Status |
|--------|-------|--------|
| **Total Active Signals** | 853 | ✅ Excellent |
| **NFL Signals** | 834 (10.95% avg edge) | ✅ High volume |
| **NBA Signals** | 19 (11.87% avg edge) | ⚠️ Low (season starts Oct 21) |
| **NHL Signals** | 0 | ⚠️ No current games |
| **Games in Pipeline** | 50+ | ✅ Good coverage |
| **Odds Snapshots** | 2,566+ | ✅ Comprehensive |
| **API Quota Usage** | ~462/500 | ✅ Within limits |
| **Dashboard** | localhost:3000 | ✅ Live (redesigned UI) |

### ✅ Fully Operational Features

1. **Multi-Sport ETL Pipeline**
   - Leagues: NFL, NBA, NHL
   - Markets: Moneyline, Spread, Total
   - Rate limiting: 6s between requests
   - Success rate: 100%

2. **Per-Selection Fair Probability Model**
   - Fixed critical bug (was 40%+ edges → now 11%)
   - Each selection gets its own fair probability
   - Uses ELO ratings with home advantage (+25 points)

3. **ELO Rating System**
   - K-factor: 20 (moderate volatility)
   - Home advantage: 25 points
   - Idempotent history tracking
   - Updates automatically on settlement

4. **Signal Generation**
   - Edge range: 2.13% - 19.80% (20% cap)
   - Confidence levels: High (≥5%), Medium (≥3.5%), Low (<3.5%)
   - Stake sizing: ¼-Kelly capped at 1% bankroll

5. **Sport-Specific Expiry Logic**
   - NFL: 48h before game (injury volatility)
   - NBA: 24h before game (lineup changes)
   - NHL: 36h before game (balanced risk)
   - 14-day lookahead window

6. **Dashboard**
   - Live signals view with filters
   - Shows: Game, Market, Side, Book, Odds, Fair Prob, Edge %, Stake %
   - Filters: League, Market Type, Min Edge
   - "Side" column shows exact selection

### ⚠️ Known Issues & Limitations

1. **High edges (11% avg)** - Expected until ELOs diverge after 50+ games settled
2. **NBA signals sparse** - Only 2 games in 14-day window (season starts Oct 21)
3. **NHL totals skipped** - Many exceed 20% edge cap (need team-specific total models)
4. **No vig removal** - Using raw implied probabilities (Phase 1.1 fix)

---

## What We've Built (Baseline)

### Critical Fixes Implemented (Oct 7-8, 2025)

#### 1. Per-Selection Fair Probabilities (Major Fix)
**Problem:** System calculated ONE fair probability per market and applied it to ALL selections
- Example: Giants ML at 53.6% fair AND Eagles ML at 53.6% fair (mathematically impossible)
- Result: 40%+ average edges (unrealistic)

**Solution:**
- Added `selection` column to `odds_snapshots` table (migration 0004)
- Each selection now gets its own fair probability:
  - **Moneyline:** `p_home` for home team, `p_away = 1 - p_home` for away
  - **Spread:** Team-specific cover probability based on implied margin
  - **Total:** `P(Over)` for Over, `P(Under)` for Under

**Result:** Edges normalized to 11% average (will drop to 2-5% as ELOs diverge)

**Files Changed:**
- `infra/migrations/0004_add_selection_to_odds.sql`
- `ops/scripts/odds_etl_v2.py` (stores selection)
- `packages/shared/shared/db.py` (bulk_insert_odds_snapshots)
- `ops/scripts/generate_signals_v2.py` (calculate_fair_probability method)

#### 2. Multi-Sport Support
**Changes:**
- Extended `SIGNAL_LOOKAHEAD_HOURS` to 336 (14 days) to capture all three sports
- Implemented sport-specific expiry logic
- Updated Makefile defaults to `nfl,nba,nhl`

**Result:** Now generating signals across all three sports

#### 3. Dashboard Transparency
**Added:**
- "Side" column showing exact selection (e.g., "Philadelphia Eagles -7.5", "Over 40.5")
- Fixed PostgreSQL NUMERIC → float conversion
- Used scalar subquery to fetch selection data

**Result:** Users can see exactly what each signal recommends betting

#### 4. Safety Rails
- 20% edge cap with logging for outliers
- Skip signals with missing selection data

#### 5. Dashboard UI Redesign (Oct 8, 2025)
**Changes:**
- Redesigned from basic table to professional techy/hackery dark theme
- Terminal-style header with colored dots (red/yellow/green)
- Sport tabs with counts (ALL, NFL, NBA, NHL)
- Sortable table with 11 columns (click headers to sort)
- Color-coded edge percentages (green ≥5%, cyan ≥3%, yellow ≥2%)
- Hover effects with accent border highlighting
- Monospace fonts (JetBrains Mono) for numeric values
- Removed 100-signal LIMIT for full dataset display

**Result:** Clean, data-dense interface optimized for comparing signals at a glance

**Files Changed:**
- `apps/dashboard/app/globals.css` (new dark theme CSS variables)
- `apps/dashboard/app/layout.tsx` (font imports)
- `apps/dashboard/app/signals/SignalsClient.tsx` (table layout with sorting)
- `apps/dashboard/actions/signals.ts` (added league/game_time fields, removed LIMIT)

#### 6. Automation Status Component (Oct 8, 2025)
**Added:**
- Live countdown timers for all three automated workflows
- Real-time updates every second using React hooks
- Terminal-style design matching dashboard aesthetic
- Three job cards: Odds ETL, Signal Generation, Settlement
- Shows frequency, description, and time until next run

**Implementation:**
- Client component with `useState` and `useEffect`
- CSS Modules for scoped, maintainable styling
- Calculates next run time based on interval or daily schedule
- Formats remaining time (seconds, minutes, or hours)

**Result:** Users can see automation status at a glance

**Files Changed:**
- `apps/dashboard/components/AutomationStatus.tsx` (new component)
- `apps/dashboard/components/AutomationStatus.module.css` (new CSS Module)
- `apps/dashboard/app/signals/SignalsClient.tsx` (integrated component)

#### 7. GitHub Actions Automation (Oct 8, 2025)
**Implemented:**
- Three automated workflows running 7 days/week for NBA/NHL coverage
- Secrets configured in GitHub repository settings
- Fixed command-line flags (`--league` → `--leagues`)
- Multi-sport support across all workflows

**Workflows:**
- **Odds ETL** (`odds_etl.yml`): Every 15 minutes, fetches NFL/NBA/NHL odds
- **Signal Generation** (`generate_signals.yml`): Every 20 minutes, generates signals for all sports
- **Settlement** (`settle_results.yml`): Daily at 2 AM ET, settles bets and updates ELO

**Configuration:**
- GitHub Secrets: `DATABASE_URL`, `THE_ODDS_API_KEY`, `SLACK_WEBHOOK_URL`
- All scripts use `--leagues nfl,nba,nhl` flag
- Environment variables passed from workflow to scripts

**Result:** Fully automated data pipeline running 24/7

**Files Changed:**
- `.github/workflows/odds_etl.yml` (schedule changed to `*/15 * * * *`, multi-sport)
- `.github/workflows/generate_signals.yml` (schedule changed to `*/20 * * * *`, multi-sport, fixed flags)
- `.github/workflows/settle_results.yml` (fixed flags, multi-sport)

### Database Schema (11 Tables)

```
teams (84 teams across 3 sports)
  ↓
games (30 NFL, 2 NBA, 18 NHL upcoming)
  ↓
odds_snapshots (2,566 rows with selection data) ← **IMMUTABLE** (never UPDATE)
  ↓
signals (1120 active, auto-expire based on sport)
  ↓
team_elos (dynamic ratings, update on settlement)
  ↓
elo_history (idempotent game-by-game tracking)
```

**Additional tables:**
- `markets` - Market definitions (moneyline, spread, total)
- `players` - Player roster (for future player props)
- `bets` - User-placed wagers (manual entry)
- `results` - Game outcomes
- `clv_history` - Closing Line Value tracking

---

## Architecture Deep Dive

### Data Flow Pipeline

```
1. ETL (odds_etl_v2.py)
   → The Odds API → Parse selection → Normalize → DB (teams, games, markets, odds_snapshots)

2. Feature Generation (features.py)
   → Games + Team ELOs → Calculate home advantage → Generate features

3. Signal Generation (generate_signals_v2.py)
   → Fetch latest odds per (game, market, book)
   → Calculate per-selection fair probability (ELO-based)
   → Calculate edge: fair_prob - implied_prob
   → Filter by threshold (2% sides, 3% props)
   → Calculate sport-specific expiry
   → Write to signals table

4. Dashboard (Next.js)
   → Read-only queries → Display signals with filters

5. Settlement (settle_results_v2.py)
   → Fetch results from API
   → Update games with final scores
   → Settle bets (win/loss/push)
   → Update ELO ratings
   → Write to elo_history
```

### Key Architectural Patterns

#### 1. Provider Layer (`packages/providers/`)

**Purpose:** Isolate all external API calls

**theoddsapi.py:**
- Sport mapping: `nfl → americanfootball_nfl`
- Book mapping: `draftkings, fanduel, williamhill_us (Caesars), betmgm`
- Rate limiting: 6s default between requests
- Quota tracking via response headers
- Returns normalized `NormalizedMarketRow` schema

**results.py:**
- Fetches game scores from The Odds API
- Returns `GameResult` with final scores

#### 2. Database Layer (`packages/shared/shared/db.py`)

**Purpose:** All writes go through idempotent upserts

**Key Methods:**
- `upsert_team()` - ON CONFLICT (external_id) DO UPDATE
- `upsert_game()` - ON CONFLICT (external_id) DO UPDATE
- `upsert_market()` - ON CONFLICT (name) DO UPDATE
- `bulk_insert_odds_snapshots()` - Batch inserts for performance
- `insert_signal()` - Write betting signals
- `update_game_result()` - Set final scores

**Transaction Safety:**
- Context managers for automatic rollback
- Retry logic: 3 attempts with exponential backoff
- Singleton pattern via `get_db()`

#### 3. Odds Math Library (`packages/shared/shared/odds_math.py`)

**Functions:**
- `american_to_decimal()` / `decimal_to_american()` - Odds conversion
- `implied_probability()` - Calculate implied prob from odds
- `remove_vig_multiplicative()` - Remove vig from two-way markets
- `calculate_edge()` - Edge % calculation
- `recommended_stake()` - Fractional Kelly stake sizing
- `calculate_clv()` - Closing Line Value
- `expected_value()` - EV calculation

#### 4. Signal Generation Logic

**Per-Selection Fair Probability Calculation:**

```python
def calculate_fair_probability(self, game, market_name, selection, line_value=None):
    """Calculate fair probability for a SPECIFIC selection."""

    if market_name == 'moneyline':
        # ELO-based win probability for HOME team
        p_home = elo_to_prob(home_elo_adj, away_elo)
        p_away = 1 - p_home

        # Return probability for whichever team is in the selection
        if game['home_team'] in selection:
            return p_home
        elif game['away_team'] in selection:
            return p_away

    elif market_name == 'spread':
        # Determine if selection is for home or away team
        is_home = game['home_team'] in selection

        if is_home:
            # Home team covering: actual_spread > line_value
            cover_margin = implied_spread - line_value
            fair_prob = stats.norm.cdf(cover_margin, loc=0, scale=14)
        else:
            # Away team covering
            cover_margin = -implied_spread - line_value
            fair_prob = stats.norm.cdf(cover_margin, loc=0, scale=14)

        return fair_prob

    elif market_name == 'total':
        if 'Over' in selection:
            return 1 - stats.norm.cdf(line_value, loc=league_avg_total, scale=league_std)
        elif 'Under' in selection:
            return stats.norm.cdf(line_value, loc=league_avg_total, scale=league_std)
```

**Sport-Specific Expiry:**

```python
def calculate_expiry_time(self, game_scheduled_at, sport):
    """Calculate when signal should expire based on sport volatility."""

    if sport == 'nfl':
        hours_before = 48  # Wed/Fri injury reports
    elif sport == 'nba':
        hours_before = 24  # Daily lineup changes
    else:  # nhl and others
        hours_before = 36  # Balanced risk

    return game_scheduled_at - timedelta(hours=hours_before)
```

---

## Phase 1: Model Refinement (NEXT)

**Status:** Ready to start
**Timeline:** 2-3 weeks
**Priority:** High

### 1.1 Vig Removal Enhancement

**Current:** Uses raw implied probabilities from individual odds
**Target:** Paired vig removal (same book, same timestamp)

```python
# For each book/timestamp/game/market:
implied_home, implied_away = remove_vig_multiplicative(prob_home_raw, prob_away_raw)
# Then compare to fair probabilities
```

**Impact:** Will reduce edges by 2-4%, bringing them closer to realistic 3-7% range

**Implementation:**
1. Modify `generate_signals_v2.py` to group odds by (book, timestamp, game, market)
2. For paired markets (moneyline, spread), apply vig removal
3. For totals, apply two-way vig removal (Over vs Under)
4. Update edge calculation to use vig-removed implied probs

**Files:** `ops/scripts/generate_signals_v2.py`

**Estimated Effort:** 4-6 hours

---

### 1.2 Team-Specific Total Models

**Current:** Uses league average (45 points for NFL)
**Target:** Team offensive/defensive ratings

```python
# Calculate expected points per team
expected_total = (team_a_offensive_rating + team_b_defensive_rating) / 2 * 2
# Adjust for pace and venue
```

**Impact:** More accurate total predictions, reduces 10-15% false edges

**Implementation:**
1. Add `offensive_rating` and `defensive_rating` columns to `team_elos` table
2. Calculate rolling averages from historical games (last 10 games)
3. Update `calculate_fair_probability()` for totals to use team-specific ratings
4. Incorporate pace adjustments (possessions per game)

**Files:**
- `infra/migrations/0005_add_team_ratings.sql`
- `packages/models/models/features.py`
- `ops/scripts/generate_signals_v2.py`

**Estimated Effort:** 8-10 hours

---

### 1.3 Weather & Injury Integration

**Current:** Basic weather check in features (not fully integrated)
**Target:** Real-time injury scraping + weather API

```python
# NFL: Wind >15mph, cold <32°F, precipitation
# NBA: N/A (indoors)
# NHL: N/A (indoors)
```

**Impact:** Catches 5-10% of line movements before they happen

**Data Sources:**
- Weather: OpenWeatherMap API (free tier)
- Injuries: ESPN injury report scraping (ToS-compliant)

**Implementation:**
1. Add weather provider to `packages/providers/weather.py`
2. Add injury scraper to `packages/providers/injuries.py`
3. Update `features.py` to incorporate weather/injury scores
4. Add weather/injury columns to signals table for transparency

**Files:**
- `packages/providers/weather.py` (new)
- `packages/providers/injuries.py` (new)
- `packages/models/models/features.py`
- `ops/scripts/generate_signals_v2.py`

**Estimated Effort:** 12-15 hours

---

## Phase 2: Automation & Monitoring

**Status:** Planning
**Timeline:** 1-2 months
**Priority:** Medium

### 2.1 Scheduled Signal Regeneration

**Setup GitHub Actions cron jobs:**

```yaml
# NFL: Sunday 8pm, Wednesday 2pm (before injury reports)
- cron: '0 20 * * 0'  # Sunday 8pm ET
- cron: '0 14 * * 3'  # Wednesday 2pm ET

# NBA: Daily 10am during season (Oct-Apr)
- cron: '0 10 * 10-4 *'  # Daily 10am ET Oct-Apr

# NHL: Mon/Wed/Fri 10am during season (Oct-Apr)
- cron: '0 10 * 10-4 1,3,5'  # MWF 10am ET Oct-Apr
```

**Impact:** Always have fresh signals, auto-expire stale ones

**Implementation:**
1. Create `.github/workflows/` directory
2. Create workflow files for each sport
3. Configure GitHub secrets (DATABASE_URL, THE_ODDS_API_KEY)
4. Test with manual triggers

**Files:** `.github/workflows/generate_signals_{sport}.yml`

**Estimated Effort:** 4-6 hours

---

### 2.2 Slack Alerts for High-Value Signals

**Current:** No alerting
**Target:** Post to Slack when edge ≥ 5%

```python
if edge_pct >= 5.0 and config['slack_webhook']:
    send_slack_alert({
        'game': f"{home} vs {away}",
        'market': market_name,
        'selection': selection,
        'edge': f"{edge_pct:.2f}%",
        'odds': odds_american,
        'book': sportsbook,
        'expires': expiry_time.strftime('%Y-%m-%d %H:%M')
    })
```

**Impact:** Never miss a high-value bet

**Implementation:**
1. Already partially implemented in `generate_signals_v2.py`
2. Uncomment Slack webhook code
3. Test with valid webhook URL
4. Add formatting for better readability

**Files:** `ops/scripts/generate_signals_v2.py`

**Estimated Effort:** 2 hours

---

### 2.3 CLV Tracking System

**Current:** Schema exists but not implemented
**Target:** Track closing line value for all placed bets

```python
# Before game starts:
fetch_closing_odds()
update_bet_clv(bet_id, closing_odds)

# CLV% = (close_prob - entry_prob) × 100
```

**Impact:** Primary metric for long-term profitability validation

**Implementation:**
1. Create `ops/scripts/track_clv.py`
2. Fetch closing odds 5 minutes before game start
3. Calculate CLV for all open bets
4. Update `bets` table with CLV %
5. Insert into `clv_history` table

**Files:** `ops/scripts/track_clv.py` (new)

**Estimated Effort:** 6-8 hours

---

## Phase 3: User Experience

**Status:** Future
**Timeline:** 3-6 months
**Priority:** Low

### 3.1 Manual Bet Entry Page

**Current:** No way to record actual bets
**Target:** Dashboard page to log wagers

**Features:**
- Select from active signals or manual entry
- Track stake, book, timestamp
- Auto-calculate CLV when game completes
- P&L dashboard with filters

**Impact:** Close the loop - see which signals you actually bet and their outcomes

**Files:** `apps/dashboard/app/bets/entry/page.tsx` (new)

**Estimated Effort:** 10-12 hours

---

### 3.2 Signal Expiry Visualization

**Current:** Signals expire silently
**Target:** Show countdown timer in dashboard

```tsx
<td>
  {signal.expires_at > now
    ? `Expires in ${hoursUntil(signal.expires_at)}h`
    : 'EXPIRED'}
</td>
```

**Impact:** Know when to place bets before signals expire

**Files:** `apps/dashboard/app/signals/page.tsx`

**Estimated Effort:** 2-3 hours

---

### 3.3 Historical Performance Analytics

**Current:** No analytics
**Target:** Charts showing:
- Edge % over time (should stabilize as ELOs diverge)
- Win rate by market type
- ROI by sportsbook
- CLV distribution (target: >55% positive CLV)

**Impact:** Data-driven model improvements

**Files:** `apps/dashboard/app/analytics/page.tsx` (new)

**Estimated Effort:** 15-20 hours

---

## Troubleshooting Guide

### ETL Issues

**Problem:** ETL fails with "Invalid API key"
```bash
# Solution:
echo $THE_ODDS_API_KEY  # Verify key is set
# Check .env file has THE_ODDS_API_KEY=xxx
```

**Problem:** ETL succeeds but no data in database
```bash
# Solution:
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM odds_snapshots"
# Verify DATABASE_URL has write permissions
# Check logs for INSERT errors
```

**Problem:** API quota exceeded
```bash
# Solution:
# Free tier = 500 requests/month (~16/day)
# Reduce ETL frequency or upgrade to paid tier
# Check quota: curl -H "apiKey: $THE_ODDS_API_KEY" https://api.the-odds-api.com/v4/sports/
```

---

### Signal Generation Issues

**Problem:** No signals generated
```bash
# Checklist:
# 1. Check odds_snapshots has recent data
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM odds_snapshots WHERE fetched_at > NOW() - INTERVAL '24 hours'"

# 2. Check games in window
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM games WHERE scheduled_at BETWEEN NOW() AND NOW() + INTERVAL '14 days'"

# 3. Lower threshold for testing
EDGE_SIDES=0.01 make signals

# 4. Check model logs
grep "No model available" /tmp/signals_run.log
```

**Problem:** Edges still too high (>20%)
```bash
# This is expected when:
# - ELO ratings are at default 1500 (no differentiation)
# - No vig removal implemented yet
# - Team-specific models not implemented

# Solutions:
# 1. Wait for games to settle (ELOs will diverge)
# 2. Implement Phase 1.1 (vig removal)
# 3. Implement Phase 1.2 (team-specific total models)
```

---

### Dashboard Issues

**Problem:** Dashboard shows "No signals"
```bash
# Solution:
# 1. Verify DATABASE_READONLY_URL is set in apps/dashboard/.env.local
cat apps/dashboard/.env.local

# 2. Query signals table directly
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM signals WHERE status='active' AND expires_at > NOW()"

# 3. Check read-only role has SELECT permissions
psql "$DATABASE_READONLY_URL" -c "SELECT 1 FROM signals LIMIT 1"
```

**Problem:** Dashboard errors on PostgreSQL NUMERIC types
```bash
# Solution: Already fixed in apps/dashboard/lib/db.ts:9
# Converts NUMERIC to float automatically
# If error persists, check TypeScript types match database schema
```

---

### Database Issues

**Problem:** Connection refused
```bash
# Solution:
make db-ping  # Diagnostic tool

# Check:
# 1. DATABASE_URL format: postgresql://user:pass@host:port/dbname
# 2. Firewall rules allow connections
# 3. SSL mode correct (sslmode=require for Neon)
# 4. DNS resolves: nslookup <host>
```

**Problem:** Migration fails
```bash
# Solution:
# Check which migrations have run:
psql "$DATABASE_URL" -c "SELECT * FROM migrations" 2>/dev/null || echo "Migrations table doesn't exist"

# Re-run specific migration:
psql "$DATABASE_URL" -f infra/migrations/0004_add_selection_to_odds.sql
```

---

## Development Workflow

### Before Starting Work

1. **Activate virtual environment:**
```bash
source .venv/bin/activate
```

2. **Pull latest changes:**
```bash
git pull origin main
```

3. **Verify system health:**
```bash
make verify
```

---

### Making Changes

#### 1. Modifying Models

**ELO parameters:**
```python
# Edit: packages/models/models/features.py
K_FACTOR = 20         # Increase for more volatile ratings
HOME_ADVANTAGE = 25   # Increase for stronger home advantage
```

**Fair probability logic:**
```python
# Edit: ops/scripts/generate_signals_v2.py
# Method: calculate_fair_probability()
```

**Edge thresholds:**
```bash
# Edit: .env
EDGE_SIDES=0.02   # Minimum edge for sides/totals
EDGE_PROPS=0.03   # Minimum edge for props
```

#### 2. Adding New Markets

1. Add market to `theoddsapi.py` sport mapping
2. Update `calculate_fair_probability()` to handle new market
3. Test with single sport: `python ops/scripts/generate_signals_v2.py --leagues nfl`

#### 3. Database Schema Changes

1. Create new migration: `infra/migrations/000X_description.sql`
2. Test migration on local DB: `psql "$DATABASE_URL" -f infra/migrations/000X_description.sql`
3. Update `db.py` if adding new upsert functions
4. Update TypeScript types in `apps/dashboard/actions/` if affecting dashboard

---

### Testing Changes

**End-to-End Test:**
```bash
# 1. Run ETL
make etl

# 2. Generate signals
make signals

# 3. Check signal counts
psql "$DATABASE_URL" -c "SELECT sport, COUNT(*) FROM signals s JOIN games g ON s.game_id = g.id WHERE status='active' GROUP BY sport"

# 4. View in dashboard
make dashboard
open http://localhost:3000/signals
```

**Unit Tests (when implemented):**
```bash
pytest packages/shared/tests/test_odds_math.py -v
pytest packages/models/tests/ -v
```

---

### Committing Changes

**DO NOT commit:**
- `.env` or `.env.local` files
- API keys or credentials
- `node_modules/` or `.venv/`
- Log files or temporary data

**Commit message format:**
```
[Component] Brief description

- Detailed change 1
- Detailed change 2

Fixes: #issue-number (if applicable)
```

**Example:**
```
[SignalGen] Implement per-selection fair probabilities

- Added selection column to odds_snapshots table
- Updated calculate_fair_probability() to accept selection parameter
- Fixed edge inflation bug (40% → 11%)

Fixes: #23
```

---

## Configuration Reference

### Environment Variables (.env)

```bash
# === Database ===
DATABASE_URL='postgresql://...'              # Read-write (ETL, signals)
DATABASE_READONLY_URL='postgresql://...'     # Read-only (dashboard)

# === API ===
USE_API=true
THE_ODDS_API_KEY='...'                       # Get from the-odds-api.com

# === Signal Generation ===
SIGNAL_LOOKAHEAD_HOURS=336                   # 14 days (captures all sports)
EDGE_SIDES=0.02                              # 2% min edge for sides/totals
EDGE_PROPS=0.03                              # 3% min edge for props
KELLY_FRACTION=0.25                          # ¼-Kelly (conservative)
MAX_STAKE_PCT=0.01                           # 1% max per bet
BANKROLL=1000.0                              # Current bankroll

# === Leagues ===
LEAGUES=nfl,nba,nhl                          # Comma-separated

# === Optional ===
SLACK_WEBHOOK_URL='...'                      # For high-edge alerts
```

### Makefile Commands

```bash
make migrate       # Run database migrations
make etl           # Fetch odds for nfl,nba,nhl
make signals       # Generate signals (14-day window)
make settle        # Settle completed games, update ELO
make dashboard     # Start Next.js dev server
make install       # Install Python + Node dependencies
make verify        # Run system health check
make db-ping       # Test database connection
make clean         # Remove build artifacts
```

---

## Success Metrics

### Current State (Oct 8, 2025)

| Metric | Current | Target | Timeline |
|--------|---------|--------|----------|
| **Average Edge** | 11.28% | 3-5% | After 50+ games settled |
| **CLV (Positive)** | N/A | >55% | After 200+ bets tracked |
| **Win Rate** | N/A | 52-54% | After 100+ bets |
| **ROI** | N/A | 5-8% | After 1 season |
| **API Quota Usage** | 462/500 | <200/500 | Ongoing |

### Key Performance Indicators

**System Health:**
- ETL success rate: Target >95%
- Signal generation count per day: Target >100
- Dashboard uptime: Target 99%+

**Model Performance:**
- Closing Line Value (CLV): Target >0% average over 200 bets
- Return on Investment (ROI): Target >5% long-term
- Brier score: Target <0.20 (calibration metric)

---

## Resources

### Documentation
- [The Odds API Docs](https://the-odds-api.com/liveapi/guides/v4/)
- [PostgreSQL NUMERIC Types](https://www.postgresql.org/docs/current/datatype-numeric.html)
- [Kelly Criterion Explained](https://www.investopedia.com/articles/trading/04/091504.asp)
- [Closing Line Value (CLV)](https://www.pinnacle.com/en/betting-articles/betting-strategy/what-is-closing-line-value)

### Internal Docs
- `CLAUDE.md` - High-level project overview
- `COMPLIANCE.md` - Legal and ToS compliance
- `README.md` - Quick start guide

---

## Monitoring Checklist

- [ ] Check API quota daily (should be <50 requests/day)
- [ ] Review signal counts (should have 100+ active across all sports)
- [ ] Verify dashboard loads (localhost:3000/signals)
- [ ] Check database connection (make db-ping)
- [ ] Review error logs for ETL failures
- [ ] Monitor ELO rating divergence (check `team_elos` table)

---

**Document Version:** 1.0 (Consolidated)
**Last Updated:** October 8, 2025
**Maintainer:** Dylan Suhr

**Built with:** Python 3.10+, PostgreSQL, Next.js 14, The Odds API
**License:** Private (not for redistribution)
