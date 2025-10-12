#!/usr/bin/env python3
"""
AI Paper Betting Agent
Autonomously selects signals and places mock bets with intelligent decision-making.

Features:
- Multi-factor confidence scoring
- Correlation risk assessment
- Kelly criterion sizing with fractional Kelly
- Bankroll management and exposure limits
- Transparent decision logging
- Strategy-based bet selection
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from packages.shared.shared.db_query import query

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PaperBettingAgent:
    """
    Intelligent agent for autonomous paper betting.

    Uses multi-factor analysis to make decisions:
    - Edge quality (CLV history if available)
    - Confidence level from signal generation
    - Bankroll management (Kelly criterion)
    - Exposure limits (per game, per day)
    - Correlation risk (multiple bets on same game)
    """

    def __init__(self, strategy_name: str = 'Conservative'):
        self.strategy = self._load_strategy(strategy_name)
        self.bankroll = self._get_current_bankroll()
        self.pending_bets = self._get_pending_bets()

        logger.info(f"Initialized agent with strategy: {strategy_name}")
        logger.info(f"Current bankroll: ${self.bankroll['balance']:.2f}")
        logger.info(f"Pending bets: {len(self.pending_bets)}")

    def _load_strategy(self, name: str) -> Dict:
        """Load betting strategy from database."""
        sql = """
            SELECT *
            FROM paper_betting_strategies
            WHERE name = %s AND enabled = true
        """
        strategies = query(sql, [name])

        if not strategies:
            logger.error(f"Strategy '{name}' not found or disabled")
            sys.exit(1)

        return strategies[0]

    def _get_current_bankroll(self) -> Dict:
        """Get current paper bankroll state."""
        sql = "SELECT * FROM paper_bankroll ORDER BY id DESC LIMIT 1"
        result = query(sql)

        if not result:
            logger.error("No paper bankroll found")
            sys.exit(1)

        return result[0]

    def _get_pending_bets(self) -> List[Dict]:
        """Get all pending paper bets."""
        sql = """
            SELECT pb.*, g.sport, g.scheduled_at
            FROM paper_bets pb
            JOIN games g ON pb.game_id = g.id
            WHERE pb.status = 'pending'
        """
        return query(sql)

    def _get_candidate_signals(self) -> List[Dict]:
        """
        Fetch active signals that meet strategy criteria.

        Only considers signals:
        - Active and not expired
        - Meet minimum edge threshold
        - Meet minimum confidence level
        - Not already bet on
        - Game starts within next 7 days
        """
        confidence_order = {'low': 1, 'medium': 2, 'high': 3}
        min_conf_value = confidence_order[self.strategy['min_confidence']]

        sql = """
            SELECT
                s.*,
                g.sport,
                g.scheduled_at,
                g.home_team_id,
                g.away_team_id,
                t_home.name as home_team,
                t_away.name as away_team,
                m.name as market_name,
                p.name as player_name,
                (
                    SELECT o2.selection
                    FROM odds_snapshots o2
                    WHERE o2.game_id = s.game_id
                      AND o2.market_id = s.market_id
                      AND o2.sportsbook = s.sportsbook
                      AND o2.odds_american = s.odds_american
                    ORDER BY o2.fetched_at DESC
                    LIMIT 1
                ) as selection
            FROM signals s
            JOIN games g ON s.game_id = g.id
            JOIN markets m ON s.market_id = m.id
            LEFT JOIN teams t_home ON g.home_team_id = t_home.id
            LEFT JOIN teams t_away ON g.away_team_id = t_away.id
            LEFT JOIN players p ON s.player_id = p.id
            WHERE s.status = 'active'
              AND s.expires_at > NOW()
              AND s.edge_percent >= %s
              AND CASE
                    WHEN s.confidence_level = 'low' THEN 1
                    WHEN s.confidence_level = 'medium' THEN 2
                    WHEN s.confidence_level = 'high' THEN 3
                  END >= %s
              AND g.scheduled_at BETWEEN NOW() AND NOW() + INTERVAL '7 days'
              AND s.id NOT IN (
                  SELECT signal_id FROM paper_bets WHERE status = 'pending'
              )
            ORDER BY s.edge_percent DESC, s.confidence_level DESC
            LIMIT 100
        """

        return query(sql, [
            float(self.strategy['min_edge']),
            min_conf_value
        ])

    def calculate_confidence_score(self, signal: Dict) -> float:
        """
        Calculate AI confidence score (0.0 - 1.0) based on multiple factors.

        Factors:
        1. Edge magnitude (higher = better)
        2. Confidence level from model (high/medium/low)
        3. CLV history if available (positive CLV = better)
        4. Time to game (more time = less confidence due to volatility)
        5. Market type (moneyline > spread > total in reliability)
        """
        score = 0.0

        # Factor 1: Edge magnitude (0-0.3 score)
        edge = float(signal['edge_percent'])
        if edge >= 10:
            score += 0.30
        elif edge >= 7:
            score += 0.25
        elif edge >= 5:
            score += 0.20
        elif edge >= 3:
            score += 0.15
        else:
            score += 0.10

        # Factor 2: Model confidence (0-0.3 score)
        conf_level = signal['confidence_level']
        if conf_level == 'high':
            score += 0.30
        elif conf_level == 'medium':
            score += 0.20
        else:  # low
            score += 0.10

        # Factor 3: CLV history (0-0.2 score)
        # Check if this sportsbook/market combo has positive CLV history
        clv_bonus = self._get_clv_bonus(signal)
        score += clv_bonus

        # Factor 4: Time to game (0-0.1 score)
        # More time = slightly lower confidence due to line movement risk
        hours_until_game = (signal['scheduled_at'] - datetime.now()).total_seconds() / 3600
        if hours_until_game <= 24:
            score += 0.05  # Last-minute sharp money already in
        elif hours_until_game <= 48:
            score += 0.08
        else:
            score += 0.10  # Early lines can move a lot

        # Factor 5: Market reliability (0-0.1 score)
        market = signal['market_name'].lower()
        if 'moneyline' in market or 'h2h' in market:
            score += 0.10  # Most liquid market
        elif 'spread' in market or 'handicap' in market:
            score += 0.08
        else:  # totals, props
            score += 0.05

        return min(1.0, score)

    def _get_clv_bonus(self, signal: Dict) -> float:
        """
        Award bonus confidence if this sportsbook/market has positive CLV history.
        """
        sql = """
            SELECT AVG(clv_percent) as avg_clv
            FROM signals
            WHERE sportsbook = %s
              AND market_id = %s
              AND clv_percent IS NOT NULL
              AND generated_at > NOW() - INTERVAL '30 days'
        """

        result = query(sql, [signal['sportsbook'], signal['market_id']])

        if result and result[0]['avg_clv']:
            avg_clv = float(result[0]['avg_clv'])
            if avg_clv > 2.0:
                return 0.20
            elif avg_clv > 1.0:
                return 0.15
            elif avg_clv > 0:
                return 0.10

        return 0.05  # Neutral if no history

    def assess_correlation_risk(self, signal: Dict) -> str:
        """
        Assess correlation risk for this bet.

        Risk levels:
        - HIGH: Multiple bets on same game
        - MEDIUM: Multiple bets on same team
        - LOW: No correlation
        """
        game_id = signal['game_id']
        home_team_id = signal['home_team_id']
        away_team_id = signal['away_team_id']

        # Check for bets on same game
        same_game_count = sum(
            1 for bet in self.pending_bets
            if bet['game_id'] == game_id
        )

        if same_game_count > 0:
            return 'high'

        # Check for bets on same teams
        same_team_count = sum(
            1 for bet in self.pending_bets
            if bet.get('home_team_id') in [home_team_id, away_team_id]
            or bet.get('away_team_id') in [home_team_id, away_team_id]
        )

        if same_team_count >= 2:
            return 'medium'

        return 'low'

    def calculate_stake(self, signal: Dict, confidence_score: float) -> Tuple[float, float]:
        """
        Calculate bet stake using Kelly criterion with fractional Kelly.

        Returns:
            (kelly_stake, actual_stake)
        """
        edge = float(signal['edge_percent']) / 100.0
        odds_american = int(signal['odds_american'])

        # Convert American odds to decimal
        if odds_american > 0:
            odds_decimal = (odds_american / 100.0) + 1
        else:
            odds_decimal = (100.0 / abs(odds_american)) + 1

        # Kelly formula: (edge / (odds - 1))
        kelly_fraction_raw = edge / (odds_decimal - 1)

        # Apply fractional Kelly from strategy
        kelly_fraction = kelly_fraction_raw * float(self.strategy['kelly_fraction'])

        # Calculate kelly stake (convert Decimal to float)
        kelly_stake = float(self.bankroll['balance']) * kelly_fraction

        # Apply confidence adjustment (reduce stake if low confidence)
        adjusted_stake = kelly_stake * confidence_score

        # Apply max stake percentage cap
        max_stake = float(self.bankroll['balance']) * (float(self.strategy['max_stake_pct']) / 100.0)
        actual_stake = min(adjusted_stake, max_stake)

        # Round to 2 decimals
        kelly_stake = round(kelly_stake, 2)
        actual_stake = round(actual_stake, 2)

        return kelly_stake, actual_stake

    def check_exposure_limits(self, signal: Dict, stake: float) -> Tuple[bool, str]:
        """
        Check if placing this bet would exceed exposure limits.

        Returns:
            (allowed, reason)
        """
        # Check game exposure
        game_id = signal['game_id']
        current_game_exposure = sum(
            float(bet['stake']) for bet in self.pending_bets
            if bet['game_id'] == game_id
        )

        total_game_exposure = current_game_exposure + stake
        max_game_exposure = float(self.bankroll['balance']) * (float(self.strategy['max_exposure_per_game']) / 100.0)

        if total_game_exposure > max_game_exposure:
            return False, f"Game exposure limit (${max_game_exposure:.2f}) would be exceeded"

        # Check daily bet limit if configured
        if self.strategy.get('max_daily_bets'):
            today_bets = sum(
                1 for bet in self.pending_bets
                if bet['placed_at'].date() == datetime.now().date()
            )

            if today_bets >= self.strategy['max_daily_bets']:
                return False, f"Daily bet limit ({self.strategy['max_daily_bets']}) reached"

        # Check total exposure
        total_pending_stake = sum(float(bet['stake']) for bet in self.pending_bets)
        if (total_pending_stake + stake) > (float(self.bankroll['balance']) * 0.3):
            return False, "Total exposure limit (30% of bankroll) would be exceeded"

        return True, "Within limits"

    def make_decision(self, signal: Dict) -> Tuple[str, str, float, Optional[float], Optional[float]]:
        """
        Make betting decision for a signal.

        Returns:
            (decision, reasoning, confidence_score, kelly_stake, actual_stake)
        """
        # Calculate confidence
        confidence_score = self.calculate_confidence_score(signal)

        # Check correlation risk
        correlation_risk = self.assess_correlation_risk(signal)

        if correlation_risk == 'high':
            reasoning = f"SKIP: High correlation risk (multiple bets on game {signal['game_id']})"
            return 'skip', reasoning, confidence_score, None, None

        # Calculate stake
        kelly_stake, actual_stake = self.calculate_stake(signal, confidence_score)

        if actual_stake < 1.0:
            reasoning = f"SKIP: Calculated stake (${actual_stake:.2f}) below %s minimum"
            return 'skip', reasoning, confidence_score, kelly_stake, None

        # Check exposure limits
        allowed, limit_reason = self.check_exposure_limits(signal, actual_stake)

        if not allowed:
            reasoning = f"SKIP: {limit_reason}"
            return 'skip', reasoning, confidence_score, kelly_stake, actual_stake

        # Decision: PLACE
        factors = [
            f"Edge: {signal['edge_percent']:.1f}%",
            f"Model confidence: {signal['confidence_level']}",
            f"AI confidence: {confidence_score:.2f}",
            f"Correlation risk: {correlation_risk}",
            f"Kelly stake: ${kelly_stake:.2f}",
            f"Actual stake: ${actual_stake:.2f} ({actual_stake/float(self.bankroll['balance'])*100:.2f}% of bankroll)"
        ]

        reasoning = f"PLACE: {' | '.join(factors)}"
        return 'place', reasoning, confidence_score, kelly_stake, actual_stake

    def place_paper_bet(self, signal: Dict, stake: float) -> int:
        """
        Place a paper bet and return bet ID.
        """
        odds_american = int(signal['odds_american'])

        # Convert to decimal odds
        if odds_american > 0:
            odds_decimal = (odds_american / 100.0) + 1
        else:
            odds_decimal = (100.0 / abs(odds_american)) + 1

        sql = """
            INSERT INTO paper_bets (
                signal_id, stake, odds_american, odds_decimal,
                game_id, market_name, selection,
                edge_percent, confidence_level
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """

        result = query(sql, [
            signal['id'],
            stake,
            odds_american,
            round(odds_decimal, 4),
            signal['game_id'],
            signal['market_name'],
            signal['selection'],
            float(signal['edge_percent']),
            signal['confidence_level']
        ])

        return result[0]['id']

    def log_decision(self, signal: Dict, decision: str, reasoning: str,
                    confidence_score: float, kelly_stake: Optional[float],
                    actual_stake: Optional[float], correlation_risk: str):
        """
        Log decision to paper_bet_decisions table for transparency.
        """
        current_exposure = sum(float(bet['stake']) for bet in self.pending_bets)
        exposure_pct = (current_exposure / float(self.bankroll['balance'])) * 100

        sql = """
            INSERT INTO paper_bet_decisions (
                signal_id, decision, reasoning, confidence_score,
                kelly_stake, actual_stake, edge_percent,
                bankroll_at_decision, exposure_pct, correlation_risk
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        query(sql, [
            signal['id'],
            decision,
            reasoning,
            confidence_score,
            kelly_stake,
            actual_stake,
            float(signal['edge_percent']),
            float(self.bankroll['balance']),
            round(exposure_pct, 2),
            correlation_risk
        ])

    def run(self, max_bets: int = 10):
        """
        Main execution loop: evaluate signals and place paper bets.

        Args:
            max_bets: Maximum number of bets to place in this run
        """
        logger.info(f"Starting paper betting agent run (max {max_bets} bets)")

        # Get candidate signals
        signals = self._get_candidate_signals()
        logger.info(f"Found {len(signals)} candidate signals")

        if not signals:
            logger.info("No candidate signals meet criteria")
            return

        bets_placed = 0
        decisions_logged = 0

        for signal in signals:
            if bets_placed >= max_bets:
                logger.info(f"Reached max bet limit ({max_bets})")
                break

            # Make decision
            decision, reasoning, confidence_score, kelly_stake, actual_stake = \
                self.make_decision(signal)

            # Assess correlation
            correlation_risk = self.assess_correlation_risk(signal)

            # Log decision
            self.log_decision(
                signal, decision, reasoning, confidence_score,
                kelly_stake, actual_stake, correlation_risk
            )
            decisions_logged += 1

            # Place bet if decision is 'place'
            if decision == 'place' and actual_stake:
                bet_id = self.place_paper_bet(signal, actual_stake)
                bets_placed += 1

                logger.info(
                    f"PLACED bet #{bet_id}: {signal['home_team']} vs {signal['away_team']} | "
                    f"{signal['market_name']} - {signal['selection']} | "
                    f"Edge: {signal['edge_percent']:.1f}% | Stake: ${actual_stake:.2f}"
                )
            else:
                logger.info(
                    f"SKIPPED: {signal['home_team']} vs {signal['away_team']} | "
                    f"{reasoning[:80]}"
                )

        logger.info(f"Run complete: {bets_placed} bets placed, {decisions_logged} decisions logged")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='AI Paper Betting Agent')
    parser.add_argument('--strategy', default='Conservative',
                       help='Strategy name (default: Conservative)')
    parser.add_argument('--max-bets', type=int, default=10,
                       help='Maximum bets to place (default: 10)')

    args = parser.parse_args()

    try:
        agent = PaperBettingAgent(strategy_name=args.strategy)
        agent.run(max_bets=args.max_bets)

    except Exception as e:
        logger.error(f"Error in paper betting agent: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
