# API Quota Status Report

**Last Updated:** November 13, 2025 (20:55 UTC)
**Status:** 🚨 QUOTA EXHAUSTED - Waiting for December 1st reset

---

## Current Situation

### Quota Status
- **Used:** 500/500 (100%)
- **Remaining:** 0
- **Provider:** The Odds API (Free Tier)
- **Monthly Limit:** 500 requests

### Timeline
- **Current Billing Period Started:** November 1, 2025 (01:56 UTC)
- **Quota Exhausted:** ~November 11-12, 2025
- **Next Reset:** **December 1, 2025 (01:56 UTC)** ⏰
- **Days Until Reset:** ~18 days

### Impact
- ✅ **Signal Generation:** Still working (using existing odds from Nov 10)
- ✅ **Paper Betting:** Still working (AI placing mock bets with existing signals)
- ✅ **Settlement:** Still working (settling bets and updating ELO)
- ❌ **Odds ETL:** Skipping runs (no fresh odds data)
- ⚠️ **Odds Age:** 70+ hours old (last fetch: Nov 10, 22:23 UTC)

---

## System Behavior During Quota Exhaustion

### What's Working Correctly ✅
1. **Odds ETL Auto-Skipping:** Workflow runs every 2 hours but checks quota first and skips ETL when exhausted
2. **Quota Monitoring:** Logs warnings twice daily (8 AM, 8 PM UTC)
3. **Signal Generation:** Creates signals from existing odds data (every 20 minutes)
4. **Paper Betting Agent:** Places mock bets autonomously (every 30 minutes)
5. **Settlement & ELO:** Updates ratings when games complete (daily 2 AM ET)

### What Was Fixed Today 🔧
1. **System Monitoring Threshold:** Changed odds staleness check from 1h → 3h (matches ETL schedule)
2. **Quota Monitoring Permissions:** Removed GitHub issue creation (was failing with 403 error)
   - Now just logs warnings to workflow output

---

## Why Quota Exhausted Faster Than Expected

### Expected vs Actual Usage

**Designed Schedule (from CLAUDE.md):**
- NFL-only ETL: 16 runs/day
- 3 markets (h2h, spreads, totals) × 1 league = 3 credits/run
- Expected: 16 runs × 3 credits = 48 credits/day
- Monthly: 48 × 30 = **1,440 credits/month** ❌ WAY OVER!

**Wait, that's wrong!** Let me recalculate based on actual usage...

**Actual Issue:**
The schedule says "16 runs/day = 480 credits/month" but that assumes 1 credit per run.
Reality: Each run fetches 3 markets = **3 credits per ETL run**.

**Corrected Math:**
- 16 runs/day × 3 credits/run = **48 credits/day**
- 48 credits/day × 30 days = **1,440 credits/month**
- Free tier: 500 credits/month
- **Shortfall: -940 credits/month** 🚨

### Root Cause
**Quota calculation in CLAUDE.md was incorrect!** The documentation said "480 credits/month" but didn't account for 3 API calls per ETL run (one for each market).

---

## Solutions

### Option 1: Reduce ETL Frequency (Stay on Free Tier)
To stay within 500 credits/month:
- **Max runs per month:** 500 ÷ 3 = 166 runs
- **Max runs per day:** 166 ÷ 30 = ~5.5 runs/day
- **Recommended schedule:** 6 runs/day (every 4 hours)
  - Times: 00:00, 04:00, 08:00, 12:00, 16:00, 20:00 UTC
  - Monthly usage: 6 × 3 × 30 = **540 credits** (still 8% over)

**Actually feasible:** 5 runs/day (every 4-5 hours)
- Times: 00:00, 06:00, 11:00, 16:00, 21:00 UTC
- Monthly usage: 5 × 3 × 30 = **450 credits** ✅ (90% utilization, 50 credit buffer)

### Option 2: Upgrade to Paid Tier
- **Starter Plan:** $50/month = 10,000 credits
  - Supports: 10,000 ÷ 3 ÷ 30 = **111 runs/day** (current schedule uses 16)
  - Plenty of headroom for expansion to NBA/NHL

### Option 3: Optimize API Usage
- Fetch only 1 market per run (rotate: h2h, spreads, totals)
- Run schedule: 16 runs/day × 1 credit = **480 credits/month** ✅
- Caveat: Each signal type only updates every 3 runs

---

## Recommended Action Plan

### Immediate (Until December 1)
1. ✅ Fixed monitoring workflows (completed today)
2. ⏳ Wait for quota reset on December 1
3. Monitor signal generation with stale odds (acceptable for paper betting validation)

### After December 1 Reset
1. **Update ETL Schedule** to 5 runs/day (every 4-5 hours)
   - Edit `.github/workflows/odds_etl.yml`
   - New cron: `'0 0,6,11,16,21 * * *'`
   - Monthly usage: 450 credits (90% utilization)

2. **Update CLAUDE.md Documentation**
   - Fix quota calculation error
   - Document correct credit usage (3 credits per ETL run)
   - Update "Active Automation" section with new schedule

3. **Add Quota Alerts**
   - Alert at 400 credits used (80%) ⏰ 8 days before exhaustion
   - Alert at 450 credits used (90%) ⏰ 3 days before exhaustion
   - Alert at 475 credits used (95%) ⏰ 1 day before exhaustion

### Long-Term (Month 3-4)
- Evaluate paid tier upgrade when adding NBA/NHL
- Current plan: Single-sport focus until NFL edge validated
- Paid tier makes sense for multi-sport expansion

---

## Monitoring Commands

```bash
# Check quota status
source .env && psql "$DATABASE_URL" -c "
SELECT * FROM api_usage_current_month WHERE provider = 'theoddsapi';
"

# Check days until reset
source .env && psql "$DATABASE_URL" -c "
SELECT
    EXTRACT(DAY FROM (DATE '2025-12-01' - CURRENT_DATE)) as days_until_reset,
    EXTRACT(EPOCH FROM (TIMESTAMP '2025-12-01 01:56:00 UTC' - NOW())) / 3600 as hours_until_reset;
"

# Check odds age
source .env && psql "$DATABASE_URL" -c "
SELECT
    MAX(fetched_at) as last_odds_fetch,
    EXTRACT(EPOCH FROM (NOW() - MAX(fetched_at))) / 3600 as hours_old
FROM odds_snapshots;
"
```

---

## Files Modified Today

1. `.github/workflows/monitoring.yml` - Fixed odds staleness threshold (1h → 3h)
2. `.github/workflows/quota_monitoring.yml` - Removed GitHub issue creation (permissions error)
3. `claude/API_QUOTA_STATUS.md` - This document

---

## References

- The Odds API Pricing: https://the-odds-api.com/liveapi/guides/v4/#pricing
- Quota tracking view: `api_usage_current_month`
- Quota check script: `ops/scripts/check_api_quota.py`
