-- sports-edge initial schema
-- Run this against your Postgres instance (Neon/Supabase)

-- Enable uuid extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Teams
CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    abbreviation VARCHAR(10),
    sport VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_teams_sport ON teams(sport);
CREATE INDEX idx_teams_external_id ON teams(external_id);

-- Players
CREATE TABLE IF NOT EXISTS players (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    team_id INTEGER REFERENCES teams(id),
    position VARCHAR(50),
    sport VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_players_team_id ON players(team_id);
CREATE INDEX idx_players_sport ON players(sport);
CREATE INDEX idx_players_external_id ON players(external_id);

-- Games
CREATE TABLE IF NOT EXISTS games (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(100) UNIQUE NOT NULL,
    sport VARCHAR(50) NOT NULL,
    home_team_id INTEGER REFERENCES teams(id),
    away_team_id INTEGER REFERENCES teams(id),
    scheduled_at TIMESTAMP NOT NULL,
    status VARCHAR(50) DEFAULT 'scheduled', -- scheduled, in_progress, final, postponed
    home_score INTEGER,
    away_score INTEGER,
    season VARCHAR(20),
    week INTEGER,
    venue VARCHAR(255),
    weather_conditions JSONB, -- {temp, wind, precip}
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_games_sport ON games(sport);
CREATE INDEX idx_games_scheduled_at ON games(scheduled_at);
CREATE INDEX idx_games_status ON games(status);
CREATE INDEX idx_games_home_team ON games(home_team_id);
CREATE INDEX idx_games_away_team ON games(away_team_id);

-- Markets (types of bets: spread, total, moneyline, player_props)
CREATE TABLE IF NOT EXISTS markets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL, -- e.g., "spread", "total_points", "anytime_td"
    category VARCHAR(50) NOT NULL, -- game, player_prop
    sport VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_markets_sport ON markets(sport);
CREATE INDEX idx_markets_category ON markets(category);

-- Odds Snapshots (time-series of odds from different books)
CREATE TABLE IF NOT EXISTS odds_snapshots (
    id SERIAL PRIMARY KEY,
    game_id INTEGER REFERENCES games(id),
    player_id INTEGER REFERENCES players(id), -- NULL for game-level markets
    market_id INTEGER REFERENCES markets(id),
    sportsbook VARCHAR(50) NOT NULL, -- draftkings, caesars, etc.
    line_value DECIMAL(10, 2), -- spread/total line (e.g., -3.5, 45.5)
    selection VARCHAR(150),
    odds_american INTEGER, -- American odds (e.g., -110, +150)
    odds_decimal DECIMAL(10, 3), -- Decimal odds (e.g., 1.909, 2.500)
    implied_probability DECIMAL(5, 4), -- e.g., 0.5238
    fetched_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_odds_game_id ON odds_snapshots(game_id);
CREATE INDEX idx_odds_player_id ON odds_snapshots(player_id);
CREATE INDEX idx_odds_market_id ON odds_snapshots(market_id);
CREATE INDEX idx_odds_sportsbook ON odds_snapshots(sportsbook);
CREATE INDEX idx_odds_fetched_at ON odds_snapshots(fetched_at DESC);

-- Signals (model-generated betting opportunities)
CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    game_id INTEGER REFERENCES games(id),
    player_id INTEGER REFERENCES players(id),
    market_id INTEGER REFERENCES markets(id),
    sportsbook VARCHAR(50) NOT NULL,
    line_value DECIMAL(10, 2),
    selection VARCHAR(150),
    odds_american INTEGER,
    fair_probability DECIMAL(5, 4), -- model-estimated true probability
    implied_probability DECIMAL(5, 4), -- book's implied probability
    edge_percent DECIMAL(5, 2), -- edge in percentage points
    kelly_fraction DECIMAL(5, 4), -- full Kelly fraction
    recommended_stake_pct DECIMAL(5, 2), -- fractional Kelly (e.g., 0.25)
    confidence_level VARCHAR(20), -- high, medium, low
    model_version VARCHAR(50),
    generated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP, -- when game starts or line expires
    status VARCHAR(50) DEFAULT 'active', -- active, expired, placed, skipped
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_signals_status ON signals(status);
CREATE INDEX idx_signals_game_id ON signals(game_id);
CREATE INDEX idx_signals_generated_at ON signals(generated_at DESC);
CREATE INDEX idx_signals_edge_percent ON signals(edge_percent DESC);

-- Bets (actual wagers placed by user)
CREATE TABLE IF NOT EXISTS bets (
    id SERIAL PRIMARY KEY,
    signal_id INTEGER REFERENCES signals(id),
    game_id INTEGER REFERENCES games(id),
    player_id INTEGER REFERENCES players(id),
    market_id INTEGER REFERENCES markets(id),
    sportsbook VARCHAR(50) NOT NULL,
    line_value DECIMAL(10, 2),
    selection VARCHAR(150),
    odds_american INTEGER,
    stake_amount DECIMAL(10, 2), -- in dollars
    placed_at TIMESTAMP NOT NULL,
    settled_at TIMESTAMP,
    result VARCHAR(50), -- win, loss, push, void
    profit_loss DECIMAL(10, 2), -- net P&L
    clv_percent DECIMAL(5, 2), -- closing line value vs our entry
    close_odds_american INTEGER, -- closing line odds
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_bets_signal_id ON bets(signal_id);
CREATE INDEX idx_bets_game_id ON bets(game_id);
CREATE INDEX idx_bets_sportsbook ON bets(sportsbook);
CREATE INDEX idx_bets_placed_at ON bets(placed_at DESC);
CREATE INDEX idx_bets_result ON bets(result);

-- Results (final stats for settlement)
CREATE TABLE IF NOT EXISTS results (
    id SERIAL PRIMARY KEY,
    game_id INTEGER REFERENCES games(id),
    player_id INTEGER REFERENCES players(id),
    stat_type VARCHAR(100), -- points, rebounds, touchdowns, etc.
    stat_value DECIMAL(10, 2),
    source VARCHAR(100), -- API or manual entry
    recorded_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_results_game_id ON results(game_id);
CREATE INDEX idx_results_player_id ON results(player_id);
CREATE INDEX idx_results_stat_type ON results(stat_type);

-- Promotions (bonus offers, boosts, etc.)
CREATE TABLE IF NOT EXISTS promos (
    id SERIAL PRIMARY KEY,
    sportsbook VARCHAR(50) NOT NULL,
    promo_type VARCHAR(50), -- deposit_match, odds_boost, bet_insurance
    description TEXT,
    terms TEXT,
    rollover_requirement INTEGER, -- e.g., 1x, 5x
    max_bonus DECIMAL(10, 2),
    min_odds INTEGER, -- minimum odds to qualify
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    estimated_ev DECIMAL(10, 2), -- expected value in dollars
    status VARCHAR(50) DEFAULT 'active', -- active, used, expired
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_promos_sportsbook ON promos(sportsbook);
CREATE INDEX idx_promos_status ON promos(status);
CREATE INDEX idx_promos_end_date ON promos(end_date);

-- CLV History (closing line value tracking)
CREATE TABLE IF NOT EXISTS clv_history (
    id SERIAL PRIMARY KEY,
    bet_id INTEGER REFERENCES bets(id),
    entry_odds_american INTEGER,
    close_odds_american INTEGER,
    clv_percent DECIMAL(5, 2),
    recorded_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_clv_bet_id ON clv_history(bet_id);
CREATE INDEX idx_clv_recorded_at ON clv_history(recorded_at DESC);

-- Model Metrics (track model performance over time)
CREATE TABLE IF NOT EXISTS model_metrics (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    metric_type VARCHAR(50), -- brier_score, calibration, log_loss, roi
    metric_value DECIMAL(10, 4),
    sample_size INTEGER,
    sport VARCHAR(50),
    market_category VARCHAR(50),
    recorded_at TIMESTAMP DEFAULT NOW(),
    notes TEXT
);

CREATE INDEX idx_model_metrics_name_version ON model_metrics(model_name, model_version);
CREATE INDEX idx_model_metrics_recorded_at ON model_metrics(recorded_at DESC);

-- Audit log (immutable record of all signal generation and bet decisions)
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL, -- signal_generated, bet_placed, bet_settled, model_updated
    entity_type VARCHAR(50), -- signal, bet, model
    entity_id INTEGER,
    user_action VARCHAR(50), -- auto, manual
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_event_type ON audit_log(event_type);
CREATE INDEX idx_audit_created_at ON audit_log(created_at DESC);

-- Create read-only role (run separately with appropriate permissions)
-- This is a template; adjust based on your cloud provider's RBAC
/*
CREATE ROLE sports_edge_readonly WITH LOGIN PASSWORD 'your_readonly_password';
GRANT CONNECT ON DATABASE your_database TO sports_edge_readonly;
GRANT USAGE ON SCHEMA public TO sports_edge_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO sports_edge_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO sports_edge_readonly;
*/
