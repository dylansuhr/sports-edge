-- Migration: Add ELO tracking table
-- Stores dynamic team strength ratings updated after each game

CREATE TABLE IF NOT EXISTS team_elos (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    elo_rating NUMERIC(10, 2) NOT NULL DEFAULT 1500.00,
    games_played INTEGER NOT NULL DEFAULT 0,
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(team_id)
);

CREATE INDEX idx_team_elos_team_id ON team_elos(team_id);
CREATE INDEX idx_team_elos_rating ON team_elos(elo_rating DESC);

COMMENT ON TABLE team_elos IS 'ELO ratings for team strength tracking';
COMMENT ON COLUMN team_elos.elo_rating IS 'Current ELO rating (default 1500, higher = stronger)';
COMMENT ON COLUMN team_elos.games_played IS 'Number of games processed for this rating';
