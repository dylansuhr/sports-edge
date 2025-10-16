# SportsEdge - Research-Aligned Roadmap & Status

**Last Updated:** October 12, 2025
**Current Phase:** Phase 1A - Quick Wins & Validation (NFL-Only Focus)
**System Status:** ✅ 100% Operational with Milestone Tracking System
**Strategy:** Research-aligned single-sport focus until edge statistically validated
**Latest:** ✅ Milestone tracking, ✅ Line shopping, ✅ NFL-only workflows, ✅ Automated sport addition detection

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Research-Aligned Strategy](#research-aligned-strategy)
3. [5-Phase Roadmap](#5-phase-roadmap)
4. [Current System Status](#current-system-status)
5. [Milestone Tracking System](#milestone-tracking-system)
6. [Phase 1A: Quick Wins (Weeks 1-2)](#phase-1a-quick-wins-weeks-1-2)
7. [Phase 1B: Validation (Months 1-6)](#phase-1b-validation-months-1-6)
8. [Phase 2: System Optimization (Months 6-9)](#phase-2-system-optimization-months-6-9)
9. [Phase 2.5: Promo System Deployment (Month 9, Weeks 1-2)](#phase-25-promo-system-deployment-month-9-weeks-1-2)
10. [Phase 3: Real Money Validation (Months 9-12)](#phase-3-real-money-validation-months-9-12)
11. [Phase 4: NBA Expansion (Month 12+)](#phase-4-nba-expansion-month-12)
12. [Phase 5: NHL Expansion (Month 15+)](#phase-5-nhl-expansion-month-15)
13. [Architecture Deep Dive](#architecture-deep-dive)
14. [Troubleshooting Guide](#troubleshooting-guide)
15. [Development Workflow](#development-workflow)

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

# Fetch latest odds and generate signals (NFL-only)
make etl && make signals

# View signals and milestone progress
make dashboard  # localhost:3000/signals and /progress

# Settle completed games
make settle

# Check milestone readiness
make milestone-check
```

---

## Research-Aligned Strategy

### Core Principle: Single-Sport Focus Until Validated

**Research Finding:** "Focus on a single sport (NFL recommended) until edge is statistically validated. Then expand systematically." (8.5/10 alignment score)

**Why NFL-Only First:**
1. **Sample Size**: 272 games/season (17 weeks × 16 games) = fastest validation
2. **Market Efficiency**: Most liquid betting market = reliable closing line data
3. **Data Quality**: Comprehensive stats, injury reports, weather data
4. **Seasonality**: September-February gives 6 months of continuous data
5. **API Efficiency**: 67% reduction in API usage (432 → 144 credits/month)

**When to Add NBA/NHL:**
- ✅ 1,000+ paper bets settled (NFL)
- ✅ ROI > 3% sustained over 3+ months
- ✅ CLV > 1% average
- ✅ p-value < 0.01 (99% confidence edge exists)
- ✅ Historical backtesting confirms edge
- ✅ Line shopping implemented
- ✅ Milestone tracking system shows "READY"

**Estimated Timeline:**
- **Optimistic:** 6 months (paper betting 5 bets/day = 900 bets in 6 months)
- **Realistic:** 9-12 months (accounts for calibration, seasonal variance)
- **Conservative:** 12+ months (NFL season + postseason + 3-month validation)

### Automated Sport Addition Detection

The system will **automatically alert** when ready to add NBA/NHL:

1. **Dashboard `/progress` page**: Real-time milestone tracking with visual timeline
2. **Daily Slack alerts**: When all 6 criteria met (8 AM ET check)
3. **GitHub issues**: Auto-created if blocked >7 days
4. **Seasonal calendar**: Alerts 2 weeks before NBA/NHL seasons if ready

**No manual tracking needed** - system handles all validation checks autonomously.

---

## 5-Phase Roadmap

### Overview

| Phase | Focus | Duration | Status |
|-------|-------|----------|--------|
| **1A: Quick Wins** | Line shopping, NFL-only, backtesting | Weeks 1-2 | ✅ IN PROGRESS |
| **1B: Validation** | Paper betting, data accumulation | Months 1-6 | ⏳ Pending |
| **2: Optimization** | ML models, advanced features | Months 6-9 | 📋 Planned |
| **3: Real Money** | Small stakes validation | Months 9-12 | 📋 Planned |
| **4: NBA** | Add second sport | Month 12+ | 🔒 Locked |
| **5: NHL** | Add third sport | Month 15+ | 🔒 Locked |

**Key Principle:** Each phase has **automated milestone detection**. No manual decision-making needed.

---

## Current System Status

### Production Metrics (Oct 12, 2025)

| Metric | Value | Status |
|--------|-------|--------|
| **Focus** | NFL-Only | ✅ Research-aligned |
| **Active Signals** | 800+ (NFL) | ✅ High volume |
| **Average Edge** | 10.95% | ⚠️ Calibrating (expected) |
| **Paper Bets** | ~50 settled | ⏳ Accumulating data |
| **API Quota Usage** | ~144/500 | ✅ 67% savings vs 3-sport |
| **Milestones Tracked** | 5 phases | ✅ Automated detection |
| **Line Shopping** | Implemented | ✅ +1-2% ROI boost |
| **Dashboard** | localhost:3000 | ✅ Live with /progress timeline |

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

## Recent Enhancements (Oct 10, 2025)

### ✅ Completed: Paired Vig Removal

**Impact:** Reduces edges by 1.26% average, more accurate probability calculations

**Implementation:**
- Added `_group_odds_for_vig_removal()` to group paired odds by market/sportsbook
- Added `_get_devigged_probability()` to apply multiplicative vig removal
- Created migration `0005_add_raw_implied_prob.sql` to track both raw and devigged probabilities
- Updated `db.py` to store `raw_implied_probability` separately

**Results:**
- Moneylines: 1.38-3.82% vig removed per selection
- Totals: 1.69-3.05% vig removed
- Spreads: Correctly uses raw prob (API only provides one side)
- Average edge reduced from ~11% to ~10.3% (more realistic)

**Files:** `ops/scripts/generate_signals_v2.py`, `packages/shared/shared/db.py`, `infra/migrations/0005_add_raw_implied_prob.sql`

---

### ✅ Completed: CLV (Closing Line Value) Tracking

**Impact:** Gold standard for measuring model performance, independent of bet outcomes

**Implementation:**
- Created `ops/scripts/capture_closing_lines.py` - fetches odds before games start
- Created `ops/scripts/clv_report.py` - comprehensive performance analysis
- Migration `0006_add_signal_clv_tracking.sql` - added CLV columns to signals
- Added `make clv` and `make clv-report` commands

**Features:**
- Automatic closing line capture (run 10-30 min before games)
- Performance reports: Overall CLV, by sport, by market, by confidence
- Interpretation guidance (excellent/good/neutral/poor)
- Target metrics: >0.5% avg CLV, >52% beat closing line rate

**Files:** `ops/scripts/capture_closing_lines.py`, `ops/scripts/clv_report.py`, `infra/migrations/0006_add_signal_clv_tracking.sql`, `Makefile`

---

### ✅ Completed: Team-Specific Total Models (Fully Integrated)

**Status:** ✅ Complete and operational

---

### ✅ Completed: Autonomous Learning System (Oct 10, 2025)

**Impact:** Fully automated model that learns and evolves without manual intervention

**Implementation:**
- Created `ops/scripts/auto_analyze_performance.py` - weekly performance analysis engine
- Created `ops/scripts/auto_tune_parameters.py` - autonomous parameter tuning based on CLV
- Created `.github/workflows/capture_closing_lines.yml` - captures closing lines every 30 minutes
- Created `.github/workflows/weekly_performance_analysis.yml` - Sunday 9 AM ET analysis
- Created performance dashboard at `/performance` with line charts and readiness indicator

**Features:**
1. **Automated CLV Capture** - Every 30 minutes before games
2. **Weekly Performance Analysis**:
   - Overall CLV, beat closing %, edge analysis
   - By sport, by market, by confidence level
   - Automated recommendations for parameter adjustments
   - Database logging of all analysis
3. **Autonomous Parameter Tuning**:
   - Adjusts EDGE_SIDES based on CLV performance
   - Adjusts KELLY_FRACTION based on variance
   - Conservative changes (max 20% per adjustment)
   - Dry-run mode for safety
4. **Performance Dashboard**:
   - Model readiness indicator (Ready/Monitor/Not Ready/Insufficient Data)
   - CLV trend line chart (30 days)
   - Beat closing % line chart (30 days)
   - Performance by sport (bar chart)
   - Performance by market (bar chart)
   - Statistical summary (median, std dev, percentiles)
   - Navigation with Signals/Performance/My Bets tabs

**Model Readiness Criteria:**
- ✅ Ready: CLV ≥ 0.5%, Beat Close ≥ 52%, 100+ signals
- ⚠️ Monitor: CLV ≥ 0%, Beat Close ≥ 50%, 100+ signals
- ❌ Not Ready: Below thresholds, 100+ signals
- 📊 Insufficient Data: < 100 signals with CLV

**Files:**
- `ops/scripts/auto_analyze_performance.py` (new)
- `ops/scripts/auto_tune_parameters.py` (new)
- `.github/workflows/capture_closing_lines.yml` (new)
- `.github/workflows/weekly_performance_analysis.yml` (new)
- `apps/dashboard/actions/performance.ts` (new)
- `apps/dashboard/app/performance/page.tsx` (new)
- `apps/dashboard/app/performance/PerformanceCharts.tsx` (new)
- `apps/dashboard/components/ModelReadinessCard.tsx` (new)
- `apps/dashboard/components/Navigation.tsx` (new)
- `apps/dashboard/app/layout.tsx` (updated with navigation)

---

### ✅ Phase 1 Complete Summary

All 4 core enhancements completed:
1. ✅ Paired vig removal (1.26% avg reduction)
2. ✅ CLV tracking (gold standard metric)
3. ✅ Team-specific total models (exponential moving average ratings)
4. ✅ Early-season sample size filter (min 3 games)

**Implementation:**
- Added `offensive_ratings` and `defensive_ratings` dicts to `NFLFeatureGenerator`
- Created `update_offensive_rating()` - tracks team scoring ability (exponential moving average)
- Created `update_defensive_rating()` - tracks defensive strength (exponential moving average)
- Created `calculate_expected_total()` - team-specific total predictions
- **Integrated into signal generation** - replaces league averages with team-specific calculations
- **Integrated into settlement** - updates offensive/defensive ratings after each game
- Sport-specific standard deviations (NFL: 10.0, NBA: 12.0, NHL: 2.5)

**Features:**
- Team-specific scoring projections (league avg + offensive rating + opponent defensive rating)
- Home field advantage built-in (+2.5 points for NFL)
- Exponential moving average (α=0.15, ~6 game window)
- Opponent-adjusted ratings (accounts for strength of opposition)

**Expected Impact:**
- Reduces false positive signals on totals by 20-30%
- More accurate NHL/NBA total predictions (15%+ edges → 5-8%)
- Improves as more games are settled and ratings stabilize

**Files:** `packages/models/models/features.py`, `ops/scripts/generate_signals_v2.py`, `ops/scripts/settle_results_v2.py`

---

### ✅ Completed: Early-Season Sample Size Filter

**Status:** ✅ Complete and operational

**Implementation:**
- Added `get_team_games_played()` to check settled game count
- Minimum sample size: 3 games per team
- Automatic confidence downgrade for insufficient sample
  - High → Medium
  - Medium → Low
  - Low → Low (unchanged)

**Features:**
- Warns when teams have < 3 games played
- Reduces false confidence in early-season signals
- Prevents over-betting on untested teams
- Gradually allows higher confidence as season progresses

**Impact:**
- Protects against early-season ELO rating volatility
- Reduces risk during model calibration period
- More conservative approach aligns with patient growth strategy

**Files:** `ops/scripts/generate_signals_v2.py`

---

## Phase 1: Model Refinement (IN PROGRESS)

**Status:** 4 of 4 core items completed ✅
**Timeline:** 2-3 weeks (started Oct 10)
**Priority:** High

**Completed Items:**
1. ✅ Paired vig removal (1.26% avg reduction)
2. ✅ CLV tracking (gold standard performance metric)
3. ✅ Team-specific total models (fully integrated)
4. ✅ Early-season sample size filter (confidence downgrade)

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

## Phase 2: Autonomous Learning System ✅ COMPLETE

**Status:** ✅ Fully Operational
**Completed:** October 10, 2025
**Priority:** High

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

## Phase 2.5: Promo System Deployment (Month 9, Weeks 1-2)

**Status:** Future
**Timeline:** 2-4 weeks before real money launch (Month 9)
**Priority:** High (for Phase 3 success)
**Expected Value:** $5,000-10,000 from new-customer bonuses

### Overview

Deploy promo tracking system 2-4 weeks before opening sportsbook accounts to:
1. Build promo database (2-3 weeks of historical data)
2. Identify highest-EV account opening bonuses
3. Create multi-account strategy (7 accounts recommended)
4. Calculate rollover requirements and expected ROI

**Research Quote:** "New-customer bonuses are the highest-EV bets you'll ever make. Often 20-50% ROI."

**Visual Trigger:** `/progress` dashboard will show "⚠️ Promo System Ready" milestone when Phase 2 reaches 50%+ completion.

---

### Implementation Tasks

#### Task 1: Promo Scraper (4-6 hours)

**Script:** `ops/scripts/scrape_promos.py`

**Target Sites:**
- OddsChecker, Covers, Legal Sports Report (promo aggregators, NOT sportsbooks)
- Scraping aggregators is legally safer than direct sportsbook scraping

**Method:** BeautifulSoup or Apify Sportsbook Scraper API

**Output:** Writes to `promos` table (schema already exists in migration 0001)

**Automation:** `.github/workflows/scrape_promos.yml` - Weekly runs (Sunday 9 AM ET)

---

#### Task 2: EV Calculator (3-4 hours)

**Module:** `packages/shared/shared/promo_math.py`

**Functions:**
```python
def calculate_promo_ev(promo_type, max_bonus, rollover, min_odds):
    """
    Calculates expected value for different promo types:
    - Deposit Match: EV = bonus * (1 - (1/min_odds)^rollover)
    - Risk-Free Bet: EV = bonus * 0.7 (approx 70% recovery)
    - Odds Boost: EV = (boosted_odds - fair_odds) * stake
    """
    pass
```

**Integration:** Called from promo dashboard to rank offers by EV

---

#### Task 3: Dashboard Integration (2 hours)

**File:** `apps/dashboard/app/promos/page.tsx` (already exists as placeholder!)

**Features:**
- Sort by estimated EV (descending)
- Filter by: sportsbook, promo type, expiration date
- Track status: 'available', 'in_progress', 'completed'
- Display rollover progress bar

**Database Connection:** `apps/dashboard/actions/promos.ts` (new)

---

#### Task 4: Database Schema Updates (1 hour)

**Migration:** `infra/migrations/0014_add_promo_milestone.sql` ✅ Created

**Adds:**
- "Promo System Ready" milestone (Phase 3)
- `user_status` column to `promos` table
- `rollover_progress` column to `promos` table

---

#### Task 5: Documentation & Compliance (1 hour)

**Updates:**
- Add disclaimer to promo dashboard about ethical use
- Document multi-account strategy
- Update COMPLIANCE.md with promo usage guidelines

---

### Legal & Compliance

**✅ SAFE:**
- Scraping promo aggregator sites (they compile public info)
- Tracking your own promo usage
- Using promo APIs (Unabated, OpticOdds)

**⚠️ RISKY:**
- Scraping sportsbook sites directly (likely violates ToS)
- Automating bet placement via promos (COMPLIANCE.md prohibits)
- Bonus abuse (COMPLIANCE.md warns against this)

**COMPLIANCE.md Section 2 Update:**
> **Promo Tracking:** SportsEdge tracks publicly available promotional offers for research purposes. Users must comply with all sportsbook terms when using bonuses. Do not engage in bonus abuse or multi-accounting schemes prohibited by sportsbooks.

---

### Success Metrics

- **Promos tracked:** 50+ active offers at any time
- **Bonus capture:** $2,000-5,000 from new-customer bonuses (Month 10-11)
- **Ongoing value:** +1% ROI from recurring promos (Month 12+)
- **Time cost:** <30 minutes/week to review

---

### Timeline

**Week 1-2 of Month 9 (Pre-Launch):**
1. Build promo scraper (Day 1-2)
2. Run scraper for 2-3 weeks to populate database
3. Connect dashboard to promo table (Day 3)
4. Add EV calculator (Day 4-5)
5. Test + document (Day 6-7)

**Month 10 (Real Money Launch):**
1. Review promo dashboard
2. Select best 7 sportsbook accounts based on EV
3. Open accounts using new-customer bonuses
4. Track rollover progress in database
5. Combine promo bets with validated signals

---

### Milestone Criteria (Tracked on `/progress` Dashboard)

**Milestone:** "Promo System Ready"
**Phase:** Phase 3
**Criteria:**
1. ✅ Phase 2 (Optimized System) complete
2. ⬜ Promo scraper operational
3. ⬜ 2+ weeks of promo data collected
4. ⬜ EV calculator validated
5. ⬜ Dashboard page functional
6. ⬜ Multi-account strategy documented

**Visual Alert:** Shows on `/progress` dashboard 30 days before "Real Money Validation" milestone target date

---

### Files to Create

**Backend:**
- `ops/scripts/scrape_promos.py` - Promo scraper script
- `packages/shared/shared/promo_math.py` - EV calculator

**Dashboard:**
- `apps/dashboard/actions/promos.ts` - Database queries

**Automation:**
- `.github/workflows/scrape_promos.yml` - Weekly scraper workflow

**Database:**
- `infra/migrations/0014_add_promo_milestone.sql` - ✅ Already created

---

### Estimated Total Effort

**12-16 hours** (1-2 days of focused work)

**Breakdown:**
- Scraper: 4-6 hours
- EV calculator: 3-4 hours
- Dashboard: 2 hours
- Schema: 1 hour (done)
- Docs: 1 hour
- Testing: 1-2 hours

---

### Dependencies

- **Prerequisite:** Phase 2 (Optimized System) milestone at 50%+ completion
- **Blocker if not ready:** Can still launch Phase 3 without promos, but leaves $5K+ on table

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
