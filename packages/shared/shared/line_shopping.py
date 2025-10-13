"""
Line Shopping Module

Compares odds across multiple sportsbooks and selects the best available.
Research shows this adds +1-2% ROI improvement immediately.

Usage:
    from shared.shared.line_shopping import select_best_odds

    best = select_best_odds(
        game_id=123,
        market_id=1,
        selection="Eagles -7.5",
        sportsbooks=['draftkings', 'fanduel', 'betmgm']
    )
"""

from typing import Dict, List, Optional
from .db import get_db


def select_best_odds(
    game_id: int,
    market_id: int,
    selection: str,
    sportsbooks: List[str],
    max_age_minutes: int = 30
) -> Optional[Dict]:
    """
    Compare odds across all sportsbooks and return the best.

    Args:
        game_id: Database game ID
        market_id: Database market ID
        selection: Selection string (e.g., "Eagles -7.5", "Over 45.5")
        sportsbooks: List of sportsbook names to compare
        max_age_minutes: Maximum age of odds in minutes (default 30)

    Returns:
        Dict with best odds or None if no odds found:
        {
            'sportsbook': 'draftkings',
            'odds_american': -110,
            'odds_decimal': 1.909,
            'implied_prob': 0.524,
            'improvement_pct': 1.5  # vs average odds
        }
    """
    db = get_db()

    # Fetch all recent odds for this game/market/selection
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    sportsbook,
                    odds_american,
                    odds_decimal,
                    implied_probability
                FROM odds_snapshots
                WHERE game_id = %s
                  AND market_id = %s
                  AND selection = %s
                  AND sportsbook = ANY(%s)
                  AND fetched_at > NOW() - INTERVAL '%s minutes'
                ORDER BY odds_decimal DESC
            """, (game_id, market_id, selection, sportsbooks, max_age_minutes))

            rows = cur.fetchall()

    if not rows:
        return None

    # Best odds = highest decimal odds (best value for bettor)
    best_row = rows[0]

    # Calculate improvement vs average
    avg_decimal = sum(float(row[2]) for row in rows) / len(rows)
    best_decimal = float(best_row[2])
    improvement_pct = ((best_decimal - avg_decimal) / avg_decimal) * 100

    return {
        'sportsbook': best_row[0],
        'odds_american': int(best_row[1]),
        'odds_decimal': float(best_row[2]),
        'implied_prob': float(best_row[3]),
        'improvement_pct': round(improvement_pct, 2),
        'books_compared': len(rows)
    }


def get_all_odds_for_selection(
    game_id: int,
    market_id: int,
    selection: str,
    max_age_minutes: int = 30
) -> List[Dict]:
    """
    Get all available odds for a selection across all books.

    Useful for visualization and comparison.
    """
    db = get_db()

    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    sportsbook,
                    odds_american,
                    odds_decimal,
                    implied_probability,
                    fetched_at
                FROM odds_snapshots
                WHERE game_id = %s
                  AND market_id = %s
                  AND selection = %s
                  AND fetched_at > NOW() - INTERVAL '%s minutes'
                ORDER BY odds_decimal DESC
            """, (game_id, market_id, selection, max_age_minutes))

            rows = cur.fetchall()

    return [
        {
            'sportsbook': row[0],
            'odds_american': int(row[1]),
            'odds_decimal': float(row[2]),
            'implied_prob': float(row[3]),
            'fetched_at': row[4]
        }
        for row in rows
    ]


def calculate_line_shopping_impact(days: int = 30) -> Dict:
    """
    Calculate historical impact of line shopping on signals.

    Compares signals that would have been placed with line shopping
    vs without line shopping.

    Args:
        days: Number of days to analyze

    Returns:
        Dict with impact metrics:
        {
            'avg_improvement_pct': 1.2,
            'roi_boost_estimate': 1.5,
            'signals_analyzed': 1250
        }
    """
    db = get_db()

    # Query signals with their odds improvement tracking
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    AVG(odds_improvement_pct) as avg_improvement,
                    COUNT(*) as signal_count
                FROM signals
                WHERE created_at > NOW() - INTERVAL '%s days'
                  AND odds_improvement_pct IS NOT NULL
            """, (days,))

            row = cur.fetchone()

    if not row or not row[0]:
        return {
            'avg_improvement_pct': 0,
            'roi_boost_estimate': 0,
            'signals_analyzed': 0
        }

    avg_improvement = float(row[0])
    signal_count = row[1]

    # ROI boost is approximately equal to odds improvement
    # (slightly conservative estimate)
    roi_boost = avg_improvement * 0.8

    return {
        'avg_improvement_pct': round(avg_improvement, 2),
        'roi_boost_estimate': round(roi_boost, 2),
        'signals_analyzed': signal_count
    }
