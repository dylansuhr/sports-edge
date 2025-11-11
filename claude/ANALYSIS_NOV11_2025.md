# SportsEdge System Analysis - November 11, 2025

## Executive Summary

**Status: CRITICAL ISSUES IDENTIFIED** 🚨

After 11 days of operation (Nov 1-11), the system has multiple critical issues that need immediate attention:

1. **API Quota Management:** System consumed 533 credits in 30 days, but quota reset timing misunderstood
2. **Paper Betting Performance:** **-56.76% ROI** on 9 bets (1W-6L) - AI is losing badly
3. **AI Betting Rate:** Only **1.21%** of signals result in bets (9 out of 742) - AI is barely betting
4. **Settlement Issues:** 26 October bets still pending settlement
5. **ELO System:** Working (54 updates, 31 teams) but 25 games awaiting settlement

---

## Part 1: API Quota Consumption Analysis

### Current State
- **Total Credits Used:** 533 credits
- **Time Period:** Oct 13 - Nov 11 (30 days)
- **Daily Average:** 15.6 credits/day
- **Quota Status:** 0/500 remaining (exhausted)

### The Issue
**You assumed the quota reset on Nov 1st, but it actually resets based on when you first started using the API (around Oct 13).**

### Credits by Day
```
Oct 13:  56 credits (initial setup/testing)
Oct 14:  35 credits
Oct 15-31: 16 credits/day (consistent)
Nov 1-10: 16 credits/day (consistent)
Nov 11:  12 credits (partial day, exhausted)
```

### Why 16 Credits Per Day?
Your ETL workflow runs:
- Every 2 hours (12 runs/day)
- Plus 4 strategic times (1am, 7am, 1pm, 7pm)
- **Total: 16 runs/day × 1 credit/call = 16 credits/day**

### Expected vs Actual
- **Your Plan:** 480 credits/month (16 runs/day)
- **Reality:** 533 credits used in 30 days
- **Extra Usage:** 53 credits over estimate (9.9% overage)
- **Cause:** Initial testing (56 credits on Oct 13) + 35 on Oct 14

### The Real Problem
**The quota doesn't reset monthly on the 1st - it resets 30 days after your first API call.**

Your first call was Oct 13, so quota should have reset around Nov 12-13, not Nov 1st.

---

## Part 2: Paper Betting Performance Analysis

### Overall Performance (Nov 1-11)

**TERRIBLE RESULTS:**
- **Total Bets:** 9
- **Record:** 1W - 6L - 0P (2 pending)
- **Win Rate:** 14.29% (expected ~52%)
- **Total Staked:** $88.48
- **Net P/L:** **-$50.22**
- **ROI:** **-56.76%**
- **Average Stake:** $9.83
- **Average Edge:** 16.87%

### By Market Type
| Market    | Bets | W-L  | Avg Edge | Net P/L   |
|-----------|------|------|----------|-----------|
| Spread    | 6    | 0-4  | 18.30%   | -$39.78   |
| Total     | 2    | 1-1  | 17.57%   | -$0.74    |
| Moneyline | 1    | 0-1  | 6.89%    | -$9.70    |

### Daily Betting Activity
| Date    | Bets | P/L      |
|---------|------|----------|
| Nov 1   | 4    | -$20.74  |
| Nov 3   | 2    | -$19.69  |
| Nov 7   | 1    | -$9.79   |
| Nov 10  | 2    | $0.00 (pending) |

### All Settled Bets Details
```
11-07  Carolina Panthers -5.5   (2.00 odds, $9.79, 19.9% edge) → LOST -$9.79
11-03  New York Giants ML       (2.42 odds, $9.70, 6.9% edge)  → LOST -$9.70
11-03  Colts -6.5               (1.98 odds, $9.99, 19.9% edge) → LOST -$9.99
11-01  Over 43.5                (1.93 odds, $10.00, 16.0% edge) → WON +$9.26 ✅
11-01  Patriots -6.5            (1.95 odds, $10.00, 17.9% edge) → LOST -$10.00
11-01  Cowboys -3.5             (1.98 odds, $10.00, 12.1% edge) → LOST -$10.00
11-01  Over 42.5                (1.93 odds, $10.00, 19.1% edge) → LOST -$10.00
```

### Critical Observations

1. **High edges aren't translating to wins:** Average 16.87% edge but only 14.29% win rate
2. **Spread bets performing worst:** 0-4 record on spreads with 18.3% average edge
3. **Model calibration issue:** If edges are real, we should be winning ~60-70% of bets
4. **Sample size:** Only 7 settled bets - too small to draw strong conclusions, but trend is alarming

---

## Part 3: AI Betting Behavior Analysis

### Signal Conversion Rate

**CRITICAL ISSUE: AI IS BARELY BETTING**

- **Total Signals Generated (Nov 1-11):** 742
- **Signals AI Bet On:** 9
- **Conversion Rate:** **1.21%**
- **Expected Rate:** 5-10%
- **Problem Severity:** 🚨 **CRITICAL**

### Why Is This Happening?

#### Strategy Settings (Conservative)
```
min_edge: 3.0%
min_confidence: medium
max_stake_pct: 1.0%
kelly_fraction: 0.25
max_exposure_per_game: 3.0%
```

#### Signal Distribution
- **Total Active Signals:** 742
- **Edge >= 3%:** 699 (94.2%) ✅
- **Edge >= 5%:** 593 (79.9%) ✅
- **Edge >= 10%:** 308 (41.5%)
- **Average Edge:** 9.75%

**So 699 signals meet the minimum edge threshold, but AI only bet on 9 (1.29% of qualified signals).**

### Possible Causes

1. **Selection Field Missing:** The query tries to get `selection` but it might be NULL for many signals
2. **Correlation Filter Too Aggressive:** AI avoids multiple bets on same game
3. **Game Timing Filter:** Only bets on games within 7 days
4. **CLV Bonus Unavailable:** No CLV history yet, so confidence scores are lower
5. **Max Bets Per Run:** Agent limited to 10 bets per run (30 min intervals)
6. **Already Bet Filter:** Excludes signals already in pending bets

### Most Likely Issue
Looking at the code (line 151): `AND g.scheduled_at BETWEEN NOW() AND NOW() + INTERVAL '7 days'`

**This is filtering out most signals!** NFL games are typically once per week, so many signals may be for games > 7 days away.

---

## Part 4: Settlement & ELO System

### Settlement Status

**Good News: Settlement is working, but incomplete**

- **Total Games (Nov 1-11):** 52 games scheduled
- **Settled:** 27 games (51.9%)
- **Awaiting Settlement:** 25 games (48.1%)

### ELO System Performance

**✅ ELO System is Working**

- **Total Updates:** 54 ELO ratings updated
- **Teams Updated:** 31 teams
- **Average ELO:** 1501.9 (close to initial 1500)
- **First Update:** Nov 3, 2025
- **Last Update:** Nov 10, 2025

### Outstanding Issues

**26 October bets still pending settlement** - These are from Oct 12-14 and should have been settled by now. This suggests:
1. Settlement script not running frequently enough
2. Games not being marked with scores
3. Bug in settlement logic

---

## Part 5: ETL Pipeline Analysis

### Status: ✅ Working Until Quota Exhausted

- **Runs per Day:** 16 (as designed)
- **Success Rate:** 93% (160/172 successful, 12 failed when quota exhausted)
- **Consistency:** Perfect 16 credits/day Oct 15 - Nov 10
- **Failure Mode:** Graceful (logs quota exhaustion, doesn't crash)

### Issues Identified

1. **No Quota Monitoring:** System doesn't track approaching quota limits
2. **No Degradation Strategy:** When quota low, could reduce frequency rather than exhaust completely
3. **Off-by-one Month:** Assumed Nov 1 reset, but quota resets ~30 days after first use

---

## Part 6: Code Issues Identified

### Critical Issues

#### 1. **Signal Selection Query - 7 Day Filter Too Restrictive**
**Location:** `ops/scripts/paper_bet_agent.py:151`

```python
AND g.scheduled_at BETWEEN NOW() AND NOW() + INTERVAL '7 days'
```

**Problem:** NFL games are weekly, so this excludes many valid signals for games 8-14 days out.

**Impact:** **This is likely the PRIMARY cause of 1.21% betting rate.**

**Fix:** Change to `INTERVAL '14 days'` to match signal generation window.

---

#### 2. **Selection Field Often NULL**
**Location:** `ops/scripts/paper_bet_agent.py:122-135`

```python
COALESCE(
    s.selection,
    (
        SELECT o2.selection
        FROM odds_snapshots o2
        WHERE o2.game_id = s.game_id
          AND o2.market_id = s.market_id
          AND o2.sportsbook = s.sportsbook
          AND o2.odds_american = s.odds_american
        ORDER BY o2.fetched_at DESC
        LIMIT 1
    )
) as selection
```

**Problem:** If `signals.selection` is NULL and the subquery doesn't find a match, `selection` will be NULL and bet will fail.

**Impact:** Bets may be rejected due to missing selection data.

**Fix:** Ensure `selection` is always populated in `signals` table during signal generation.

---

#### 3. **October Bets Not Settling**
**26 pending bets from October 12-14** that should have been settled.

**Possible Causes:**
1. Settlement workflow not running daily
2. Games not being updated with scores
3. Settlement script filtering out old bets

**Fix:** Check `settle_paper_bets.py` and `settle_results_v2.py` workflows.

---

#### 4. **Model Calibration - Edges Too High**
**Average edge of 9.75%** is unrealistic and suggests model miscalibration.

**Evidence:**
- AI betting on 16.87% average edge bets
- Only winning 14.29% (expected 60-70% if edges are real)
- Losing -56.76% ROI

**Likely Causes:**
1. **ELO ratings not converged yet:** Only 54 updates across 31 teams (< 2 updates/team)
2. **Team ratings not accurate:** Need 50+ games per team for ELO to stabilize
3. **Vig removal too aggressive:** May be overestimating true probability
4. **Line shopping inflating edges:** Comparing best available line vs fair value

**Fix:**
- Continue accumulating data (need 100+ settled bets)
- Review ELO parameters (K-factor, home advantage)
- Add early-season damping factor
- Compare actual win rates vs predicted edges

---

#### 5. **No Automated Quota Monitoring**
System exhausted 500 credits without warning.

**Fix:** Add quota monitoring with alerts at 80%, 90%, 95% thresholds.

---

### Medium Priority Issues

#### 6. **No Bankroll Tracking**
`paper_bankroll` table not being updated (schema mismatch in queries).

**Impact:** Can't track cumulative P/L, ROI, or bankroll growth over time.

---

#### 7. **CLV Tracking Not Implemented**
`signals.clv_percent` field exists but not being populated.

**Impact:** AI can't use CLV history to improve bet selection.

---

#### 8. **Signal Expiry Too Aggressive**
NFL signals expire 48 hours before game, but games are weekly.

**Problem:** Signals generated on Monday for next Sunday game expire Wednesday, wasting 4 days of potential betting.

**Fix:** Extend NFL expiry to 24 hours (or even 12 hours) before game.

---

## Part 7: Recommended Fixes (Prioritized)

### IMMEDIATE (Fix Today)

1. **Fix 7-day filter → 14-day filter**
   - File: `ops/scripts/paper_bet_agent.py:151`
   - Change: `INTERVAL '7 days'` → `INTERVAL '14 days'`
   - Impact: Should increase betting rate from 1.21% to 5-10%

2. **Ensure `selection` field always populated**
   - File: `ops/scripts/generate_signals_v2.py`
   - Add: Populate `selection` field when inserting signals
   - Impact: Prevent bet placement failures

3. **Fix October bet settlement**
   - Check `settle_paper_bets.py` workflow schedule
   - Manually run settlement for Oct 12-14 games
   - Verify games have scores in database

4. **Wait for API quota reset**
   - Verify reset date from The Odds API (likely Nov 12-13)
   - Resume workflows when quota resets

---

### HIGH PRIORITY (This Week)

5. **Add Quota Monitoring**
   - Track API credits remaining
   - Alert at 80%, 90%, 95% thresholds
   - Implement degradation strategy (reduce frequency when low)

6. **Extend Signal Expiry Window**
   - NFL: 48h → 12h before game
   - Impact: Allow betting closer to game time when lines are sharper

7. **Fix `paper_bankroll` Updates**
   - Correct schema mismatches in bankroll queries
   - Ensure cumulative P/L tracking works

8. **Investigate Model Calibration**
   - Compare predicted win rates vs actual
   - Review ELO parameters
   - Add early-season damping factor

---

### MEDIUM PRIORITY (Next 2 Weeks)

9. **Implement CLV Tracking**
   - Capture closing lines 10-30 min before games
   - Calculate CLV for each signal
   - Use CLV in AI decision-making

10. **Add Bet Decision Logging**
    - Log why AI skipped each signal (reasoning)
    - Create `paper_bet_decisions` table if not exists
    - Improve AI transparency

11. **Optimize API Usage**
    - Reduce polling frequency during off-peak times
    - Only poll frequently 24h before games
    - Could extend free tier to 45-60 days

12. **Add Performance Monitoring Alerts**
    - Alert if ROI < 0% after 50+ bets
    - Alert if win rate < 45% after 50+ bets
    - Alert if betting rate < 3%

---

## Part 8: Expected Performance After Fixes

### Betting Rate
- **Current:** 1.21% (9/742 signals)
- **After 7→14 day fix:** 5-10% (37-74 bets)
- **After expiry fix:** 8-12% (59-89 bets)

### Settlement
- **Current:** 7 settled, 26 pending (from October)
- **After fix:** All October bets settled, current bets settle daily

### ROI/Win Rate
- **Current:** -56.76% ROI, 14.29% win rate (7 bets)
- **Need:** 100+ settled bets to evaluate accurately
- **Expected (if model calibrated):** 3-5% ROI, 52-54% win rate
- **If still negative after 100 bets:** Model needs major revision

---

## Part 9: Data Quality Assessment

### What's Working ✅
1. **ETL Pipeline:** Consistent, reliable, graceful failure
2. **Signal Generation:** 742 signals in 11 days (67/day average)
3. **ELO Updates:** 54 updates, system learning from outcomes
4. **Workflow Automation:** All scheduled jobs running on time
5. **Database integrity:** No corruption, queries working

### What's Broken 🚨
1. **AI Betting Logic:** 1.21% conversion rate (need 5-10%)
2. **Model Calibration:** -56.76% ROI suggests edges are wrong
3. **Settlement Backlog:** 26 October bets still pending
4. **Quota Management:** No monitoring, exhausted without warning
5. **Bankroll Tracking:** Schema mismatches preventing updates

---

## Part 10: Next Steps

### Today (Nov 11)
- [ ] Fix 7-day → 14-day filter in `paper_bet_agent.py`
- [ ] Ensure `selection` field populated in `generate_signals_v2.py`
- [ ] Manually settle October bets
- [ ] Wait for API quota reset (check with The Odds API)

### This Week
- [ ] Add API quota monitoring and alerts
- [ ] Extend signal expiry to 12h before games
- [ ] Fix `paper_bankroll` update queries
- [ ] Review model calibration (compare predicted vs actual win rates)

### Next 2 Weeks
- [ ] Implement CLV tracking
- [ ] Add bet decision logging table
- [ ] Optimize API usage for longer free tier
- [ ] Set up performance monitoring alerts

### After 100+ Settled Bets (Month 2-3)
- [ ] Full model performance review
- [ ] If ROI still negative: major model revision
- [ ] If ROI positive: continue accumulating data
- [ ] Consider upgrade to paid API tier if needed

---

## Conclusion

**The system has good infrastructure but critical issues in the AI betting logic and model calibration.**

**Primary Problem:** The 7-day game filter is preventing the AI from betting on most signals. This is easily fixable.

**Secondary Problem:** The model edges appear inflated (9.75% average is unrealistic). This needs more data to confirm, but early results (-56.76% ROI) are concerning.

**Good News:**
- ETL pipeline is solid
- ELO system is learning
- Workflows are automated and reliable
- Database integrity is good

**Action Required:**
1. Fix the 7-day filter immediately
2. Wait for API quota reset
3. Accumulate 100+ bets to properly evaluate model
4. Don't bet real money until ROI is consistently positive over 1000+ paper bets

**Timeline to Real Money:**
- **Optimistic:** 6-9 months (if fixes work and model shows edge)
- **Realistic:** 12+ months (if model needs major revision)
- **Current Status:** Not ready - losing -56.76% on paper bets

---

Generated: November 11, 2025
Next Review: After quota resets and 50+ more bets placed
