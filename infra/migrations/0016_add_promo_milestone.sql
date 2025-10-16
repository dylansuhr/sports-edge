-- Migration: Add Promo System Milestone
-- Purpose: Track promo tracking system deployment for Phase 3 (Real Money Validation)
-- Date: 2025-10-15

-- Add "Promo System Ready" milestone
-- This will trigger visual alerts on /progress dashboard 2-4 weeks before Phase 3
INSERT INTO milestones (name, phase, description, criteria, target_date, status) VALUES
(
    'Promo System Ready',
    'Phase 3',
    'Promo tracking system deployed for account opening strategy',
    '{
        "phase_2_complete": {
            "target": true,
            "description": "Phase 2 (Optimized System) milestone complete"
        },
        "promo_scraper_built": {
            "target": true,
            "description": "Promo scraper script operational (ops/scripts/scrape_promos.py)"
        },
        "promo_database_populated": {
            "target": true,
            "description": "2+ weeks of promo data collected in promos table"
        },
        "ev_calculator_tested": {
            "target": true,
            "description": "Promo EV calculator validated (packages/shared/shared/promo_math.py)"
        },
        "dashboard_connected": {
            "target": true,
            "description": "Promo dashboard page functional (/promos)"
        },
        "multi_account_strategy": {
            "target": true,
            "description": "Multi-account strategy documented (7 accounts recommended)"
        }
    }'::jsonb,
    -- Target date: 30 days before Real Money Validation milestone
    (SELECT target_date FROM milestones WHERE name = 'Real Money Validation' LIMIT 1) - INTERVAL '30 days',
    'pending'
)
ON CONFLICT DO NOTHING;

-- Add additional columns to promos table for tracking usage
ALTER TABLE promos
ADD COLUMN IF NOT EXISTS user_status VARCHAR(20) DEFAULT 'available'
CHECK (user_status IN ('available', 'in_progress', 'completed', 'expired'));

ALTER TABLE promos
ADD COLUMN IF NOT EXISTS rollover_progress DECIMAL(5, 2) DEFAULT 0.00
CHECK (rollover_progress >= 0 AND rollover_progress <= 100);

-- Create index for filtering available promos
CREATE INDEX IF NOT EXISTS idx_promos_user_status ON promos(user_status, end_date);

-- Comments
COMMENT ON COLUMN promos.user_status IS 'Tracks user usage of promo: available (not used), in_progress (clearing rollover), completed (rollover cleared), expired (past end_date)';
COMMENT ON COLUMN promos.rollover_progress IS 'Percentage of rollover requirement completed (0-100)';

-- Migration complete
-- Visual trigger will appear on /progress dashboard when Phase 2 reaches 50%+ completion
