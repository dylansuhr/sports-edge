#!/usr/bin/env python3
"""
Signal Generation Script

Combines fair-odds models with market odds to identify +EV betting opportunities.
Applies vig removal, calculates edge%, and sizes bets using fractional Kelly.

Usage:
    python ops/scripts/generate_signals.py --sport nfl --min-edge 3.0
"""

import argparse
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List
import json

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'packages'))

from shared.shared.odds_math import (
    implied_probability,
    remove_vig_multiplicative,
    calculate_edge,
    recommended_stake,
    american_to_decimal
)

# Placeholder for database connection
DATABASE_URL = os.getenv('DATABASE_URL')


class SignalGenerator:
    """Generate betting signals from fair odds and market odds."""

    def __init__(
        self,
        min_edge_pct: float = 3.0,
        kelly_fraction: float = 0.25,
        max_stake_pct: float = 0.01,
        bankroll: float = 1000.0
    ):
        """
        Initialize signal generator.

        Args:
            min_edge_pct: Minimum edge % to generate signal (default 3%)
            kelly_fraction: Fractional Kelly to use (default 0.25 = quarter-Kelly)
            max_stake_pct: Max stake as % of bankroll (default 1%)
            bankroll: Current bankroll in dollars
        """
        self.min_edge_pct = min_edge_pct
        self.kelly_fraction = kelly_fraction
        self.max_stake_pct = max_stake_pct
        self.bankroll = bankroll

    def generate_signal(
        self,
        game_id: int,
        market_id: int,
        sportsbook: str,
        odds_american: int,
        fair_prob: float,
        line_value: float = None,
        player_id: int = None,
        metadata: Dict = None
    ) -> Dict:
        """
        Generate a betting signal if edge meets threshold.

        Args:
            game_id: Game ID
            market_id: Market ID
            sportsbook: Sportsbook name
            odds_american: Market odds (American format)
            fair_prob: Model's fair probability
            line_value: Line value (for spreads/totals)
            player_id: Player ID (for props)
            metadata: Additional metadata

        Returns:
            Signal dict or None if below threshold
        """
        # Calculate implied probability from market odds
        implied_prob = implied_probability(odds_american)

        # Calculate edge
        edge_pct = calculate_edge(fair_prob, implied_prob)

        # Skip if below threshold
        if edge_pct < self.min_edge_pct:
            return None

        # Calculate recommended stake
        stake = recommended_stake(
            fair_prob=fair_prob,
            american_odds=odds_american,
            bankroll=self.bankroll,
            fraction=self.kelly_fraction,
            max_stake_pct=self.max_stake_pct
        )

        # Determine confidence level
        if edge_pct >= 5.0:
            confidence = 'high'
        elif edge_pct >= 3.5:
            confidence = 'medium'
        else:
            confidence = 'low'

        # Build signal
        signal = {
            'game_id': game_id,
            'player_id': player_id,
            'market_id': market_id,
            'sportsbook': sportsbook,
            'line_value': line_value,
            'odds_american': odds_american,
            'fair_probability': round(fair_prob, 4),
            'implied_probability': round(implied_prob, 4),
            'edge_percent': round(edge_pct, 2),
            'recommended_stake_pct': round(stake / self.bankroll * 100, 2),
            'recommended_stake_dollars': round(stake, 2),
            'confidence_level': confidence,
            'model_version': 'baseline_v0.1',
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'metadata': metadata or {}
        }

        return signal

    def compare_lines_and_generate_signals(
        self,
        game_id: int,
        market_id: int,
        fair_prob: float,
        market_lines: List[Dict],
        line_value: float = None,
        player_id: int = None
    ) -> List[Dict]:
        """
        Compare lines across multiple sportsbooks and generate signals.

        Args:
            game_id: Game ID
            market_id: Market ID
            fair_prob: Model's fair probability
            market_lines: List of dicts with 'sportsbook' and 'odds_american'
            line_value: Line value (for spreads/totals)
            player_id: Player ID (for props)

        Returns:
            List of signals (may be empty)
        """
        signals = []

        for line in market_lines:
            signal = self.generate_signal(
                game_id=game_id,
                market_id=market_id,
                sportsbook=line['sportsbook'],
                odds_american=line['odds_american'],
                fair_prob=fair_prob,
                line_value=line_value,
                player_id=player_id
            )

            if signal:
                signals.append(signal)

        # Sort by edge (best first)
        signals.sort(key=lambda s: s['edge_percent'], reverse=True)

        return signals

    def apply_vig_removal_to_two_way_market(
        self,
        line_a_odds: int,
        line_b_odds: int
    ) -> Dict:
        """
        Remove vig from a two-way market (e.g., over/under, spread).

        Args:
            line_a_odds: Odds for outcome A (American)
            line_b_odds: Odds for outcome B (American)

        Returns:
            Dict with fair_prob_a, fair_prob_b
        """
        prob_a = implied_probability(line_a_odds)
        prob_b = implied_probability(line_b_odds)

        fair_prob_a, fair_prob_b = remove_vig_multiplicative(prob_a, prob_b)

        return {
            'fair_prob_a': fair_prob_a,
            'fair_prob_b': fair_prob_b,
            'vig_pct': round((prob_a + prob_b - 1.0) * 100, 2)
        }


def load_latest_odds_from_db(sport: str = 'nfl') -> List[Dict]:
    """
    Load latest odds snapshots from database.

    Returns:
        List of odds snapshots
    """
    # TODO: Implement database query
    # For now, return sample data
    print(f"[DB] Loading latest {sport} odds...")

    # Placeholder sample data
    sample_odds = [
        {
            'game_id': 1,
            'market_id': 1,  # spread
            'sportsbook': 'draftkings',
            'line_value': -3.5,
            'odds_american': -110
        },
        {
            'game_id': 1,
            'market_id': 1,  # spread
            'sportsbook': 'caesars',
            'line_value': -3.5,
            'odds_american': -105
        },
        {
            'game_id': 1,
            'market_id': 2,  # total
            'sportsbook': 'draftkings',
            'line_value': 45.5,
            'odds_american': -110
        }
    ]

    return sample_odds


def load_fair_probabilities_from_models(sport: str = 'nfl') -> Dict:
    """
    Load fair probabilities from models.

    Returns:
        Dict mapping (game_id, market_id) -> fair_prob
    """
    # TODO: Load from model predictions
    print(f"[Models] Loading {sport} model predictions...")

    # Placeholder: assume we have a model that estimates 60% win prob for favorite
    fair_probs = {
        (1, 1): 0.60,  # Game 1, spread market
        (1, 2): 0.52,  # Game 1, total market
    }

    return fair_probs


def save_signals_to_db(signals: List[Dict]):
    """Save signals to database."""
    # TODO: Implement database insert
    print(f"\n[DB] Would save {len(signals)} signals")

    for signal in signals:
        print(f"\n[Signal] {signal['sportsbook']} | "
              f"Edge: {signal['edge_percent']}% | "
              f"Stake: ${signal['recommended_stake_dollars']}")
        print(f"  Fair: {signal['fair_probability']:.3f} | "
              f"Implied: {signal['implied_probability']:.3f} | "
              f"Odds: {signal['odds_american']:+d}")


def send_slack_notification(signals: List[Dict], webhook_url: str = None):
    """Send Slack notification for high-edge signals."""
    if not webhook_url:
        webhook_url = os.getenv('SLACK_WEBHOOK_URL')

    if not webhook_url:
        print("[Slack] No webhook configured, skipping notification")
        return

    # Filter for high-value signals
    high_edge_signals = [s for s in signals if s['edge_percent'] >= 3.0]

    if not high_edge_signals:
        return

    # Build message
    message = f"🎯 *{len(high_edge_signals)} New Betting Signals* (Edge ≥ 3%)\n\n"

    for signal in high_edge_signals[:5]:  # Show top 5
        message += (
            f"• *{signal['sportsbook']}* | "
            f"Edge: *{signal['edge_percent']}%* | "
            f"Stake: ${signal['recommended_stake_dollars']}\n"
            f"  Fair: {signal['fair_probability']:.1%} | "
            f"Odds: {signal['odds_american']:+d}\n\n"
        )

    # TODO: Send to Slack
    print(f"\n[Slack] Would send notification:\n{message}")


def main():
    parser = argparse.ArgumentParser(description='Generate betting signals')
    parser.add_argument('--sport', type=str, default='nfl', help='Sport to analyze')
    parser.add_argument('--min-edge', type=float, default=3.0, help='Minimum edge % threshold')
    parser.add_argument('--bankroll', type=float, default=1000.0, help='Current bankroll')
    parser.add_argument('--kelly-fraction', type=float, default=0.25, help='Kelly fraction (0.25 = quarter-Kelly)')

    args = parser.parse_args()

    print(f"[SignalGen] Generating {args.sport.upper()} signals (min edge: {args.min_edge}%)")

    # Initialize generator
    generator = SignalGenerator(
        min_edge_pct=args.min_edge,
        kelly_fraction=args.kelly_fraction,
        bankroll=args.bankroll
    )

    # Load odds and model predictions
    market_odds = load_latest_odds_from_db(sport=args.sport)
    fair_probs = load_fair_probabilities_from_models(sport=args.sport)

    # Generate signals
    all_signals = []

    for odds_snapshot in market_odds:
        game_id = odds_snapshot['game_id']
        market_id = odds_snapshot['market_id']
        key = (game_id, market_id)

        # Get fair probability for this market
        fair_prob = fair_probs.get(key)

        if fair_prob is None:
            continue  # Skip if no model prediction

        # Generate signal
        signal = generator.generate_signal(
            game_id=game_id,
            market_id=market_id,
            sportsbook=odds_snapshot['sportsbook'],
            odds_american=odds_snapshot['odds_american'],
            fair_prob=fair_prob,
            line_value=odds_snapshot.get('line_value')
        )

        if signal:
            all_signals.append(signal)

    # Save signals
    if all_signals:
        save_signals_to_db(all_signals)
        send_slack_notification(all_signals)
        print(f"\n[SUCCESS] Generated {len(all_signals)} signals")
    else:
        print("\n[INFO] No signals above threshold")


if __name__ == '__main__':
    main()
