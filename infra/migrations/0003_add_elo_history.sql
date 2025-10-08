-- Migration: Add ELO history tracking table
-- Records ELO rating changes after each game settlement

CREATE TABLE IF NOT EXISTS elo_history (
    id SERIAL PRIMARY KEY,
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    pre_elo DOUBLE PRECISION NOT NULL,
    post_elo DOUBLE PRECISION NOT NULL,
    delta DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(game_id, team_id)
);

CREATE INDEX IF NOT EXISTS idx_elo_history_game_id ON elo_history(game_id);
CREATE INDEX IF NOT EXISTS idx_elo_history_team_id ON elo_history(team_id);
CREATE INDEX IF NOT EXISTS idx_elo_history_created_at ON elo_history(created_at DESC);

COMMENT ON TABLE elo_history IS 'Historical record of ELO rating changes after game settlements';
COMMENT ON COLUMN elo_history.pre_elo IS 'ELO rating before the game';
COMMENT ON COLUMN elo_history.post_elo IS 'ELO rating after the game';
COMMENT ON COLUMN elo_history.delta IS 'Change in ELO rating (post - pre)';
