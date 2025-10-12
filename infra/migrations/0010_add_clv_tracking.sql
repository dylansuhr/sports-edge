-- Migration: Add Closing Line Value (CLV) tracking
-- This allows us to measure if our signals beat the closing line

-- Add CLV columns to signals table
ALTER TABLE signals
ADD COLUMN IF NOT EXISTS closing_odds_american INT,
ADD COLUMN IF NOT EXISTS closing_odds_decimal NUMERIC(10, 4),
ADD COLUMN IF NOT EXISTS closing_line_value NUMERIC(10, 4),
ADD COLUMN IF NOT EXISTS closing_captured_at TIMESTAMP WITH TIME ZONE;

COMMENT ON COLUMN signals.closing_odds_american IS 'Final odds before game starts (American format)';
COMMENT ON COLUMN signals.closing_odds_decimal IS 'Final odds before game starts (Decimal format)';
COMMENT ON COLUMN signals.closing_line_value IS 'CLV = (closing_decimal / opening_decimal) - 1 (positive = beat closing line)';
COMMENT ON COLUMN signals.closing_captured_at IS 'When closing odds were captured (typically 5-10 min before game)';

-- Create index for CLV queries
CREATE INDEX IF NOT EXISTS idx_signals_clv ON signals(closing_line_value) WHERE closing_line_value IS NOT NULL;

-- Create CLV summary view
CREATE OR REPLACE VIEW signal_clv_summary AS
SELECT
    g.sport,
    m.category as market_category,
    COUNT(*) as total_signals,
    COUNT(CASE WHEN closing_line_value > 0 THEN 1 END) as beat_closing,
    ROUND(AVG(closing_line_value) * 100, 2) as avg_clv_percent,
    ROUND(STDDEV(closing_line_value) * 100, 2) as clv_stddev_percent,
    COUNT(CASE WHEN closing_line_value > 0.02 THEN 1 END) as clv_gt_2pct,
    COUNT(CASE WHEN closing_line_value > 0.05 THEN 1 END) as clv_gt_5pct
FROM signals s
JOIN games g ON s.game_id = g.id
JOIN markets m ON s.market_id = m.id
WHERE s.closing_line_value IS NOT NULL
GROUP BY g.sport, m.category
ORDER BY avg_clv_percent DESC;

COMMENT ON VIEW signal_clv_summary IS 'Summary statistics of CLV performance by sport and market';
