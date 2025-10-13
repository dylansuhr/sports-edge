# Streamlined Architecture - October 2025

**Goal:** Clean, maintainable codebase with no feature duplication

---

## Architecture Principles

1. **Single Source of Truth** - Each feature lives in exactly one place
2. **Dashboard-First** - Real-time visibility trumps batch reports
3. **Automation Where Needed** - Only automate what can't be done interactively
4. **Phase-Appropriate** - Keep only what's needed for current phase

---

## Core System Components

### 1. Data Pipeline (Automated)
- **odds_etl.yml** - Fetch NFL odds every 15 min (144 credits/month)
- **generate_signals.yml** - Generate betting signals every 20 min
- **capture_closing_lines.yml** - Capture closing lines every 30 min (CLV tracking)
- **settle_results.yml** - Settle bets & update ELO ratings daily at 2 AM ET

### 2. Paper Betting (Automated)
- **paper_betting.yml** - AI agent places mock bets every 30 min
- Autonomous validation with $0 risk
- Target: 1,000 settled bets before real money

### 3. Dashboard (Real-Time Visibility)
- **/** - Home with SystemModeIndicator (Waiting/Action/Ready/Review)
- **/signals** - Active betting signals with automation status
- **/progress** - Timeline with milestones, action guidance, week-by-week roadmap
- **/analytics** - Performance insights (sportsbook, market, correlations)
- **/paper-betting** - Paper bet tracking with P&L, decision log
- **/performance** - Model performance, CLV trends, readiness indicator

### 4. Quality & Monitoring
- **tests.yml** - CI/CD checks on every push (linting, build verification)
- **monitoring.yml** - Hourly health checks (detects stale data, silent failures)

---

## What Was Removed (and Why)

### ❌ milestone_check.yml (Redundant Workflow)
**Reason:** Dashboard `/progress` page provides superior real-time visibility
- WaitingPeriodCard shows data accumulation progress
- ActionTimelineCalendar shows week-by-week roadmap
- NextActionAlert tells you exactly when action is needed
- No need for separate GitHub Actions + issue creation

**Script Retained:** `check_milestone_readiness.py` still available for manual debugging

### ❌ weekly_performance_analysis.yml (Redundant Workflow)
**Reason:** Dashboard `/analytics` page provides real-time insights
- Performance by sportsbook, market, confidence
- Correlation analysis (edge vs CLV, timing vs CLV)
- Betting patterns (best/worst combos, optimal timing)
- Auto-tuning not needed until Phase 2 (ML Enhancement)

**Scripts Retained:** 
- `auto_analyze_performance.py` - Can run manually if needed
- `auto_tune_parameters.py` - Will be useful in Phase 2

---

## Information Flow

```
The Odds API
    ↓ (every 15 min)
Odds ETL → Database
    ↓ (every 20 min)
Signal Generation → Signals Table
    ↓ (every 30 min - before game)
Closing Line Capture → CLV Tracking
    ↓ (every 30 min)
Paper Betting AI → Paper Bets Table
    ↓ (daily 2 AM)
Settlement → Game Results + ELO Updates
    ↓ (real-time)
Dashboard → User Visibility
```

---

## Dashboard Pages Map

### Primary Navigation
1. **Home (/)** 
   - SystemModeIndicator: Current state (Waiting/Action/Ready/Review)
   - KPI cards: Open signals, avg edge, 7-day CLV, lifetime ROI
   - AutomationStatus: Workflow countdown timers
   - Quick links to all pages

2. **Signals (/signals)**
   - Sortable table of active signals
   - Sport tabs (NFL-only currently)
   - Automation status with live countdowns
   - Kelly sizing, edge %, confidence, expiry

3. **Progress (/progress)**
   - NextActionAlert: "What to do when" with countdown
   - WaitingPeriodCard: Day counter, metrics progress
   - ActionTimelineCalendar: Week-by-week roadmap
   - ProgressTimeline: Detailed milestone criteria

4. **Analytics (/analytics)**
   - Key insights: Best/worst combos, optimal timing
   - Performance charts: By sportsbook, market, confidence
   - Parameter tuning history: 30-day trends
   - Correlation analysis: Edge vs CLV, timing vs CLV
   - CLV by hour of day

5. **Paper Betting (/paper-betting)**
   - Bankroll dashboard: Balance, ROI, win rate, CLV
   - Decision log: All AI decisions (placed + skipped)
   - Performance charts: P&L over time
   - Market breakdown

6. **Performance (/performance)**
   - Model readiness indicator
   - CLV trend charts
   - Beat closing % over time
   - Performance by sport/market

### Secondary Pages
7. **Bets (/bets)** - Manual bet tracking (placeholder for real money phase)
8. **Promos (/promos)** - Placeholder
9. **Reports (/reports)** - Placeholder

---

## Current Phase: 1A - Quick Wins & Validation

**Status:** Waiting for 1,000 paper bets to accumulate

**Active Features:**
- ✅ NFL-only odds ETL (single-sport focus)
- ✅ Signal generation with line shopping
- ✅ Paper betting AI (autonomous mock betting)
- ✅ CLV tracking
- ✅ Timeline dashboard with action guidance

**Not Needed Yet:**
- ❌ Multi-sport support (wait until NFL validated)
- ❌ ML model enhancements (Phase 2)
- ❌ Auto-tuning (Phase 2)
- ❌ Real money betting (Phase 3)

**Next Milestone:** Historical backtesting when 1,000 bets reached

---

## File Organization

### Python Packages
```
packages/
├── providers/          # API integrations (The Odds API)
├── shared/shared/      # Database, odds math, utilities
└── models/models/      # ELO system, feature generation
```

### Operations Scripts
```
ops/scripts/
├── odds_etl_v2.py                    # Core: Odds fetching
├── generate_signals_v2.py            # Core: Signal generation
├── settle_results_v2.py              # Core: Settlement
├── paper_bet_agent.py                # Core: AI paper betting
├── settle_paper_bets.py              # Core: Paper bet settlement
├── capture_closing_lines.py          # Core: CLV capture
├── clv_report.py                     # Utility: Manual CLV reports
├── check_milestone_readiness.py      # Utility: Manual milestone checks
├── auto_analyze_performance.py       # Reserved: Phase 2
├── auto_tune_parameters.py           # Reserved: Phase 2
└── verify_setup.py                   # Utility: System health check
```

### Dashboard
```
apps/dashboard/
├── app/                           # Next.js 14 pages
│   ├── page.tsx                   # Home
│   ├── signals/                   # Signals page
│   ├── progress/                  # Timeline & milestones
│   ├── analytics/                 # Advanced analytics
│   ├── paper-betting/             # Paper betting dashboard
│   └── performance/               # Model performance
├── actions/                       # Server actions (database queries)
│   ├── signals.ts
│   ├── milestones.ts
│   ├── analytics.ts
│   ├── performance.ts
│   └── paper-betting.ts
└── components/                    # React components
    ├── WaitingPeriodCard.tsx
    ├── ActionTimelineCalendar.tsx
    ├── NextActionAlert.tsx
    ├── SystemModeIndicator.tsx
    └── ...
```

---

## Maintenance Guidelines

### Adding New Features
1. **Check for duplication first** - Does this already exist?
2. **Choose the right layer** - Dashboard (real-time) vs Script (batch) vs Workflow (scheduled)
3. **Single responsibility** - One feature, one location
4. **Phase-appropriate** - Is this needed now or later?

### Removing Features
1. **Check all references** - Workflows, scripts, dashboard
2. **Document why** - Add to this file
3. **Keep scripts** - Even if workflow removed (useful for debugging)

### Code Review Checklist
- [ ] No duplicate functionality
- [ ] Dashboard-first for user-facing features
- [ ] Automated only when necessary
- [ ] Phase-appropriate (don't build for Phase 3 in Phase 1)
- [ ] Single source of truth
- [ ] Clear separation of concerns

---

## Success Metrics

**Before streamlining:**
- 9 GitHub Actions workflows
- Some duplicate functionality (milestone checking in both workflow + dashboard)
- Weekly reports duplicating real-time analytics

**After streamlining:**
- 7 GitHub Actions workflows (22% reduction)
- Zero feature duplication
- Dashboard provides superior UX vs batch reports
- Clearer system architecture

**Result:** Easier to maintain, easier to understand, no confusion about "where do I check this?"

---

**Last Updated:** October 13, 2025
**Version:** 2.0
**Status:** Production Ready ✅
