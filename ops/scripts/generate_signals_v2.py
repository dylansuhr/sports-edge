#!/usr/bin/env python3
"""
Signal Generation Script (v2 - API-Driven)

Reads latest odds from database, calculates fair probabilities using models,
identifies +EV opportunities, and writes signals to database.

Usage:
    python ops/scripts/generate_signals_v2.py --sport nfl
    python ops/scripts/generate_signals_v2.py --leagues nfl,nba
"""

import argparse
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import requests
from dotenv import load_dotenv

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'packages'))

from shared.shared.odds_math import (
    implied_probability,
    remove_vig_multiplicative,
    calculate_edge,
    recommended_stake,
    american_to_decimal
)
from shared.shared.db import get_db
from models.models.features import NFLFeatureGenerator
from models.models.prop_models import NFLGameLineModel, create_baseline_fair_odds

# Load environment
load_dotenv()


def check_env_vars():
    """Validate required environment variables."""
    required = ['DATABASE_URL']
    missing = [var for var in required if not os.getenv(var)]

    if missing:
        print(f"[ERROR] Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)


def get_env_config():
    """Load configuration from environment variables."""
    return {
        'edge_sides': float(os.getenv('EDGE_SIDES', '0.02')),  # 2%
        'edge_props': float(os.getenv('EDGE_PROPS', '0.03')),  # 3%
        'kelly_fraction': float(os.getenv('KELLY_FRACTION', '0.25')),  # ¼-Kelly
        'max_stake_pct': float(os.getenv('MAX_STAKE_PCT', '0.01')),  # 1%
        'bankroll': float(os.getenv('BANKROLL', '1000.0')),
        'slack_webhook': os.getenv('SLACK_WEBHOOK_URL'),
        'model_version': 'v0.2-api-driven'
    }


class SignalGeneratorV2:
    """Generate betting signals with database integration."""

    def __init__(self, config: Dict):
        self.config = config
        self.db = get_db()
        self.feature_gen = NFLFeatureGenerator()
        self.game_model = NFLGameLineModel()
        self.team_elos = {}  # Cache of team ELO ratings

    def load_upcoming_games(self, league: str, hours_ahead: int = 48) -> List[Dict]:
        """
        Load upcoming games from database.

        Args:
            league: League to filter (nfl, nba, nhl)
            hours_ahead: How many hours ahead to look for games

        Returns:
            List of game dicts
        """
        now = datetime.now(timezone.utc)
        cutoff_time = now + timedelta(hours=hours_ahead)

        print(f"[SignalGen] Looking for games between:")
        print(f"[SignalGen]   NOW:    {now.isoformat()}")
        print(f"[SignalGen]   CUTOFF: {cutoff_time.isoformat()} ({hours_ahead}h ahead)")

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
                AND g.scheduled_at > NOW()
                AND g.scheduled_at <= NOW() + INTERVAL '%s hours'
            ORDER BY g.scheduled_at ASC
        """

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (league, hours_ahead))
                columns = [desc[0] for desc in cur.description]
                games = [dict(zip(columns, row)) for row in cur.fetchall()]

        print(f"[SignalGen] Found {len(games)} upcoming {league.upper()} games")

        # Log first 3 game times if any exist
        if games:
            print(f"[SignalGen] Earliest games:")
            for i, game in enumerate(games[:3]):
                print(f"[SignalGen]   {i+1}. {game['home_team']} vs {game['away_team']} at {game['scheduled_at'].isoformat()}")

        return games

    def load_latest_odds_for_game(self, game_id: int) -> List[Dict]:
        """
        Load latest odds snapshots for a game.

        Returns most recent snapshot per (market, sportsbook) combination.
        """
        sql = """
            WITH latest_odds AS (
                SELECT
                    o.game_id,
                    o.market_id,
                    o.sportsbook,
                    o.selection,
                    o.odds_american,
                    o.odds_decimal,
                    o.implied_probability,
                    o.line_value,
                    o.fetched_at,
                    m.name as market_name,
                    m.category as market_category,
                    ROW_NUMBER() OVER (
                        PARTITION BY o.market_id, o.sportsbook, o.selection
                        ORDER BY o.fetched_at DESC
                    ) as rn
                FROM odds_snapshots o
                JOIN markets m ON o.market_id = m.id
                WHERE o.game_id = %s
            )
            SELECT
                game_id,
                market_id,
                market_name,
                market_category,
                sportsbook,
                selection,
                odds_american,
                odds_decimal,
                implied_probability,
                line_value,
                fetched_at
            FROM latest_odds
            WHERE rn = 1
            ORDER BY market_id, sportsbook
        """

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (game_id,))
                columns = [desc[0] for desc in cur.description]
                odds = [dict(zip(columns, row)) for row in cur.fetchall()]

        return odds

    def load_team_elos(self, league: str):
        """Load ELO ratings for all teams in a league."""
        self.team_elos = self.db.get_all_team_elos(sport=league)
        print(f"[SignalGen] Loaded {len(self.team_elos)} team ELO ratings")

    def get_team_games_played(self, team_id: int, sport: str) -> int:
        """Get number of games a team has played (for sample size filtering)."""
        sql = """
            SELECT COUNT(*)
            FROM games
            WHERE (home_team_id = %s OR away_team_id = %s)
                AND sport = %s
                AND status IN ('final', 'closed')
        """

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (team_id, team_id, sport))
                count = cur.fetchone()[0]
                return count

    def _group_odds_for_vig_removal(self, odds_snapshots: List[Dict]) -> Dict:
        """
        Group odds by market/sportsbook for vig removal on two-way markets.

        Returns a dict: {(market_id, sportsbook, line_value): {selection: implied_prob}}
        This allows us to apply vig removal to paired odds (e.g., both sides of a spread).
        """
        grouped = {}

        for odds in odds_snapshots:
            market_id = odds['market_id']
            market_name = odds['market_name']
            sportsbook = odds['sportsbook']
            selection = odds.get('selection')
            line_value = odds.get('line_value')

            if not selection:
                continue

            # Convert line_value to float for grouping
            line_key = float(line_value) if line_value is not None else None

            # Group key: (market_id, sportsbook, line_value)
            # Two-way markets should have matching line values for paired odds
            key = (market_id, sportsbook, line_key, market_name)

            if key not in grouped:
                grouped[key] = {}

            grouped[key][selection] = float(odds['implied_probability'])

        return grouped

    def _get_devigged_probability(
        self,
        odds_by_market: Dict,
        market_id: int,
        sportsbook: str,
        line_value: Optional[float],
        market_name: str,
        selection: str,
        raw_implied_prob: float
    ) -> float:
        """
        Get vig-removed implied probability for a selection, falling back to raw if vig removal not possible.

        Args:
            odds_by_market: Grouped odds for vig removal
            market_id: Market ID
            sportsbook: Sportsbook name
            line_value: Line value (for spreads/totals)
            market_name: Market type
            selection: Selection name
            raw_implied_prob: Raw implied probability from odds

        Returns:
            Vig-removed probability if available, otherwise raw probability
        """
        # Build lookup key
        line_key = float(line_value) if line_value is not None else None
        key = (market_id, sportsbook, line_key, market_name)

        # Check if we have paired odds for vig removal
        if key not in odds_by_market:
            return raw_implied_prob

        market_selections = odds_by_market[key]

        # Only apply vig removal to two-way markets with both selections
        if len(market_selections) != 2:
            return raw_implied_prob

        # Get both probabilities
        probs = list(market_selections.values())
        selections = list(market_selections.keys())

        if len(probs) != 2:
            return raw_implied_prob

        # Apply multiplicative vig removal
        fair_prob_a, fair_prob_b = remove_vig_multiplicative(probs[0], probs[1])

        # Calculate vig for logging
        total_prob = probs[0] + probs[1]
        vig_pct = (total_prob - 1.0) * 100

        # Return the probability for the current selection
        if selections[0] == selection:
            devigged_prob = fair_prob_a
        elif selections[1] == selection:
            devigged_prob = fair_prob_b
        else:
            return raw_implied_prob

        # Log vig removal (only for first instance to avoid spam)
        if abs(devigged_prob - raw_implied_prob) > 0.001:  # Only log if significant difference
            # Silently apply - logging happens at signal level
            pass

        return devigged_prob

    def calculate_expiry_time(self, game_scheduled_at: datetime, sport: str) -> datetime:
        """
        Calculate when a signal should expire based on sport-specific risk factors.

        Sport-specific expiry windows (before game time):
        - NFL: 48 hours (Wed/Fri injury reports create volatility)
        - NBA: 24 hours (daily lineup changes, load management)
        - NHL: 36 hours (goalie announcements, but more stable)

        Args:
            game_scheduled_at: When the game starts
            sport: Sport type (nfl, nba, nhl)

        Returns:
            Expiry datetime (signal becomes stale)
        """
        sport_lower = sport.lower()

        if sport_lower == 'nfl':
            hours_before = 48  # Expire 2 days before game
        elif sport_lower == 'nba':
            hours_before = 24  # Expire 1 day before game
        else:  # nhl and others
            hours_before = 36  # Expire 1.5 days before game

        candidate = game_scheduled_at - timedelta(hours=hours_before)
        now_utc = datetime.now(timezone.utc)

        # Never expire signals in the past; keep at least a small buffer before the game.
        minimum_expiry = now_utc + timedelta(minutes=5)
        if candidate < minimum_expiry:
            candidate = minimum_expiry

        # Do not keep signals alive past the scheduled start.
        return min(candidate, game_scheduled_at)

    def calculate_fair_probability(
        self,
        game: Dict,
        market_name: str,
        selection: str,
        line_value: Optional[float] = None
    ) -> Optional[float]:
        """
        Calculate fair probability for a specific selection using ELO-based models.

        Args:
            game: Game dict with team info
            market_name: Type of market (moneyline, spread, total)
            selection: Which side (team name, "Over", "Under")
            line_value: Line value for spread/total markets

        Returns:
            Fair probability (0-1) for the SELECTION winning, or None if cannot calculate
        """
        try:
            # Get team ELO ratings (default to 1500 if not found)
            home_elo = self.team_elos.get(game['home_team_id'], 1500.0)
            away_elo = self.team_elos.get(game['away_team_id'], 1500.0)

            # Apply home field advantage
            home_elo_adj = home_elo + self.feature_gen.home_advantage
            elo_diff = home_elo_adj - away_elo

            if market_name == 'moneyline':
                # ELO-based win probability for HOME team
                p_home = self.feature_gen.expected_score(home_elo_adj, away_elo)
                p_away = 1 - p_home

                # Return probability for whichever team is in the selection
                if game['home_team'] in selection:
                    return p_home
                elif game['away_team'] in selection:
                    return p_away
                else:
                    print(f"[Model] ⚠️  Cannot match selection '{selection}' to home/away team")
                    return None

            elif market_name == 'spread':
                # Spread model requires line value
                if line_value is None:
                    return None

                # Convert ELO diff to implied spread: 25 ELO points ≈ 1 point spread
                implied_spread = elo_diff / 25.0

                # Determine if selection is for home or away team
                # The selection contains the team name, so check which one
                is_home = game['home_team'] in selection
                is_away = game['away_team'] in selection

                if not (is_home or is_away):
                    print(f"[Model] ⚠️  Cannot match spread selection '{selection}' to home/away")
                    return None

                # For home team: P(home_score - away_score > line)
                # For away team: P(away_score - home_score > line) = P(home_score - away_score < -line)
                from scipy import stats
                if is_home:
                    # Home team covering: actual_spread > line_value
                    cover_margin = implied_spread - line_value
                    fair_prob = float(stats.norm.cdf(cover_margin, loc=0, scale=14))
                else:
                    # Away team covering: actual_spread < -line_value
                    # Which is equivalent to: -actual_spread > line_value
                    cover_margin = -implied_spread - line_value
                    fair_prob = float(stats.norm.cdf(cover_margin, loc=0, scale=14))

                return fair_prob

            elif market_name == 'total':
                # Total model requires line value
                if line_value is None:
                    return None

                # Use team-specific total calculation
                home_points, away_points, expected_total = self.feature_gen.calculate_expected_total(
                    game['home_team_id'],
                    game['away_team_id']
                )

                # Standard deviation based on sport
                if game['sport'] == 'nfl':
                    league_std = 10.0  # NFL has higher variance
                elif game['sport'] == 'nba':
                    league_std = 12.0  # NBA has moderate variance
                else:  # nhl
                    league_std = 2.5   # NHL has lower variance (6 goals avg)

                # Determine if selection is Over or Under
                from scipy import stats
                if 'Over' in selection:
                    # P(total > line)
                    over_prob = float(1 - stats.norm.cdf(line_value, loc=expected_total, scale=league_std))
                    return over_prob
                elif 'Under' in selection:
                    # P(total < line)
                    under_prob = float(stats.norm.cdf(line_value, loc=expected_total, scale=league_std))
                    return under_prob
                else:
                    print(f"[Model] ⚠️  Cannot match total selection '{selection}' to Over/Under")
                    return None

            else:
                return None

        except Exception as e:
            print(f"[Model] Error calculating fair prob: {e}")
            return None

    def generate_signals_for_game(self, game: Dict) -> List[Dict]:
        """Generate signals for a single game."""
        game_id = game['game_id']
        signals = []

        # Load latest odds
        odds_snapshots = self.load_latest_odds_for_game(game_id)

        if not odds_snapshots:
            print(f"[SignalGen]   ⚠️  No odds snapshots found for game {game_id}")
            return signals

        print(f"[SignalGen]   Found {len(odds_snapshots)} odds snapshots")

        # Get team ELOs for logging
        home_elo = self.team_elos.get(game['home_team_id'], 1500.0)
        away_elo = self.team_elos.get(game['away_team_id'], 1500.0)
        print(f"[SignalGen]   Team ELOs: {game['home_team']} ({home_elo:.0f}) vs {game['away_team']} ({away_elo:.0f})")

        # Check sample size (minimum 3 games for reliable signals)
        home_games_played = self.get_team_games_played(game['home_team_id'], game['sport'])
        away_games_played = self.get_team_games_played(game['away_team_id'], game['sport'])
        min_games = 3

        insufficient_sample = home_games_played < min_games or away_games_played < min_games

        if insufficient_sample:
            print(f"[SignalGen]   ⚠️  Insufficient sample size: Home={home_games_played}, Away={away_games_played} (min={min_games})")
            print(f"[SignalGen]   Reducing confidence for early-season signals")

        # Group odds by market/sportsbook for vig removal
        odds_by_market = self._group_odds_for_vig_removal(odds_snapshots)

        # Group by market for logging
        markets_seen = set()

        # Process each individual odds snapshot (each represents a specific selection)
        for odds in odds_snapshots:
            market_id = odds['market_id']
            market_name = odds['market_name']
            selection = odds.get('selection')
            sportsbook = odds['sportsbook']

            # Skip if no selection (old data)
            if not selection:
                continue

            # Log market if first time seeing it
            market_key = (market_id, market_name)
            if market_key not in markets_seen:
                markets_seen.add(market_key)
                print(f"[SignalGen]   Checking market: {market_name}")

            # Convert Decimal to float if needed
            line_value = odds.get('line_value')
            if line_value is not None:
                line_value = float(line_value)

            # Calculate fair probability FOR THIS SPECIFIC SELECTION
            fair_prob = self.calculate_fair_probability(game, market_name, selection, line_value)

            if fair_prob is None:
                # Silently skip - warnings already printed in calculate_fair_probability
                continue

            # Determine edge threshold based on market type
            if market_name in ['spread', 'total', 'moneyline']:
                min_edge = self.config['edge_sides'] * 100  # Convert to %
            else:
                min_edge = self.config['edge_props'] * 100

            # Get implied probability (with vig removed if possible)
            implied_prob_raw = float(odds['implied_probability'])
            implied_prob = self._get_devigged_probability(
                odds_by_market,
                market_id,
                sportsbook,
                line_value,
                market_name,
                selection,
                implied_prob_raw
            )

            # Calculate edge for this selection
            edge_pct = calculate_edge(fair_prob, implied_prob)

            # Skip if edge below threshold
            if edge_pct < min_edge:
                continue

            # Cap edge at 20% to catch outliers
            if edge_pct > 20.0:
                print(f"[SignalGen]     ⚠️  Skipping extreme edge {edge_pct:.1f}% for {selection} @ {sportsbook}")
                continue

            # Calculate stake
            stake_dollars = recommended_stake(
                fair_prob=fair_prob,
                american_odds=odds['odds_american'],
                bankroll=self.config['bankroll'],
                fraction=self.config['kelly_fraction'],
                max_stake_pct=self.config['max_stake_pct']
            )

            stake_pct = (stake_dollars / self.config['bankroll']) * 100

            # Determine confidence (downgrade if insufficient sample)
            if edge_pct >= 5.0:
                confidence = 'high'
            elif edge_pct >= 3.5:
                confidence = 'medium'
            else:
                confidence = 'low'

            # Downgrade confidence for early-season games (< 3 games played)
            if insufficient_sample:
                if confidence == 'high':
                    confidence = 'medium'
                elif confidence == 'medium':
                    confidence = 'low'
                # 'low' stays 'low'

            # Calculate sport-specific expiry time
            expiry_time = self.calculate_expiry_time(game['scheduled_at'], game['sport'])

            # Create signal dict
            signal = {
                'game_id': game_id,
                'market_id': market_id,
                'sportsbook': sportsbook,
                'odds_american': odds['odds_american'],
                'line_value': line_value,
                'fair_probability': round(fair_prob, 4),
                'implied_probability': round(implied_prob, 4),  # Vig-removed
                'raw_implied_probability': round(implied_prob_raw, 4),  # Original with vig
                'edge_percent': round(edge_pct, 2),
                'recommended_stake_pct': round(stake_pct, 2),
                'confidence_level': confidence,
                'expires_at': expiry_time,
                'kelly_fraction': self.config['kelly_fraction']
            }

            signals.append(signal)

            # Log signal creation
            print(f"[SignalGen]     ✅ Signal: {selection} @ {sportsbook} | Edge: {edge_pct:.2f}% | Fair: {fair_prob:.3f} vs Implied: {implied_prob:.3f}")

        return signals

    def save_signal_to_db(self, signal: Dict) -> int:
        """Save a signal to the database."""
        return self.db.insert_signal(
            game_id=signal['game_id'],
            market_id=signal['market_id'],
            sportsbook=signal['sportsbook'],
            odds_american=signal['odds_american'],
            fair_probability=signal['fair_probability'],
            implied_probability=signal['implied_probability'],
            raw_implied_probability=signal.get('raw_implied_probability'),
            edge_percent=signal['edge_percent'],
            kelly_fraction=signal['kelly_fraction'],
            recommended_stake_pct=signal['recommended_stake_pct'],
            confidence_level=signal['confidence_level'],
            model_version=self.config['model_version'],
            expires_at=signal['expires_at'],
            line_value=signal.get('line_value')
        )

    def send_slack_notification(self, signals: List[Dict]):
        """Send Slack webhook for high-edge signals."""
        webhook_url = self.config['slack_webhook']

        if not webhook_url:
            print("[Slack] No webhook configured, skipping notification")
            return

        # Filter for high-value signals (≥3%)
        high_edge = [s for s in signals if s['edge_percent'] >= 3.0]

        if not high_edge:
            return

        # Build message
        message = f"🎯 *{len(high_edge)} New Betting Signals* (Edge ≥ 3%)\n\n"

        for signal in high_edge[:5]:  # Top 5
            message += (
                f"• *{signal['sportsbook']}* | "
                f"Edge: *{signal['edge_percent']}%* | "
                f"Stake: {signal['recommended_stake_pct']:.2f}%\n"
                f"  Fair: {signal['fair_probability']:.1%} | "
                f"Odds: {signal['odds_american']:+d}\n\n"
            )

        # Send to Slack
        try:
            response = requests.post(
                webhook_url,
                json={'text': message},
                timeout=10
            )

            if response.status_code == 200:
                print(f"[Slack] Notification sent for {len(high_edge)} signals")
            else:
                print(f"[Slack] Failed to send notification: {response.status_code}")

        except Exception as e:
            print(f"[Slack] Error sending notification: {e}")


def main():
    parser = argparse.ArgumentParser(description='Generate betting signals (v2 - API-driven)')
    parser.add_argument('--leagues', type=str, help='Comma-separated leagues (default: from LEAGUES env)')
    parser.add_argument('--hours-ahead', type=int, help='Look ahead window in hours (default: from SIGNAL_LOOKAHEAD_HOURS env or 48)')

    args = parser.parse_args()

    # Check environment
    check_env_vars()
    config = get_env_config()

    # Get leagues
    leagues_str = args.leagues or os.getenv('LEAGUES', 'nfl')
    leagues = [l.strip() for l in leagues_str.split(',')]

    # Get lookahead window (priority: CLI arg > env var > default)
    hours_ahead = args.hours_ahead or int(os.getenv('SIGNAL_LOOKAHEAD_HOURS', '48'))

    print(f"[SignalGen] Starting signal generation for: {', '.join(leagues)}")
    print(f"[SignalGen] Lookahead window: {hours_ahead} hours")
    print(f"[SignalGen] Config: Edge sides={config['edge_sides']*100}%, "
          f"Edge props={config['edge_props']*100}%, "
          f"Kelly={config['kelly_fraction']}")

    # Initialize generator
    generator = SignalGeneratorV2(config)

    # Check for core tables before proceeding
    print(f"\n[SignalGen] Checking database schema...")
    all_exist, missing = generator.db.check_core_tables(['games', 'markets', 'odds_snapshots', 'signals'])

    if not all_exist:
        print(f"[ERROR] Required database tables are missing: {', '.join(missing)}")
        print(f"[ERROR] Run migrations to create tables:")
        print(f"[ERROR]   make migrate")
        print(f"[ERROR]   OR: psql $DATABASE_URL -f infra/migrations/0001_init.sql")
        sys.exit(1)

    print(f"[SignalGen] ✓ Database schema verified")

    # Process each league
    all_signals = []

    for league in leagues:
        print(f"\n[SignalGen] Processing {league.upper()}...")

        # Load team ELO ratings for this league
        generator.load_team_elos(league)

        # Load upcoming games
        games = generator.load_upcoming_games(league, hours_ahead)

        for game in games:
            print(f"\n[SignalGen] Processing game #{game['game_id']}: {game['home_team']} vs {game['away_team']}")
            print(f"[SignalGen]   Scheduled: {game['scheduled_at'].isoformat()}")

            # Generate signals for this game
            signals = generator.generate_signals_for_game(game)

            if not signals:
                print(f"[SignalGen]   No +EV signals found for this game")

            # Save signals to database
            for signal in signals:
                try:
                    signal_id = generator.save_signal_to_db(signal)
                    signal['id'] = signal_id
                    all_signals.append(signal)

                    print(f"  ✅ Signal #{signal_id}: {signal['sportsbook']} | "
                          f"Edge {signal['edge_percent']}% | "
                          f"Stake {signal['recommended_stake_pct']:.2f}%")

                except Exception as e:
                    print(f"  ❌ Error saving signal: {e}")

    # Send Slack notification
    if all_signals:
        generator.send_slack_notification(all_signals)

    # Summary
    print(f"\n[SignalGen] ===== SUMMARY =====")
    print(f"[SignalGen] Leagues processed: {len(leagues)}")
    print(f"[SignalGen] Total signals generated: {len(all_signals)}")
    print(f"[SignalGen] Status: {'SUCCESS' if all_signals else 'NO SIGNALS'}")


if __name__ == '__main__':
    main()
