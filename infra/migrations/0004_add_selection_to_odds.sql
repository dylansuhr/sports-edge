-- Migration 0004: Add selection column to odds_snapshots
--
-- Purpose: Track which side/team each odds row represents
-- Examples: "Green Bay Packers", "Cincinnati Bengals", "Over", "Under"
--
-- This enables per-selection fair probability calculations for accurate edge detection

\echo '🔄 Adding selection column to odds_snapshots...'

-- Add selection column
ALTER TABLE odds_snapshots
ADD COLUMN IF NOT EXISTS selection VARCHAR(100);

-- Add index for faster filtering by selection
CREATE INDEX IF NOT EXISTS idx_odds_selection ON odds_snapshots(selection);

-- Verify column added
SELECT COUNT(*) as rows_with_selection
FROM odds_snapshots
WHERE selection IS NOT NULL;

\echo '✅ Migration 0004 complete - selection column added'
