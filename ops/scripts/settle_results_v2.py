#!/usr/bin/env python3
"""
Results Settlement Script (v2 - API-Driven with ELO Updates)

Fetches game results from The Odds API, updates game scores, settles bets,
calculates Closing Line Value (CLV), and updates team ELO ratings.

Usage:
    python ops/scripts/settle_results_v2.py --leagues nfl
    python ops/scripts/settle_results_v2.py --days 2
"""

import argparse
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'packages'))

from providers.results import fetch_results
from shared.shared.db import get_db
from shared.shared.odds_math import calculate_clv, profit_from_bet

# Load environment
load_dotenv()

# ELO constants
K_FACTOR = 20.0
HOME_ADVANTAGE = 25.0


def check_env_vars():
    """Validate required environment variables."""
    required = ['DATABASE_URL']
    missing = [var for var in required if not os.getenv(var)]

    if missing:
        print(f"[ERROR] Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)


def safe_float(value) -> float:
    """Coerce Decimal or any numeric type to float."""
    if value is None:
        return 0.0
    return float(value)


def expected_win_probability(elo_a: float, elo_b: float) -> float:
    """
    Calculate expected win probability using ELO formula.

    Args:
        elo_a: Team A's ELO rating (already adjusted for home advantage if applicable)
        elo_b: Team B's ELO rating

    Returns:
        Probability that team A wins (0.0 to 1.0)
    """
    return 1.0 / (1.0 + 10.0 ** ((elo_b - elo_a) / 400.0))


def update_elo_ratings(
    home_elo: float,
    away_elo: float,
    home_score: int,
    away_score: int
) -> tuple[float, float]:
    """
    Update ELO ratings for both teams after a game.

    Args:
        home_elo: Home team's current ELO
        away_elo: Away team's current ELO
        home_score: Home team's final score
        away_score: Away team's final score

    Returns:
        Tuple of (new_home_elo, new_away_elo)
    """
    # Determine actual outcome
    if home_score > away_score:
        actual_home = 1.0
        actual_away = 0.0
    elif home_score < away_score:
        actual_home = 0.0
        actual_away = 1.0
    else:  # Tie
        actual_home = 0.5
        actual_away = 0.5

    # Calculate expected probabilities (with home advantage)
    home_elo_adjusted = home_elo + HOME_ADVANTAGE
    expected_home = expected_win_probability(home_elo_adjusted, away_elo)
    expected_away = 1.0 - expected_home

    # Update ratings
    new_home_elo = home_elo + K_FACTOR * (actual_home - expected_home)
    new_away_elo = away_elo + K_FACTOR * (actual_away - expected_away)

    return new_home_elo, new_away_elo


class SettlementProcessor:
    """Process game results, settle bets, and update ELO ratings."""

    def __init__(self):
        self.db = get_db()

    def find_game_by_teams_and_date(
        self,
        league: str,
        home_team: str,
        away_team: str,
        game_date: str
    ) -> Optional[Dict]:
        """Find game in database by teams and date."""
        sql = """
            SELECT
                g.id as game_id,
                g.external_id,
                g.scheduled_at,
                g.home_team_id,
                g.away_team_id,
                g.status,
                t_home.name as home_team,
                t_away.name as away_team
            FROM games g
            JOIN teams t_home ON g.home_team_id = t_home.id
            JOIN teams t_away ON g.away_team_id = t_away.id
            WHERE g.sport = %s
                AND t_home.name = %s
                AND t_away.name = %s
                AND DATE(g.scheduled_at) = DATE(%s)
        """

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (league, home_team, away_team, game_date))
                row = cur.fetchone()

                if row:
                    columns = [desc[0] for desc in cur.description]
                    return dict(zip(columns, row))

        return None

    def update_game_with_results(
        self,
        game_id: int,
        home_score: int,
        away_score: int
    ):
        """Update game with final scores."""
        self.db.update_game_result(game_id, home_score, away_score, status='final')

    def get_closing_line(
        self,
        game_id: int,
        market_id: int,
        sportsbook: str
    ) -> Optional[int]:
        """
        Get closing line odds (last snapshot before game start, or up to 30min after).

        Returns American odds or None if not found.
        """
        sql = """
            SELECT odds_american
            FROM odds_snapshots
            WHERE game_id = %s
                AND market_id = %s
                AND sportsbook = %s
                AND fetched_at <= (SELECT scheduled_at FROM games WHERE id = %s) + INTERVAL '30 minutes'
            ORDER BY fetched_at DESC
            LIMIT 1
        """

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (game_id, market_id, sportsbook, game_id))
                row = cur.fetchone()

                if row:
                    return row[0]

        return None

    def determine_bet_outcome(
        self,
        bet: Dict,
        home_score: int,
        away_score: int
    ) -> str:
        """
        Determine if bet won, lost, or pushed.

        Args:
            bet: Bet dict with market info
            home_score: Final home score
            away_score: Final away score

        Returns:
            'win', 'loss', 'push', or 'void'
        """
        market_name = bet['market_name']
        line_value = safe_float(bet.get('line_value'))

        if market_name == 'spread':
            if line_value is None:
                return 'void'

            # Assuming home team was bet (would need actual bet selection in production)
            adjusted_margin = (home_score - away_score) + line_value

            if adjusted_margin > 0:
                return 'win'
            elif adjusted_margin < 0:
                return 'loss'
            else:
                return 'push'

        elif market_name == 'total':
            if line_value is None:
                return 'void'

            total_points = home_score + away_score

            # Assuming "over" was bet (would need actual bet selection)
            if total_points > line_value:
                return 'win'
            elif total_points < line_value:
                return 'loss'
            else:
                return 'push'

        elif market_name == 'moneyline':
            # Assuming home team was bet (would need actual bet selection)
            if home_score > away_score:
                return 'win'
            elif home_score < away_score:
                return 'loss'
            else:
                return 'push'

        else:
            return 'void'

    def settle_bets_for_game(
        self,
        game_id: int,
        home_score: int,
        away_score: int
    ) -> Dict:
        """
        Settle all open bets for a completed game.

        Returns dict with settlement stats.
        """
        # Get open bets for this game
        sql = """
            SELECT
                b.id as bet_id,
                b.game_id,
                b.market_id,
                b.sportsbook,
                b.odds_american,
                b.stake_amount,
                b.line_value,
                m.name as market_name
            FROM bets b
            JOIN markets m ON b.market_id = m.id
            WHERE b.game_id = %s
                AND b.settled_at IS NULL
        """

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (game_id,))
                columns = [desc[0] for desc in cur.description]
                bets = [dict(zip(columns, row)) for row in cur.fetchall()]

        stats = {'settled': 0, 'wins': 0, 'losses': 0, 'pushes': 0, 'total_clv': 0.0}

        for bet in bets:
            try:
                # Determine outcome
                outcome = self.determine_bet_outcome(bet, home_score, away_score)

                # Calculate P&L
                if outcome == 'win':
                    pnl = profit_from_bet(safe_float(bet['stake_amount']), bet['odds_american'], won=True)
                    stats['wins'] += 1
                elif outcome == 'loss':
                    pnl = profit_from_bet(safe_float(bet['stake_amount']), bet['odds_american'], won=False)
                    stats['losses'] += 1
                else:  # push or void
                    pnl = 0.0
                    stats['pushes'] += 1

                # Get closing line for CLV
                close_odds = self.get_closing_line(
                    bet['game_id'],
                    bet['market_id'],
                    bet['sportsbook']
                )

                clv_pct = None
                if close_odds:
                    clv_pct = calculate_clv(bet['odds_american'], close_odds)
                    stats['total_clv'] += clv_pct

                # Update bet
                update_sql = """
                    UPDATE bets
                    SET result = %s,
                        profit_loss = %s,
                        clv_percent = %s,
                        close_odds_american = %s,
                        settled_at = NOW(),
                        updated_at = NOW()
                    WHERE id = %s
                """

                with self.db.get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            update_sql,
                            (outcome, pnl, clv_pct, close_odds, bet['bet_id'])
                        )

                # Insert CLV history record
                if clv_pct is not None:
                    clv_sql = """
                        INSERT INTO clv_history (
                            bet_id,
                            entry_odds_american,
                            close_odds_american,
                            clv_percent,
                            recorded_at
                        )
                        VALUES (%s, %s, %s, %s, NOW())
                    """

                    with self.db.get_connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute(
                                clv_sql,
                                (bet['bet_id'], bet['odds_american'], close_odds, clv_pct)
                            )

                stats['settled'] += 1

            except Exception as e:
                print(f"    ❌ Error settling bet #{bet['bet_id']}: {e}")
                continue

        return stats

    def update_team_elos(
        self,
        game_id: int,
        home_team_id: int,
        away_team_id: int,
        home_score: int,
        away_score: int
    ):
        """Update ELO ratings for both teams and record history."""
        # Get current ELO ratings
        home_elo = self.db.get_team_elo(home_team_id)
        away_elo = self.db.get_team_elo(away_team_id)

        # Calculate new ratings
        new_home_elo, new_away_elo = update_elo_ratings(
            home_elo, away_elo, home_score, away_score
        )

        # Update database
        self.db.upsert_team_elo(home_team_id, new_home_elo)
        self.db.upsert_team_elo(away_team_id, new_away_elo)

        # Record history (idempotent)
        self.db.upsert_elo_history(game_id, home_team_id, home_elo, new_home_elo)
        self.db.upsert_elo_history(game_id, away_team_id, away_elo, new_away_elo)

        # Log changes
        home_delta = new_home_elo - home_elo
        away_delta = new_away_elo - away_elo

        print(f"    📊 ELO Updates:")
        print(f"       Home: {home_elo:.1f} → {new_home_elo:.1f} ({home_delta:+.1f})")
        print(f"       Away: {away_elo:.1f} → {new_away_elo:.1f} ({away_delta:+.1f})")

    def process_results_for_league(
        self,
        league: str,
        days_back: int = 2
    ) -> Dict:
        """
        Process all results for a league.

        Returns:
            Dict with counts and stats
        """
        print(f"\n[Settlement] Processing {league.upper()} results...")

        # Fetch results from API
        try:
            results = fetch_results(league, days_from=days_back)
        except Exception as e:
            print(f"[Settlement] Error fetching results: {e}")
            return {'games_updated': 0, 'bets_settled': 0, 'avg_clv': 0.0}

        if not results:
            print(f"[Settlement] No completed games found")
            return {'games_updated': 0, 'bets_settled': 0, 'avg_clv': 0.0}

        print(f"[Settlement] Found {len(results)} completed games")

        games_updated = 0
        total_bets_settled = 0
        total_wins = 0
        total_losses = 0
        total_pushes = 0
        cumulative_clv = 0.0

        for result in results:
            try:
                # Find game in database
                game = self.find_game_by_teams_and_date(
                    league=result['league'],
                    home_team=result['home_team'],
                    away_team=result['away_team'],
                    game_date=result['game_time']
                )

                if not game:
                    print(f"  ⚠️  Game not found: {result['home_team']} vs {result['away_team']}")
                    continue

                print(f"\n  📊 {result['home_team']} {result['final_home']} - "
                      f"{result['final_away']} {result['away_team']}")

                # Begin transaction-like processing
                try:
                    # Update game with scores
                    self.update_game_with_results(
                        game['game_id'],
                        result['final_home'],
                        result['final_away']
                    )
                    games_updated += 1

                    # Update team ELO ratings
                    self.update_team_elos(
                        game['game_id'],
                        game['home_team_id'],
                        game['away_team_id'],
                        result['final_home'],
                        result['final_away']
                    )

                    # Settle bets
                    bet_stats = self.settle_bets_for_game(
                        game['game_id'],
                        result['final_home'],
                        result['final_away']
                    )

                    total_bets_settled += bet_stats['settled']
                    total_wins += bet_stats['wins']
                    total_losses += bet_stats['losses']
                    total_pushes += bet_stats['pushes']
                    cumulative_clv += bet_stats['total_clv']

                    if bet_stats['settled'] > 0:
                        avg_clv_this_game = bet_stats['total_clv'] / bet_stats['settled']
                        print(f"    💰 Settled {bet_stats['settled']} bet(s): "
                              f"{bet_stats['wins']}W-{bet_stats['losses']}L-{bet_stats['pushes']}P, "
                              f"Avg CLV: {avg_clv_this_game:.2f}%")

                except Exception as game_error:
                    print(f"  ❌ Error processing game settlement: {game_error}")
                    continue

            except Exception as e:
                print(f"  ❌ Error processing result: {e}")
                continue

        avg_clv = cumulative_clv / total_bets_settled if total_bets_settled > 0 else 0.0

        return {
            'games_updated': games_updated,
            'bets_settled': total_bets_settled,
            'wins': total_wins,
            'losses': total_losses,
            'pushes': total_pushes,
            'avg_clv': avg_clv
        }


def main():
    parser = argparse.ArgumentParser(description='Settle bet results with ELO updates (v2)')
    parser.add_argument('--leagues', type=str, help='Comma-separated leagues (default: from LEAGUES env)')
    parser.add_argument('--days', type=int, help='Days to look back for results (default: SETTLEMENT_LOOKBACK_DAYS or 2)')

    args = parser.parse_args()

    # Check environment
    check_env_vars()

    # Get leagues
    leagues_str = args.leagues or os.getenv('LEAGUES', 'nfl')
    leagues = [l.strip() for l in leagues_str.split(',')]

    # Get lookback days
    days_back = args.days or int(os.getenv('SETTLEMENT_LOOKBACK_DAYS', '2'))

    print(f"[Settlement] Starting settlement for leagues: {', '.join(leagues)}")
    print(f"[Settlement] Looking back {days_back} day(s)")
    print(f"[Settlement] ELO Settings: K={K_FACTOR}, Home Advantage={HOME_ADVANTAGE}")

    # Initialize processor
    processor = SettlementProcessor()

    # Check for core tables before proceeding
    print(f"\n[Settlement] Checking database schema...")
    all_exist, missing = processor.db.check_core_tables(['games', 'bets', 'team_elos', 'elo_history'])

    if not all_exist:
        print(f"[ERROR] Required database tables are missing: {', '.join(missing)}")
        print(f"[ERROR] Run migrations to create tables:")
        print(f"[ERROR]   make migrate")
        sys.exit(1)

    print(f"[Settlement] ✓ Database schema verified")

    # Process each league
    total_games = 0
    total_bets = 0
    total_wins = 0
    total_losses = 0
    total_pushes = 0
    total_clv = 0.0

    for league in leagues:
        result = processor.process_results_for_league(league, days_back)
        total_games += result['games_updated']
        total_bets += result['bets_settled']
        total_wins += result['wins']
        total_losses += result['losses']
        total_pushes += result['pushes']

        if result['bets_settled'] > 0:
            total_clv += result['avg_clv'] * result['bets_settled']

    avg_clv = total_clv / total_bets if total_bets > 0 else 0.0

    # Summary
    print(f"\n[Settlement] ===== SUMMARY =====")
    print(f"[Settlement] Leagues processed: {len(leagues)}")
    print(f"[Settlement] Games updated: {total_games}")
    print(f"[Settlement] Bets settled: {total_bets}")
    if total_bets > 0:
        print(f"[Settlement] Record: {total_wins}W-{total_losses}L-{total_pushes}P")
        print(f"[Settlement] Average CLV: {avg_clv:.2f}%")
    print(f"[Settlement] Status: {'SUCCESS' if total_games > 0 or total_bets > 0 else 'NO DATA'}")


if __name__ == '__main__':
    main()
