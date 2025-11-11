#!/usr/bin/env python3
"""
Milestone Readiness Checker

Checks if milestone criteria are met and logs results to database.
Runs daily via GitHub Actions to track progress toward phase advancement.

Usage:
    python ops/scripts/check_milestone_readiness.py
    python ops/scripts/check_milestone_readiness.py --milestone-id 1
    python ops/scripts/check_milestone_readiness.py --send-alerts
"""

import argparse
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Tuple
import json

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'packages'))

from shared.shared.db import get_db
from scipy import stats
import numpy as np

def calculate_p_value_from_bets() -> float:
    """
    Calculate p-value for statistical significance of edge.

    Uses one-sample t-test to determine if mean ROI is significantly > 0.
    """
    db = get_db()

    # Get all settled paper bets
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT profit_loss, stake
                FROM paper_bets
                WHERE status IN ('won', 'lost', 'push', 'void')
                  AND profit_loss IS NOT NULL
            """)
            bets = cur.fetchall()

    if not bets or len(bets) < 30:
        return 1.0  # Not enough data, return worst p-value

    # Calculate ROI for each bet
    rois = [float(profit_loss) / float(stake) for profit_loss, stake in bets if stake > 0]

    if not rois:
        return 1.0

    # One-sample t-test: Is mean ROI significantly > 0?
    t_stat, p_value = stats.ttest_1samp(rois, 0, alternative='greater')

    return float(p_value)


def check_feature_implemented(feature_name: str) -> bool:
    """
    Check if a feature is implemented by looking for marker in database or files.
    """
    if feature_name == 'line_shopping':
        db = get_db()
        try:
            with db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT COUNT(*)
                        FROM signals
                        WHERE odds_improvement_pct IS NOT NULL
                          AND odds_improvement_pct > 0
                          AND created_at > NOW() - INTERVAL '14 days'
                    """)
                    count = cur.fetchone()[0]
                    if count > 0:
                        return True
        except Exception:
            return False
        return False

    elif feature_name == 'backtesting':
        # Check if backtest results table exists and has data
        db = get_db()
        try:
            with db.get_connection() as conn:
                with conn.cursor() as cur:
                    # Check for backtest_results table (will be created during backtesting)
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_name = 'backtest_results'
                        )
                    """)
                    table_exists = cur.fetchone()[0]

                    if not table_exists:
                        return False

                    # Check if it has enough data
                    cur.execute("SELECT COUNT(*) FROM backtest_results")
                    count = cur.fetchone()[0]
                    return count >= 1000
        except Exception:
            return False

    elif feature_name == 'ml_model':
        # Check if ML model file exists
        model_path = os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'nfl_ml_model.pkl')
        return os.path.exists(model_path)

    elif feature_name == 'props':
        # Check if prop markets exist in database
        db = get_db()
        try:
            with db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT 1 FROM markets
                            WHERE category = 'prop' OR name LIKE '%prop%'
                        )
                    """)
                    return cur.fetchone()[0]
        except Exception:
            return False

    return False


def check_milestone_criteria(milestone_id: int) -> Tuple[bool, Dict[str, Any]]:
    """
    Check if all criteria are met for a milestone.

    Returns:
        (all_met, results_dict)
    """
    db = get_db()

    # Fetch milestone
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT name, criteria
                FROM milestones
                WHERE id = %s
            """, (milestone_id,))
            row = cur.fetchone()

    if not row:
        print(f"[ERROR] Milestone {milestone_id} not found")
        return False, {}

    milestone_name, criteria = row
    criteria = json.loads(criteria) if isinstance(criteria, str) else criteria

    print(f"\n[CHECK] Checking milestone: {milestone_name}")
    print(f"[CHECK] Criteria: {len(criteria)} items")

    results = {}

    for criterion_key, criterion_config in criteria.items():
        target = criterion_config['target']
        description = criterion_config['description']

        print(f"\n  Checking: {description}")

        # Check different criterion types
        if criterion_key == 'paper_bets_settled':
            with db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT COUNT(*)
                        FROM paper_bets
                        WHERE status IN ('won', 'lost', 'push', 'void')
                    """)
                    current = cur.fetchone()[0]

            met = current >= target
            results[criterion_key] = {
                'current': current,
                'target': target,
                'met': met,
                'description': description
            }
            print(f"    {current} / {target} → {'✅' if met else '❌'}")

        elif criterion_key == 'roi_pct':
            with db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT roi_percent FROM paper_bankroll
                        ORDER BY updated_at DESC LIMIT 1
                    """)
                    row = cur.fetchone()
                    current = float(row[0]) if row and row[0] else 0.0

            met = current >= target
            results[criterion_key] = {
                'current': round(current, 2),
                'target': target,
                'met': met,
                'description': description
            }
            print(f"    {current:.2f}% / {target}% → {'✅' if met else '❌'}")

        elif criterion_key == 'clv_pct':
            with db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT AVG(clv_percent), COUNT(*)
                        FROM signals
                        WHERE clv_percent IS NOT NULL
                    """)
                    row = cur.fetchone()
                    avg_clv = float(row[0]) if row and row[0] else 0.0
                    sample_size = int(row[1] or 0)

            current = avg_clv
            min_sample = criterion_config.get('min_sample', 50)

            if sample_size < min_sample:
                met = False
                note = f"Insufficient CLV sample size ({sample_size}/{min_sample})"
                print(f"    {note}")
            else:
                met = current >= target
                note = None

            results[criterion_key] = {
                'current': round(current, 2),
                'target': target,
                'met': met,
                'description': description,
                'sample_size': sample_size,
                'note': note
            }
            print(f"    {current:.2f}% / {target}% → {'✅' if met else '❌'}")

        elif criterion_key == 'p_value_max':
            current = calculate_p_value_from_bets()
            met = current <= target
            results[criterion_key] = {
                'current': round(current, 4),
                'target': target,
                'met': met,
                'description': description
            }
            print(f"    {current:.4f} / {target} → {'✅' if met else '❌'}")

        elif criterion_key in ['line_shopping_implemented', 'backtesting_completed',
                                'ml_model_trained', 'props_added']:
            feature_map = {
                'line_shopping_implemented': 'line_shopping',
                'backtesting_completed': 'backtesting',
                'ml_model_trained': 'ml_model',
                'props_added': 'props'
            }
            current = check_feature_implemented(feature_map.get(criterion_key, criterion_key))
            met = current == target
            results[criterion_key] = {
                'current': current,
                'target': target,
                'met': met,
                'description': description
            }
            print(f"    {current} / {target} → {'✅' if met else '❌'}")

        else:
            # Generic boolean or numeric check
            # For now, mark as not met
            results[criterion_key] = {
                'current': None,
                'target': target,
                'met': False,
                'description': description
            }
            print(f"    [SKIP] Not implemented yet")

    all_met = all(r['met'] for r in results.values())

    print(f"\n[RESULT] Milestone '{milestone_name}': {len([r for r in results.values() if r['met']])} / {len(results)} criteria met")
    print(f"[RESULT] Overall: {'✅ READY' if all_met else '⚠️  NOT READY'}")

    return all_met, results


def log_milestone_check(milestone_id: int, all_met: bool, results: Dict[str, Any], notes: str = None):
    """
    Log milestone check result to database.
    """
    db = get_db()

    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO milestone_checks (
                    milestone_id, checked_at, criteria_met, all_criteria_met, notes
                ) VALUES (%s, %s, %s, %s, %s)
            """, (
                milestone_id,
                datetime.now(timezone.utc),
                json.dumps(results),
                all_met,
                notes
            ))
            conn.commit()

    print(f"[LOG] Milestone check logged to database")


def send_alert_if_ready(milestone_id: int, milestone_name: str, all_met: bool):
    """
    Send Slack alert if milestone is complete.
    """
    if not all_met:
        return

    slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
    if not slack_webhook:
        print("[ALERT] No Slack webhook configured, skipping alert")
        return

    import requests

    message = {
        'text': f"🎉 *Milestone Complete: {milestone_name}*",
        'blocks': [
            {
                'type': 'header',
                'text': {
                    'type': 'plain_text',
                    'text': f"🎉 Milestone Complete: {milestone_name}"
                }
            },
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': f"All criteria for *{milestone_name}* have been met!\n\nCheck the dashboard for next steps: `/progress`"
                }
            }
        ]
    }

    try:
        response = requests.post(slack_webhook, json=message, timeout=10)
        response.raise_for_status()
        print(f"[ALERT] Slack alert sent successfully")
    except Exception as e:
        print(f"[ALERT] Failed to send Slack alert: {e}")


def main():
    parser = argparse.ArgumentParser(description='Check milestone readiness')
    parser.add_argument('--milestone-id', type=int, help='Specific milestone to check')
    parser.add_argument('--send-alerts', action='store_true', help='Send Slack alerts if ready')

    args = parser.parse_args()

    db = get_db()

    if args.milestone_id:
        # Check specific milestone
        milestone_ids = [args.milestone_id]
    else:
        # Check all active milestones
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id FROM milestones
                    WHERE status IN ('pending', 'in_progress')
                    ORDER BY id
                """)
                milestone_ids = [row[0] for row in cur.fetchall()]

    print(f"\n[START] Checking {len(milestone_ids)} milestone(s)")

    for milestone_id in milestone_ids:
        try:
            # Fetch milestone name
            with db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT name FROM milestones WHERE id = %s", (milestone_id,))
                    row = cur.fetchone()
                    milestone_name = row[0] if row else f"Milestone {milestone_id}"

            # Check criteria
            all_met, results = check_milestone_criteria(milestone_id)

            # Log to database
            log_milestone_check(milestone_id, all_met, results)

            # Send alert if ready
            if args.send_alerts:
                send_alert_if_ready(milestone_id, milestone_name, all_met)

        except Exception as e:
            print(f"[ERROR] Failed to check milestone {milestone_id}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n[DONE] Milestone checks complete")


if __name__ == '__main__':
    main()
