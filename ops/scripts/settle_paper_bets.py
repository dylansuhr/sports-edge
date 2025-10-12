#!/usr/bin/env python3
"""
Paper Bet Settlement Script
Settles completed paper bets and updates bankroll with reinforcement learning signals.

Features:
- Settles paper bets when games complete
- Updates paper bankroll with P&L
- Calculates CLV for paper bets
- Generates performance metrics
- Provides feedback signals for model improvement
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
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


class PaperBetSettlement:
    """
    Settles paper bets and provides learning signals.

    Settlement process:
    1. Find paper bets for completed games
    2. Determine bet result (won/lost/push)
    3. Calculate profit/loss
    4. Update paper bankroll
    5. Calculate CLV if closing odds available
    6. Generate learning signals
    """

    def __init__(self):
        self.settled_count = 0
        self.total_profit_loss = 0.0

    def get_pending_paper_bets(self) -> List[Dict]:
        """
        Get paper bets for games that have completed.
        """
        sql = """
            SELECT
                pb.*,
                g.sport,
                g.scheduled_at,
                g.home_score,
                g.away_score,
                g.status as game_status,
                s.market_id,
                s.line_value,
                t_home.name as home_team,
                t_away.name as away_team
            FROM paper_bets pb
            JOIN games g ON pb.game_id = g.id
            JOIN signals s ON pb.signal_id = s.id
            LEFT JOIN teams t_home ON g.home_team_id = t_home.id
            LEFT JOIN teams t_away ON g.away_team_id = t_away.id
            WHERE pb.status = 'pending'
              AND g.status = 'completed'
              AND g.home_score IS NOT NULL
              AND g.away_score IS NOT NULL
        """
        return query(sql)

    def determine_bet_result(self, bet: Dict) -> str:
        """
        Determine if bet won, lost, or pushed.

        Returns: 'won', 'lost', 'push', or 'void'
        """
        market = bet['market_name'].lower()
        selection = bet['selection']
        home_score = int(bet['home_score'])
        away_score = int(bet['away_score'])

        # Moneyline / H2H
        if 'moneyline' in market or 'h2h' in market:
            if bet['home_team'] in selection:
                return 'won' if home_score > away_score else 'lost'
            else:
                return 'won' if away_score > home_score else 'lost'

        # Spread / Handicap
        elif 'spread' in market or 'handicap' in market:
            line_value = float(bet['line_value']) if bet['line_value'] else 0

            if bet['home_team'] in selection:
                # Home team with spread
                adjusted_score = home_score + line_value
                if adjusted_score > away_score:
                    return 'won'
                elif adjusted_score == away_score:
                    return 'push'
                else:
                    return 'lost'
            else:
                # Away team with spread
                adjusted_score = away_score + abs(line_value)
                if adjusted_score > home_score:
                    return 'won'
                elif adjusted_score == home_score:
                    return 'push'
                else:
                    return 'lost'

        # Totals / Over/Under
        elif 'total' in market or 'over' in market or 'under' in market:
            line_value = float(bet['line_value']) if bet['line_value'] else 0
            actual_total = home_score + away_score

            if 'over' in selection.lower():
                if actual_total > line_value:
                    return 'won'
                elif actual_total == line_value:
                    return 'push'
                else:
                    return 'lost'
            else:  # Under
                if actual_total < line_value:
                    return 'won'
                elif actual_total == line_value:
                    return 'push'
                else:
                    return 'lost'

        # Props or unknown market - need more sophisticated logic
        else:
            logger.warning(f"Unknown market type for bet {bet['id']}: {market}")
            return 'void'

    def calculate_profit_loss(self, bet: Dict, result: str) -> float:
        """
        Calculate profit or loss for the bet.
        """
        stake = float(bet['stake'])
        odds_american = int(bet['odds_american'])

        if result == 'won':
            if odds_american > 0:
                profit = stake * (odds_american / 100.0)
            else:
                profit = stake * (100.0 / abs(odds_american))
            return round(profit, 2)

        elif result == 'lost':
            return -stake

        elif result == 'push':
            return 0.0

        elif result == 'void':
            return 0.0

        return 0.0

    def get_closing_odds(self, bet: Dict) -> Optional[int]:
        """
        Get closing odds for CLV calculation.
        """
        # Look for odds snapshot within 30 minutes before game start
        sql = """
            SELECT odds_american
            FROM odds_snapshots
            WHERE game_id = %s
              AND market_id = %s
              AND sportsbook = (
                  SELECT sportsbook FROM signals WHERE id = %s
              )
              AND selection = %s
              AND fetched_at BETWEEN %s - INTERVAL '30 minutes' AND %s
            ORDER BY fetched_at DESC
            LIMIT 1
        """

        result = query(sql, [
            bet['game_id'],
            bet['market_id'],
            bet['signal_id'],
            bet['selection'],
            bet['scheduled_at']
        ])

        if result:
            return int(result[0]['odds_american'])

        return None

    def calculate_clv(self, bet_odds: int, closing_odds: int) -> float:
        """
        Calculate Closing Line Value (CLV) percentage.
        """
        # Convert to decimal odds
        def american_to_decimal(american):
            if american > 0:
                return (american / 100.0) + 1
            else:
                return (100.0 / abs(american)) + 1

        bet_decimal = american_to_decimal(bet_odds)
        closing_decimal = american_to_decimal(closing_odds)

        # CLV = (bet_odds - closing_odds) / closing_odds * 100
        clv = ((bet_decimal - closing_decimal) / closing_decimal) * 100

        return round(clv, 2)

    def settle_bet(self, bet: Dict):
        """
        Settle a single paper bet.
        """
        # Determine result
        result = self.determine_bet_result(bet)

        # Calculate P&L
        profit_loss = self.calculate_profit_loss(bet, result)

        # Get closing odds for CLV
        closing_odds = self.get_closing_odds(bet)
        clv = None
        if closing_odds:
            clv = self.calculate_clv(int(bet['odds_american']), closing_odds)

        # Update bet
        sql = """
            UPDATE paper_bets
            SET status = %s,
                result = %s,
                profit_loss = %s,
                settled_at = NOW()
            WHERE id = %s
        """

        query(sql, [result, result, profit_loss, bet['id']])

        # Update signal with CLV if available
        if clv is not None:
            sql_clv = """
                UPDATE signals
                SET clv_percent = %s
                WHERE id = %s
            """
            query(sql_clv, [clv, bet['signal_id']])

        self.settled_count += 1
        self.total_profit_loss += profit_loss

        logger.info(
            f"Settled bet #{bet['id']}: {bet['home_team']} vs {bet['away_team']} | "
            f"{bet['market_name']} - {bet['selection']} | "
            f"Result: {result} | P&L: ${profit_loss:+.2f}" +
            (f" | CLV: {clv:+.1f}%" if clv else "")
        )

    def update_bankroll(self):
        """
        Update paper bankroll with latest metrics.
        """
        sql = """
            WITH bet_stats AS (
                SELECT
                    COUNT(*) as total_bets,
                    SUM(stake) as total_staked,
                    SUM(profit_loss) as total_profit_loss,
                    COUNT(CASE WHEN result = 'won' THEN 1 END) as win_count,
                    COUNT(CASE WHEN result = 'lost' THEN 1 END) as loss_count,
                    COUNT(CASE WHEN result = 'push' THEN 1 END) as push_count,
                    AVG(edge_percent) as avg_edge
                FROM paper_bets
                WHERE status != 'pending'
            ),
            clv_stats AS (
                SELECT AVG(s.clv_percent) as avg_clv
                FROM paper_bets pb
                JOIN signals s ON pb.signal_id = s.id
                WHERE pb.status != 'pending'
                  AND s.clv_percent IS NOT NULL
            )
            SELECT
                bs.*,
                cs.avg_clv,
                (SELECT starting_balance FROM paper_bankroll LIMIT 1) as starting_balance
            FROM bet_stats bs
            CROSS JOIN clv_stats cs
        """

        result = query(sql)

        if not result or not result[0]:
            logger.warning("No bet stats available for bankroll update")
            return

        stats = result[0]

        total_bets = int(stats['total_bets']) if stats['total_bets'] else 0
        total_staked = float(stats['total_staked']) if stats['total_staked'] else 0.0
        total_profit_loss = float(stats['total_profit_loss']) if stats['total_profit_loss'] else 0.0
        win_count = int(stats['win_count']) if stats['win_count'] else 0
        loss_count = int(stats['loss_count']) if stats['loss_count'] else 0
        push_count = int(stats['push_count']) if stats['push_count'] else 0
        avg_edge = float(stats['avg_edge']) if stats['avg_edge'] else 0.0
        avg_clv = float(stats['avg_clv']) if stats['avg_clv'] else 0.0
        starting_balance = float(stats['starting_balance'])

        # Calculate derived metrics
        new_balance = starting_balance + total_profit_loss
        win_rate = (win_count / (win_count + loss_count) * 100) if (win_count + loss_count) > 0 else 0.0
        roi_percent = (total_profit_loss / total_staked * 100) if total_staked > 0 else 0.0

        # Update bankroll
        update_sql = """
            UPDATE paper_bankroll
            SET balance = %s,
                total_bets = %s,
                total_staked = %s,
                total_profit_loss = %s,
                roi_percent = %s,
                win_count = %s,
                loss_count = %s,
                push_count = %s,
                win_rate = %s,
                avg_edge = %s,
                avg_clv = %s,
                updated_at = NOW()
            WHERE id = (SELECT id FROM paper_bankroll LIMIT 1)
        """

        query(update_sql, [
            new_balance, total_bets, total_staked, total_profit_loss,
            round(roi_percent, 2), win_count, loss_count, push_count,
            round(win_rate, 2), round(avg_edge, 2), round(avg_clv, 2)
        ])

        logger.info(
            f"Bankroll updated: ${new_balance:.2f} | "
            f"ROI: {roi_percent:+.2f}% | "
            f"Win rate: {win_rate:.1f}% | "
            f"Avg CLV: {avg_clv:+.2f}%"
        )

    def generate_learning_signals(self):
        """
        Generate reinforcement learning signals for model improvement.

        Analyzes recent paper bet performance to identify:
        - Which markets are performing best/worst
        - Which confidence levels are accurate
        - Which edge ranges are profitable
        - CLV patterns
        """
        logger.info("Generating learning signals...")

        # Market performance
        sql_markets = """
            SELECT
                market_name,
                COUNT(*) as bets,
                AVG(CASE WHEN result = 'won' THEN 1.0 ELSE 0.0 END) as win_rate,
                AVG(profit_loss) as avg_pl,
                AVG(edge_percent) as avg_edge
            FROM paper_bets
            WHERE status != 'pending'
              AND settled_at > NOW() - INTERVAL '30 days'
            GROUP BY market_name
            HAVING COUNT(*) >= 5
            ORDER BY avg_pl DESC
        """

        markets = query(sql_markets)

        logger.info("Market Performance (last 30 days):")
        for m in markets:
            logger.info(
                f"  {m['market_name']}: {m['bets']} bets, "
                f"Win rate: {float(m['win_rate'])*100:.1f}%, "
                f"Avg P&L: ${float(m['avg_pl']):+.2f}, "
                f"Avg Edge: {float(m['avg_edge']):.1f}%"
            )

        # Confidence calibration
        sql_confidence = """
            SELECT
                confidence_level,
                COUNT(*) as bets,
                AVG(CASE WHEN result = 'won' THEN 1.0 ELSE 0.0 END) as win_rate,
                AVG(profit_loss) as avg_pl
            FROM paper_bets
            WHERE status != 'pending'
              AND settled_at > NOW() - INTERVAL '30 days'
            GROUP BY confidence_level
            HAVING COUNT(*) >= 5
            ORDER BY confidence_level DESC
        """

        confidence = query(sql_confidence)

        logger.info("Confidence Level Performance:")
        for c in confidence:
            logger.info(
                f"  {c['confidence_level']}: {c['bets']} bets, "
                f"Win rate: {float(c['win_rate'])*100:.1f}%, "
                f"Avg P&L: ${float(c['avg_pl']):+.2f}"
            )

    def run(self):
        """
        Main execution: settle all pending paper bets for completed games.
        """
        logger.info("Starting paper bet settlement...")

        # Get pending bets
        pending_bets = self.get_pending_paper_bets()
        logger.info(f"Found {len(pending_bets)} paper bets to settle")

        if not pending_bets:
            logger.info("No paper bets to settle")
            return

        # Settle each bet
        for bet in pending_bets:
            try:
                self.settle_bet(bet)
            except Exception as e:
                logger.error(f"Error settling bet {bet['id']}: {e}", exc_info=True)

        # Update bankroll
        self.update_bankroll()

        # Generate learning signals
        self.generate_learning_signals()

        logger.info(
            f"Settlement complete: {self.settled_count} bets settled, "
            f"Total P&L: ${self.total_profit_loss:+.2f}"
        )


def main():
    try:
        settlement = PaperBetSettlement()
        settlement.run()

    except Exception as e:
        logger.error(f"Error in paper bet settlement: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
