"""
Database utilities with idempotent upserts and transaction safety.

Handles all database writes with proper error handling and retry logic.
"""

import os
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from contextlib import contextmanager


class DatabaseError(Exception):
    """Custom exception for database errors."""
    pass


class Database:
    """Database connection and operations manager."""

    def __init__(self, connection_string: str = None, max_retries: int = 3):
        """
        Initialize database connection.

        Args:
            connection_string: Postgres connection string (defaults to DATABASE_URL env var)
            max_retries: Maximum number of retry attempts for transient failures
        """
        self.connection_string = connection_string or os.getenv('DATABASE_URL')
        if not self.connection_string:
            raise ValueError("DATABASE_URL is required")

        # Append connection options from DB_CONN_OPTS
        db_conn_opts = os.getenv('DB_CONN_OPTS', 'sslmode=require&connect_timeout=5')
        if db_conn_opts:
            if '?' in self.connection_string:
                self.connection_string += f'&{db_conn_opts}'
            else:
                self.connection_string += f'?{db_conn_opts}'

        self.max_retries = max_retries
        self._conn = None

    @contextmanager
    def get_connection(self):
        """Get a database connection (context manager)."""
        conn = psycopg2.connect(self.connection_string)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def execute_with_retry(self, func, *args, **kwargs):
        """Execute a function with retry logic for transient failures."""
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except psycopg2.OperationalError as e:
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"[DB] Transient error, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    raise DatabaseError(f"Failed after {self.max_retries} attempts: {e}")
            except Exception as e:
                raise DatabaseError(f"Database error: {e}")

    # ===== Team Operations =====

    def upsert_team(
        self,
        external_id: str,
        name: str,
        abbreviation: str,
        sport: str
    ) -> int:
        """
        Upsert a team (insert or update if exists).

        Returns:
            team_id
        """
        def _upsert():
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO teams (external_id, name, abbreviation, sport)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (external_id)
                        DO UPDATE SET
                            name = EXCLUDED.name,
                            abbreviation = EXCLUDED.abbreviation,
                            updated_at = NOW()
                        RETURNING id
                    """, (external_id, name, abbreviation, sport))
                    return cur.fetchone()[0]

        return self.execute_with_retry(_upsert)

    # ===== Game Operations =====

    def upsert_game(
        self,
        external_id: str,
        sport: str,
        home_team_id: int,
        away_team_id: int,
        scheduled_at: str,
        season: str = None,
        week: int = None
    ) -> int:
        """
        Upsert a game.

        Returns:
            game_id
        """
        def _upsert():
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO games (
                            external_id, sport, home_team_id, away_team_id,
                            scheduled_at, season, week
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (external_id)
                        DO UPDATE SET
                            scheduled_at = EXCLUDED.scheduled_at,
                            updated_at = NOW()
                        RETURNING id
                    """, (external_id, sport, home_team_id, away_team_id, scheduled_at, season, week))
                    return cur.fetchone()[0]

        return self.execute_with_retry(_upsert)

    # ===== Market Operations =====

    def upsert_market(
        self,
        name: str,
        category: str,
        sport: str,
        description: str = None
    ) -> int:
        """
        Upsert a market.

        Returns:
            market_id
        """
        def _upsert():
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO markets (name, category, sport, description)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (name)
                        DO UPDATE SET
                            description = EXCLUDED.description
                        RETURNING id
                    """, (name, category, sport, description))
                    return cur.fetchone()[0]

        return self.execute_with_retry(_upsert)

    # ===== Odds Snapshot Operations =====

    def insert_odds_snapshot(
        self,
        game_id: int,
        market_id: int,
        sportsbook: str,
        odds_american: int,
        odds_decimal: float,
        implied_probability: float,
        selection: str = None,
        line_value: float = None,
        player_id: int = None,
        fetched_at: str = None
    ):
        """Insert an odds snapshot (always insert, never update)."""
        def _insert():
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO odds_snapshots (
                            game_id, player_id, market_id, sportsbook, selection,
                            line_value, odds_american, odds_decimal,
                            implied_probability, fetched_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        game_id, player_id, market_id, sportsbook, selection,
                        line_value, odds_american, odds_decimal,
                        implied_probability, fetched_at or datetime.utcnow()
                    ))

        return self.execute_with_retry(_insert)

    def bulk_insert_odds_snapshots(self, snapshots: List[Dict]):
        """Bulk insert odds snapshots for performance."""
        if not snapshots:
            return

        def _bulk_insert():
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    values = [
                        (
                            s['game_id'], s.get('player_id'), s['market_id'],
                            s['sportsbook'], s.get('selection'), s.get('line_value'),
                            s['odds_american'], s['odds_decimal'],
                            s['implied_probability'], s.get('fetched_at')
                        )
                        for s in snapshots
                    ]

                    execute_values(cur, """
                        INSERT INTO odds_snapshots (
                            game_id, player_id, market_id, sportsbook, selection,
                            line_value, odds_american, odds_decimal,
                            implied_probability, fetched_at
                        ) VALUES %s
                    """, values)

        return self.execute_with_retry(_bulk_insert)

    # ===== Signal Operations =====

    def insert_signal(
        self,
        game_id: int,
        market_id: int,
        sportsbook: str,
        odds_american: int,
        fair_probability: float,
        implied_probability: float,
        edge_percent: float,
        kelly_fraction: float,
        recommended_stake_pct: float,
        confidence_level: str,
        model_version: str,
        expires_at: str,
        line_value: float = None,
        player_id: int = None,
        raw_implied_probability: float = None,
        selection: str = None
    ) -> int:
        """Insert or update a betting signal (upsert to handle duplicates)."""
        def _insert():
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO signals (
                            game_id, player_id, market_id, sportsbook,
                            line_value, selection, odds_american, fair_probability,
                            implied_probability, raw_implied_probability, edge_percent, kelly_fraction,
                            recommended_stake_pct, confidence_level,
                            model_version, expires_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (game_id, market_id, odds_american, sportsbook)
                        WHERE status = 'active'
                        DO UPDATE SET
                            fair_probability = EXCLUDED.fair_probability,
                            implied_probability = EXCLUDED.implied_probability,
                            raw_implied_probability = EXCLUDED.raw_implied_probability,
                            selection = EXCLUDED.selection,
                            edge_percent = EXCLUDED.edge_percent,
                            kelly_fraction = EXCLUDED.kelly_fraction,
                            recommended_stake_pct = EXCLUDED.recommended_stake_pct,
                            confidence_level = EXCLUDED.confidence_level,
                            model_version = EXCLUDED.model_version,
                            expires_at = EXCLUDED.expires_at,
                            generated_at = CURRENT_TIMESTAMP
                        RETURNING id
                    """, (
                        game_id, player_id, market_id, sportsbook,
                        line_value, selection, odds_american, fair_probability,
                        implied_probability, raw_implied_probability, edge_percent, kelly_fraction,
                        recommended_stake_pct, confidence_level,
                        model_version, expires_at
                    ))
                    return cur.fetchone()[0]

        return self.execute_with_retry(_insert)

    # ===== Results Operations =====

    def insert_result(
        self,
        game_id: int,
        stat_type: str,
        stat_value: float,
        source: str,
        player_id: int = None
    ):
        """Insert a game/player result."""
        def _insert():
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO results (game_id, player_id, stat_type, stat_value, source)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (game_id, player_id, stat_type, stat_value, source))

        return self.execute_with_retry(_insert)

    def update_game_result(
        self,
        game_id: int,
        home_score: int,
        away_score: int,
        status: str = 'final'
    ):
        """Update game with final scores."""
        def _update():
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE games
                        SET home_score = %s,
                            away_score = %s,
                            status = %s,
                            updated_at = NOW()
                        WHERE id = %s
                    """, (home_score, away_score, status, game_id))

        return self.execute_with_retry(_update)

    # ===== Query Operations =====

    def find_team_by_external_id(self, external_id: str) -> Optional[Dict]:
        """Find team by external ID."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM teams WHERE external_id = %s", (external_id,))
                return cur.fetchone()

    def find_game_by_external_id(self, external_id: str) -> Optional[Dict]:
        """Find game by external ID."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM games WHERE external_id = %s", (external_id,))
                return cur.fetchone()

    def find_market_by_name(self, name: str) -> Optional[Dict]:
        """Find market by name."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM markets WHERE name = %s", (name,))
                return cur.fetchone()

    def check_table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_name = %s
                    )
                """, (table_name,))
                return cur.fetchone()[0]

    def check_core_tables(self, required_tables: List[str] = None) -> tuple:
        """
        Check if core tables exist. Returns (all_exist, missing_tables).

        Args:
            required_tables: List of table names to check. Defaults to core tables.

        Returns:
            Tuple of (bool, list) - (all exist?, list of missing tables)
        """
        if required_tables is None:
            required_tables = ['teams', 'games', 'markets', 'odds_snapshots', 'signals']

        missing = []
        for table in required_tables:
            if not self.check_table_exists(table):
                missing.append(table)

        return (len(missing) == 0, missing)

    # ===== ELO Rating Operations =====

    def get_team_elo(self, team_id: int) -> float:
        """
        Get current ELO rating for a team.

        Returns 1500.0 if team not found (default rating).
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT elo_rating
                    FROM team_elos
                    WHERE team_id = %s
                """, (team_id,))
                row = cur.fetchone()

                if row:
                    return float(row[0])
                else:
                    return 1500.0

    def upsert_team_elo(self, team_id: int, elo_rating: float, games_played: int = None):
        """
        Update or insert team ELO rating.

        Args:
            team_id: Team ID
            elo_rating: New ELO rating
            games_played: Number of games played (optional, will increment if not provided)
        """
        def _upsert():
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    if games_played is not None:
                        cur.execute("""
                            INSERT INTO team_elos (team_id, elo_rating, games_played, last_updated)
                            VALUES (%s, %s, %s, NOW())
                            ON CONFLICT (team_id)
                            DO UPDATE SET
                                elo_rating = EXCLUDED.elo_rating,
                                games_played = EXCLUDED.games_played,
                                last_updated = NOW()
                        """, (team_id, elo_rating, games_played))
                    else:
                        cur.execute("""
                            INSERT INTO team_elos (team_id, elo_rating, games_played, last_updated)
                            VALUES (%s, %s, 1, NOW())
                            ON CONFLICT (team_id)
                            DO UPDATE SET
                                elo_rating = EXCLUDED.elo_rating,
                                games_played = team_elos.games_played + 1,
                                last_updated = NOW()
                        """, (team_id, elo_rating))

        return self.execute_with_retry(_upsert)

    def get_all_team_elos(self, sport: str = None) -> Dict[int, float]:
        """
        Get all team ELO ratings as a dictionary.

        Args:
            sport: Optional sport filter

        Returns:
            Dict mapping team_id -> elo_rating
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                if sport:
                    cur.execute("""
                        SELECT te.team_id, te.elo_rating
                        FROM team_elos te
                        JOIN teams t ON te.team_id = t.id
                        WHERE t.sport = %s
                    """, (sport,))
                else:
                    cur.execute("""
                        SELECT team_id, elo_rating
                        FROM team_elos
                    """)

                return {row[0]: float(row[1]) for row in cur.fetchall()}

    def upsert_elo_history(
        self,
        game_id: int,
        team_id: int,
        pre_elo: float,
        post_elo: float
    ):
        """
        Record ELO rating change after a game (idempotent).

        Args:
            game_id: Game ID
            team_id: Team ID
            pre_elo: ELO rating before the game
            post_elo: ELO rating after the game
        """
        delta = post_elo - pre_elo

        def _upsert():
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO elo_history (game_id, team_id, pre_elo, post_elo, delta, created_at)
                        VALUES (%s, %s, %s, %s, %s, NOW())
                        ON CONFLICT (game_id, team_id)
                        DO UPDATE SET
                            pre_elo = EXCLUDED.pre_elo,
                            post_elo = EXCLUDED.post_elo,
                            delta = EXCLUDED.delta,
                            created_at = NOW()
                    """, (game_id, team_id, pre_elo, post_elo, delta))

        return self.execute_with_retry(_upsert)


# Singleton instance
_db_instance = None


def get_db() -> Database:
    """Get database singleton instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
