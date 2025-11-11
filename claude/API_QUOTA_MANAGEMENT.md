# API Quota Management Guide

**Last Updated:** November 11, 2025

## Overview

SportsEdge uses The Odds API free tier (500 requests/month). This document explains how quota is managed to ensure continuous operation without exhaustion.

---

## Current Schedule (480 credits/month)

### Odds ETL Workflow
```yaml
- cron: '0 */2 * * *'        # Every 2 hours (12 runs/day)
- cron: '0 1,7,13,19 * * *'  # Strategic times (4 runs/day)
```

### Breakdown by Hour (UTC)
| Hour | Source | Count |
|------|--------|-------|
| 0    | Every 2h | 1 |
| 1    | Strategic | 1 |
| 2    | Every 2h | 1 |
| 4    | Every 2h | 1 |
| 6    | Every 2h | 1 |
| 7    | Strategic | 1 |
| 8    | Every 2h | 1 |
| 10   | Every 2h | 1 |
| 12   | Every 2h | 1 |
| 13   | Strategic | 1 |
| 14   | Every 2h | 1 |
| 16   | Every 2h | 1 |
| 18   | Every 2h | 1 |
| 19   | Strategic | 1 |
| 20   | Every 2h | 1 |
| 22   | Every 2h | 1 |

**Total:** 16 unique hours/day (no overlaps)

### Monthly Usage
```
16 runs/day × 30 days = 480 credits/month
Quota limit: 500 credits/month
Buffer: 20 credits (4%)
Utilization: 96%
```

---

## Why the Schedule is Optimal

### 1. **96% Utilization**
- Uses 480/500 credits (maximizes free tier value)
- 20-credit buffer for unexpected retries/testing
- Safety margin prevents accidental exhaustion

### 2. **Strategic Timing**
- **1 AM UTC (8 PM ET):** Evening lines update
- **7 AM UTC (2 AM ET):** Overnight adjustments
- **13 PM UTC (8 AM ET):** Morning lines
- **19 PM UTC (2 PM ET):** Afternoon market moves

### 3. **Continuous Coverage**
- Maximum gap between runs: 2 hours
- Lines are captured frequently enough to detect value
- Not so frequent that it wastes quota

---

## Quota Reset Schedule

### Important: Quota Does NOT Reset on 1st of Month!

**Quota resets 30 days after your first API call.**

- **First API call:** October 13, 2025
- **Expected reset:** November 12-13, 2025
- **Next reset:** December 12-13, 2025

### How to Verify Reset Date
1. Check your The Odds API dashboard
2. Look at `api_usage_log` table for first request timestamp
3. Add 30 days to that date

---

## Quota Monitoring System

### Automated Monitoring (quota_monitoring.yml)
- **Frequency:** Twice daily (8 AM, 8 PM UTC)
- **Check Script:** `ops/scripts/check_api_quota.py`
- **Logging:** All checks logged to `api_usage_log` table

### Alert Thresholds
| Usage | Action | Severity |
|-------|--------|----------|
| < 80% | No alert | ✅ Healthy |
| 80-89% | Log notice | 📊 Normal |
| 90-94% | Log caution | ⚠️ Watch |
| 95-99% | Create GitHub issue | 🚨 Warning |
| 100% | Create critical issue | 🔴 Critical |

### Alert Actions
When quota reaches 95%+:
1. GitHub issue created automatically
2. Issue includes:
   - Current usage percentage
   - Estimated days until exhaustion
   - Recommended actions
   - Links to upgrade options

---

## Why Quota Was Exhausted (Nov 11)

### Root Cause Analysis

**Expected usage:** 480 credits/month
**Actual usage:** 533 credits/month
**Overage:** 53 credits (10.6%)

### Breakdown
```
Oct 13: 56 credits  (initial setup/testing - EXTRA)
Oct 14: 35 credits  (more testing - EXTRA)
Oct 15-31: 272 credits (17 days × 16/day = NORMAL)
Nov 1-10: 160 credits (10 days × 16/day = NORMAL)
Nov 11: 12 credits (exhausted mid-day)

Total: 533 credits
Testing overhead: 91 credits (17% of usage)
```

### Why It Won't Happen Again
1. ✅ No more initial setup/testing
2. ✅ Quota monitoring alerts before exhaustion
3. ✅ Pre-ETL quota checks
4. ✅ Workflows paused during exhaustion

---

## What Happens When Quota Exhausted

### Automatic Safeguards
1. **ETL workflow:** Fails gracefully, logs error
2. **Signal generation:** Continues with stale odds
3. **Paper betting:** Continues with existing signals
4. **Settlement:** Fails (can't fetch game results)
5. **Monitoring:** Detects and alerts

### Manual Recovery Steps
1. Wait for quota reset (30 days after first call)
2. Workflows auto-resume when quota available
3. Settlement catches up with 45-day lookback
4. System returns to normal operation

---

## Optimizing API Usage

### Current Optimization Strategies

#### 1. **NFL-Only Focus**
- Single sport = 1 credit per run
- Multi-sport would use 3+ credits per run
- Savings: 67% reduction vs 3 sports

#### 2. **Strategic Timing**
- 16 runs/day vs continuous polling
- Captures key market movement times
- Avoids wasteful overnight/off-hours calls

#### 3. **Line Shopping**
- Fetch all 9 sportsbooks in single call
- 1 credit gets all books simultaneously
- No additional cost for more books

### Future Optimization Options (If Needed)

#### Option A: Reduce to 15 runs/day (450 credits/month)
```yaml
- cron: '0 0,2,4,6,8,10,12,14,16,18,20,22 * * *'  # 12 runs
- cron: '0 1,13,19 * * *'                         # 3 strategic times
= 15 unique runs/day = 450 credits/month
Buffer: 50 credits (10%)
```

#### Option B: Game-day only polling
- Poll 16x/day on game days only
- 2x/day on non-game days
- Saves ~30% quota on off-weeks
- More complex to implement

#### Option C: Reduce to critical windows
- Focus on 12 hours before games only
- 3-4 runs per game
- Saves significant quota
- Risk: miss early line value

---

## Upgrade Options (Paid Tiers)

If free tier becomes insufficient:

| Plan | Price | Requests | $/Request | Best For |
|------|-------|----------|-----------|----------|
| **Free** | $0 | 500/mo | $0 | Testing, single sport |
| **Starter** | $50 | 10,000/mo | $0.005 | 1-2 sports, hourly updates |
| **Pro** | $100 | 25,000/mo | $0.004 | Multi-sport, real-time |
| **Premium** | $200+ | 50,000+ | $0.004 | Professional, high-frequency |

### When to Upgrade
Consider upgrading when:
- ✅ NFL edge validated (1000+ paper bets, positive ROI)
- ✅ Ready to add NBA/NHL
- ✅ Need more frequent updates (every 30 min)
- ✅ Moving to real money betting

**Current Recommendation:** Stay on free tier until NFL edge validated (6-9 months)

---

## Monitoring Current Usage

### Check Quota Status
```bash
# Manual check
python ops/scripts/check_api_quota.py

# Database query
psql $DATABASE_URL -c "
  SELECT
    DATE(request_timestamp) as date,
    COUNT(*) as requests,
    SUM(credits_used) as credits
  FROM api_usage_log
  WHERE request_timestamp >= NOW() - INTERVAL '30 days'
  GROUP BY DATE(request_timestamp)
  ORDER BY date DESC;
"
```

### Expected Output (Steady State)
```
Date         Requests   Credits
2025-11-13   16         16
2025-11-14   16         16
2025-11-15   16         16
...
Total: 480 credits/month
```

### Warning Signs
- 🚨 > 17 requests/day sustained
- 🚨 Quota above 90% before day 27
- 🚨 Failed requests due to quota
- 🚨 Manual testing adding extra calls

---

## Best Practices

### DO ✅
- Monitor quota twice daily via automation
- Keep 4%+ buffer for safety
- Log all API calls to database
- Test changes manually (not in production)
- Wait for quota reset if exhausted

### DON'T ❌
- Run manual ETL tests in production (use local env)
- Assume quota resets on 1st of month
- Ignore quota warnings (act at 90%)
- Add more sports without calculating impact
- Increase polling frequency without checking math

---

## Troubleshooting

### "Quota exhausted mid-month"
**Cause:** Extra manual testing or schedule misconfiguration
**Fix:** Check `api_usage_log` for anomalies, wait for reset

### "Schedule using more than 16 runs/day"
**Cause:** Cron overlaps or multiple workflows hitting API
**Fix:** Verify unique hours, check for duplicate schedules

### "Buffer too small (< 10 credits)"
**Cause:** Schedule too aggressive or month has 31 days
**Fix:** Reduce runs/day or add day-of-month filtering

### "Quota monitoring not alerting"
**Cause:** Workflow not running or secrets not configured
**Fix:** Check workflow logs, verify DATABASE_URL and THE_ODDS_API_KEY

---

## Summary

✅ **Schedule optimized:** 16 runs/day = 480 credits/month (96% utilization)
✅ **Monitoring active:** Twice daily checks with alerts
✅ **Safe operation:** 20-credit buffer prevents exhaustion
✅ **Future-proof:** Can add sports after NFL edge validated

**Bottom line:** System is configured for continuous operation without quota exhaustion. The Oct 13-14 testing overhead was a one-time issue that won't recur.

---

**Next Review:** After quota resets (Nov 12-13, 2025)
**Contact:** Check The Odds API dashboard for exact reset timing
