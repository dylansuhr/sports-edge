#!/usr/bin/env python3
"""
Capture Closing Lines for CLV Tracking

Fetches odds shortly before games start and calculates CLV for active signals.
This script should run 5-10 minutes before each game's scheduled start time.

Usage:
    python ops/scripts/capture_closing_lines.py --sport nfl
    python ops/scripts/capture_closing_lines.py --leagues nfl,nba,nhl
"""

import argparse
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, List
from dotenv import load_dotenv

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'packages'))

from shared.shared.odds_math import calculate_clv
from shared.shared.db import get_db

# Load environment
load_dotenv()


def check_env_vars():
    """Validate required environment variables."""
    required = ['DATABASE_URL']
    missing = [var for var in required if not os.getenv(var)]

    if missing:
        print(f"[ERROR] Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)


class ClosingLineCapture:
    """Capture closing lines and calculate CLV for signals."""

    def __init__(self):
        self.db = get_db()

    def get_games_starting_soon(self, league: str, minutes_ahead: int = 30) -> List[Dict]:
        """
        Get games starting in the next N minutes.

        Args:
            league: League filter (nfl, nba, nhl)
            minutes_ahead: Look ahead window in minutes

        Returns:
            List of game dicts
        """
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(minutes=minutes_ahead)

        print(f"[CLV] Looking for {league.upper()} games starting between:")
        print(f"[CLV]   NOW: {now.isoformat()}")
        print(f"[CLV]   {minutes_ahead}min ahead: {cutoff.isoformat()}")

        sql = """
            SELECT
                g.id as game_id,
                g.external_id,
                g.scheduled_at,
                g.home_team_id,
                g.away_team_id,
                t_home.name as home_team,
                t_away.name as away_team,
                g.sport
            FROM games g
            JOIN teams t_home ON g.home_team_id = t_home.id
            JOIN teams t_away ON g.away_team_id = t_away.id
            WHERE g.sport = %s
                AND g.status = 'scheduled'
                AND g.scheduled_at BETWEEN NOW() AND NOW() + INTERVAL '%s minutes'
            ORDER BY g.scheduled_at ASC
        """

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (league, minutes_ahead))
                columns = [desc[0] for desc in cur.description]
                games = [dict(zip(columns, row)) for row in cur.fetchall()]

        print(f"[CLV] Found {len(games)} games starting soon")
        return games

    def get_active_signals_for_game(self, game_id: int) -> List[Dict]:
        """Get all active signals for a game that don't have CLV calculated yet."""
        sql = """
            SELECT
                s.id,
                s.game_id,
                s.market_id,
                s.sportsbook,
                s.odds_american as entry_odds,
                s.line_value,
                s.selection,
                s.created_at,
                m.name as market_name
            FROM signals s
            JOIN markets m ON s.market_id = m.id
            WHERE s.game_id = %s
                AND s.status = 'active'
                AND s.closing_odds_american IS NULL
            ORDER BY s.created_at
        """

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (game_id,))
                columns = [desc[0] for desc in cur.description]
                signals = [dict(zip(columns, row)) for row in cur.fetchall()]

        return signals

    def get_closing_odds(
        self,
        game_id: int,
        market_id: int,
        sportsbook: str,
        line_value: float = None,
        selection: str = None
    ) -> int:
        """
        Get the most recent odds for a specific market/sportsbook/line combination.

        Args:
            game_id: Game ID
            market_id: Market ID
            sportsbook: Sportsbook name
            line_value: Line value (for spreads/totals)
            selection: Market side (team name, Over/Under, etc.)

        Returns:
            American odds (most recent), or None if not found
        """
        sql = """
            SELECT odds_american, fetched_at
            FROM odds_snapshots
            WHERE game_id = %s
                AND market_id = %s
                AND sportsbook = %s
                AND (line_value = %s OR (line_value IS NULL AND %s IS NULL))
                AND (selection = %s OR (%s IS NULL AND selection IS NULL))
            ORDER BY fetched_at DESC
            LIMIT 1
        """

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (
                    game_id,
                    market_id,
                    sportsbook,
                    line_value,
                    line_value,
                    selection,
                    selection
                ))
                result = cur.fetchone()

                if result:
                    return result[0]  # odds_american
                return None

    def update_signal_clv(self, signal_id: int, closing_odds: int, clv_pct: float):
        """Update a signal with closing line information."""
        sql = """
            UPDATE signals
            SET closing_odds_american = %s,
                closing_odds_fetched_at = NOW(),
                clv_percent = %s
            WHERE id = %s
        """

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (closing_odds, clv_pct, signal_id))
                conn.commit()

    def process_game(self, game: Dict):
        """Process a single game: capture closing lines and calculate CLV."""
        game_id = game['game_id']
        print(f"\n[CLV] Processing game #{game_id}: {game['home_team']} vs {game['away_team']}")
        print(f"[CLV]   Starts at: {game['scheduled_at'].isoformat()}")

        # Get active signals for this game
        signals = self.get_active_signals_for_game(game_id)

        if not signals:
            print(f"[CLV]   No active signals to track")
            return

        print(f"[CLV]   Found {len(signals)} active signals")

        clv_results = []

        for signal in signals:
            signal_id = signal['id']
            entry_odds = signal['entry_odds']
            line_value = signal.get('line_value')
            selection = signal.get('selection')

            # Get closing odds
            closing_odds = self.get_closing_odds(
                game_id,
                signal['market_id'],
                signal['sportsbook'],
                line_value,
                selection
            )

            if not closing_odds:
                print(f"[CLV]     ⚠️  No closing odds found for signal #{signal_id} ({signal['sportsbook']} – {selection or 'unknown selection'})")
                continue

            # Calculate CLV
            clv_pct = calculate_clv(entry_odds, closing_odds)

            # Update signal
            self.update_signal_clv(signal_id, closing_odds, clv_pct)

            clv_results.append({
                'signal_id': signal_id,
                'sportsbook': signal['sportsbook'],
                'market': signal['market_name'],
                'entry_odds': entry_odds,
                'closing_odds': closing_odds,
                'clv_pct': clv_pct
            })

            # Log
            status_icon = "✅" if clv_pct > 0 else "❌"
            print(f"[CLV]     {status_icon} Signal #{signal_id} ({signal['sportsbook']} {signal['market_name']}): "
                  f"Entry {entry_odds:+d} → Close {closing_odds:+d} | CLV: {clv_pct:+.2f}%")

        # Summary
        if clv_results:
            avg_clv = sum(r['clv_pct'] for r in clv_results) / len(clv_results)
            positive_clv = sum(1 for r in clv_results if r['clv_pct'] > 0)
            print(f"\n[CLV]   Summary: {positive_clv}/{len(clv_results)} signals beat closing line | "
                  f"Avg CLV: {avg_clv:+.2f}%")


def main():
    parser = argparse.ArgumentParser(description='Capture closing lines for CLV tracking')
    parser.add_argument('--leagues', type=str, help='Comma-separated leagues (default: nfl,nba,nhl)')
    parser.add_argument('--minutes-ahead', type=int, default=30,
                        help='Look ahead window in minutes (default: 30)')

    args = parser.parse_args()

    # Check environment
    check_env_vars()

    # Get leagues
    leagues_str = args.leagues or os.getenv('LEAGUES', 'nfl,nba,nhl')
    leagues = [l.strip() for l in leagues_str.split(',')]

    print(f"[CLV] Starting closing line capture for: {', '.join(leagues)}")
    print(f"[CLV] Look-ahead window: {args.minutes_ahead} minutes")

    # Initialize
    capture = ClosingLineCapture()

    # Process each league
    total_signals_processed = 0

    for league in leagues:
        print(f"\n[CLV] ===== {league.upper()} =====")

        # Get games starting soon
        games = capture.get_games_starting_soon(league, args.minutes_ahead)

        if not games:
            print(f"[CLV] No {league.upper()} games starting in next {args.minutes_ahead} minutes")
            continue

        # Process each game
        for game in games:
            capture.process_game(game)
            total_signals_processed += len(capture.get_active_signals_for_game(game['game_id']))

    # Final summary
    print(f"\n[CLV] ===== SUMMARY =====")
    print(f"[CLV] Leagues processed: {len(leagues)}")
    print(f"[CLV] Signals with CLV calculated: {total_signals_processed}")


if __name__ == '__main__':
    main()
