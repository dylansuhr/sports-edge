# Closing Line Value (CLV) Tracking

## Overview

Closing Line Value is the **gold standard** metric for evaluating sports betting models. A positive CLV means you consistently get better odds than the closing line, which is the sharpest price in the market.

## Why CLV Matters

- **Closing line is the sharpest**: It incorporates all information right before the game
- **Strong predictor of profitability**: Models with positive CLV are profitable long-term
- **Independent of results**: Short-term luck doesn't affect CLV measurement
- **Industry standard**: Used by professional betting operations

## Database Schema

Migration `0010_add_clv_tracking.sql` adds:

```sql
-- Columns added to signals table
closing_odds_american INT          -- Final odds before game (American format)
closing_odds_decimal NUMERIC(10,4) -- Final odds before game (Decimal format)
closing_line_value NUMERIC(10,4)   -- CLV = (closing_decimal / opening_decimal) - 1
closing_captured_at TIMESTAMP      -- When closing odds were captured

-- View for CLV analysis
signal_clv_summary -- Aggregates CLV by sport and market category
```

## CLV Calculation

```
CLV = (Closing Odds Decimal / Opening Odds Decimal) - 1

Examples:
- Opening: +150 (2.50), Closing: +120 (2.20) → CLV = -12% (bad, line moved against us)
- Opening: -110 (1.909), Closing: -130 (1.769) → CLV = -7.3% (bad)
- Opening: -110 (1.909), Closing: -105 (1.952) → CLV = +2.3% (good!)
- Opening: +200 (3.00), Closing: +250 (3.50) → CLV = +16.7% (excellent!)
```

## Implementation Plan

### Phase 1: Infrastructure (✅ Complete)
- [x] Add CLV columns to signals table
- [x] Create CLV summary view
- [x] Add indices for CLV queries

### Phase 2: Data Collection (To Do)
1. **Create closing line capture script** (`ops/scripts/capture_closing_lines.py`)
   - Runs 5-10 minutes before games start
   - Fetches current odds from The Odds API
   - Calculates CLV vs opening odds
   - Updates signals table

2. **Add to GitHub Actions**
   - Schedule every 10 minutes during game days
   - Focus on games starting in next 30 minutes

### Phase 3: Analysis & Reporting (To Do)
1. **Dashboard CLV widget**
   - Average CLV by sport/market
   - CLV distribution histogram
   - Signals with CLV > 5% (high-quality picks)

2. **CLV-based signal filtering**
   - Track which signal characteristics correlate with positive CLV
   - Adjust edge thresholds based on historical CLV
   - Filter out signal sources with consistently negative CLV

## Target Metrics

**Excellent Performance:**
- Average CLV > +2%
- 60%+ of signals beat closing line
- Consistent across sports/markets

**Good Performance:**
- Average CLV > +1%
- 55%+ of signals beat closing line

**Needs Improvement:**
- Average CLV < 0%
- <50% beat closing line

## Integration with Paper Betting

CLV tracking enhances paper betting evaluation:

1. **Separate luck from skill**: A bet can lose but still have positive CLV
2. **Better model validation**: Positive CLV confirms edge exists
3. **Identify model weaknesses**: Which markets have negative CLV?
4. **Adjust strategies**: Bet more when CLV is historically high

## API Usage Considerations

- **Quota impact**: Each CLV capture requires 1-3 API calls per game
- **Timing**: Capture 5-10 min before game (sweet spot)
- **Sports-specific**: NFL games start at fixed times (easier to schedule)
- **Rate limiting**: Respect 6-second minimum between requests

## Next Steps

1. Run migration: `psql $DATABASE_URL < infra/migrations/0010_add_clv_tracking.sql`
2. Create capture script (template provided)
3. Test manually before adding to automation
4. Add GitHub Actions workflow for scheduled captures
5. Build dashboard visualization

## Reference Reading

- [Pinnacle: What is CLV?](https://www.pinnacle.com/en/betting-articles/betting-strategy/what-is-closing-line-value)
- [Captain Obvious: CLV is King](https://www.unabated.com/articles/closing-line-value-clv-is-king/)
