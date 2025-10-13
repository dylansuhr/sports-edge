-- Migration: Add Milestone Tracking
-- Purpose: Track phase milestones and automate sport addition detection
-- Date: 2025-10-12

-- Table to store milestone definitions and criteria
CREATE TABLE IF NOT EXISTS milestones (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phase VARCHAR(50) NOT NULL,
    description TEXT,
    criteria JSONB NOT NULL,
    target_date DATE,
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'blocked')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table to store milestone check history
CREATE TABLE IF NOT EXISTS milestone_checks (
    id SERIAL PRIMARY KEY,
    milestone_id INT REFERENCES milestones(id),
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    criteria_met JSONB NOT NULL,  -- Which criteria are met
    all_criteria_met BOOLEAN NOT NULL,
    notes TEXT,
    FOREIGN KEY (milestone_id) REFERENCES milestones(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX idx_milestones_status ON milestones(status, target_date);
CREATE INDEX idx_milestone_checks_timestamp ON milestone_checks(checked_at DESC);
CREATE INDEX idx_milestone_checks_milestone ON milestone_checks(milestone_id, checked_at DESC);

-- Comments
COMMENT ON TABLE milestones IS 'Tracks project milestones and phase advancement criteria';
COMMENT ON TABLE milestone_checks IS 'Historical record of milestone criteria checks';

-- Seed initial milestones
INSERT INTO milestones (name, phase, description, criteria, target_date, status) VALUES
(
    'Validated Edge (NFL)',
    'Phase 1',
    'Prove statistical edge in NFL betting with 99% confidence',
    '{
        "paper_bets_settled": {"target": 1000, "description": "Paper bets settled"},
        "roi_pct": {"target": 3.0, "description": "ROI percentage"},
        "clv_pct": {"target": 1.0, "description": "Average CLV percentage"},
        "p_value_max": {"target": 0.01, "description": "Statistical significance (p-value)"},
        "line_shopping_implemented": {"target": true, "description": "Line shopping feature implemented"},
        "backtesting_completed": {"target": true, "description": "Historical backtesting completed (1000+ bets)"}
    }'::jsonb,
    CURRENT_DATE + INTERVAL '90 days',
    'in_progress'
),
(
    'Optimized System',
    'Phase 2',
    'ML model beats ELO baseline, niche markets added',
    '{
        "paper_bets_settled": {"target": 3000, "description": "Total paper bets settled"},
        "ml_model_trained": {"target": true, "description": "ML model trained and validated"},
        "ml_beats_elo": {"target": true, "description": "ML ROI > ELO ROI + 1%"},
        "props_added": {"target": true, "description": "Player props market added"},
        "ncaaf_added": {"target": false, "description": "College football added (optional)"},
        "combined_roi_pct": {"target": 4.0, "description": "Combined ROI across all markets"}
    }'::jsonb,
    CURRENT_DATE + INTERVAL '270 days',
    'pending'
),
(
    'Real Money Validation',
    'Phase 3',
    'Successful real money deployment with positive ROI',
    '{
        "prerequisites_met": {"target": true, "description": "All Phase 2 criteria met"},
        "accounts_opened": {"target": 3, "description": "Sportsbook accounts opened"},
        "real_bets_placed": {"target": 500, "description": "Real money bets placed"},
        "real_roi_matches_paper": {"target": true, "description": "Real ROI within 2% of paper ROI"},
        "bankroll_growth": {"target": 1500, "description": "Bankroll grown to $1500+"}
    }'::jsonb,
    CURRENT_DATE + INTERVAL '365 days',
    'pending'
),
(
    'Add NBA League',
    'Sport Expansion',
    'NFL edge validated, ready to add NBA (October season start)',
    '{
        "nfl_validated": {"target": true, "description": "NFL Validated Edge milestone complete"},
        "season_timing": {"target": "October", "description": "NBA season timing (October-April)"},
        "api_quota_available": {"target": true, "description": "API quota allows multi-sport"}
    }'::jsonb,
    NULL,
    'pending'
),
(
    'Add NHL League',
    'Sport Expansion',
    'NFL+NBA validated, ready to add NHL (October season start)',
    '{
        "nfl_validated": {"target": true, "description": "NFL Validated Edge milestone complete"},
        "nba_validated": {"target": true, "description": "NBA performing well (CLV > 0%)"},
        "season_timing": {"target": "October", "description": "NHL season timing (October-April)"},
        "api_quota_available": {"target": true, "description": "API quota allows multi-sport"}
    }'::jsonb,
    NULL,
    'pending'
);

-- Function to update milestone status automatically
CREATE OR REPLACE FUNCTION update_milestone_status()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.all_criteria_met = TRUE AND (
        SELECT status FROM milestones WHERE id = NEW.milestone_id
    ) != 'completed' THEN
        UPDATE milestones
        SET status = 'completed', completed_at = NEW.checked_at
        WHERE id = NEW.milestone_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-complete milestones when criteria met
CREATE TRIGGER milestone_auto_complete
AFTER INSERT ON milestone_checks
FOR EACH ROW
EXECUTE FUNCTION update_milestone_status();

-- View for current milestone status
CREATE OR REPLACE VIEW milestone_status_current AS
SELECT
    m.id,
    m.name,
    m.phase,
    m.description,
    m.status,
    m.target_date,
    m.completed_at,
    mc.checked_at AS last_checked,
    mc.criteria_met,
    mc.all_criteria_met,
    CASE
        WHEN m.target_date IS NOT NULL THEN m.target_date - CURRENT_DATE
        ELSE NULL
    END AS days_remaining
FROM milestones m
LEFT JOIN LATERAL (
    SELECT * FROM milestone_checks
    WHERE milestone_id = m.id
    ORDER BY checked_at DESC
    LIMIT 1
) mc ON TRUE
ORDER BY
    CASE m.status
        WHEN 'in_progress' THEN 1
        WHEN 'blocked' THEN 2
        WHEN 'pending' THEN 3
        WHEN 'completed' THEN 4
    END,
    m.target_date NULLS LAST;

COMMENT ON VIEW milestone_status_current IS 'Current status of all milestones with latest check results';
