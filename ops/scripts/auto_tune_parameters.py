#!/usr/bin/env python3
"""
Autonomous Parameter Tuning

Automatically adjusts model parameters based on CLV performance.
Uses conservative, evidence-based adjustments.

Usage:
    python ops/scripts/auto_tune_parameters.py --dry-run  # Preview changes
    python ops/scripts/auto_tune_parameters.py --apply    # Apply changes
"""

import argparse
import os
import sys
import json
from datetime import datetime
from typing import Dict
from dotenv import load_dotenv, set_key

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'packages'))

from shared.shared.db import get_db

load_dotenv()


class ParameterTuner:
    """Autonomous parameter tuning based on performance."""

    def __init__(self, dry_run: bool = True):
        self.db = get_db()
        self.dry_run = dry_run
        self.env_file = '.env'

        # Current parameters
        self.params = {
            'EDGE_SIDES': float(os.getenv('EDGE_SIDES', '0.02')),
            'EDGE_PROPS': float(os.getenv('EDGE_PROPS', '0.03')),
            'KELLY_FRACTION': float(os.getenv('KELLY_FRACTION', '0.25')),
            'MAX_STAKE_PCT': float(os.getenv('MAX_STAKE_PCT', '0.01'))
        }

    def get_recent_performance(self, days: int = 14) -> Dict:
        """Get performance metrics for tuning decisions."""
        sql = """
            SELECT
                COUNT(*) as total_signals,
                ROUND(AVG(clv_percent), 3) as avg_clv,
                ROUND(STDDEV(clv_percent), 3) as stddev_clv,
                COUNT(CASE WHEN clv_percent > 0 THEN 1 END)::float / COUNT(*) * 100 as beat_close_pct,
                ROUND(AVG(edge_percent), 2) as avg_edge
            FROM signals
            WHERE clv_percent IS NOT NULL
                AND created_at > NOW() - INTERVAL '%s days'
        """

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (days,))
                columns = [desc[0] for desc in cur.description]
                result = dict(zip(columns, cur.fetchone()))

        return result

    def calculate_adjustments(self, performance: Dict) -> Dict:
        """Calculate parameter adjustments based on performance."""
        adjustments = {}

        # Minimum sample size check
        if performance['total_signals'] < 100:
            print(f"[AutoTune] ⚠️  Insufficient data ({performance['total_signals']} signals). Need 100+ for tuning.")
            return adjustments

        # Edge threshold tuning based on CLV
        avg_clv = float(performance['avg_clv'])
        current_edge_sides = self.params['EDGE_SIDES']

        if avg_clv < -0.5:
            # Negative CLV: increase threshold (be more selective)
            new_edge = min(current_edge_sides * 1.2, 0.05)  # Cap at 5%
            adjustments['EDGE_SIDES'] = {
                'current': current_edge_sides,
                'new': round(new_edge, 3),
                'change': '+20%',
                'reason': f'Negative CLV ({avg_clv:.2f}%) - need higher threshold'
            }
        elif avg_clv > 1.5 and performance['beat_close_pct'] > 55:
            # Strong positive CLV: slightly decrease threshold (capture more edge)
            new_edge = max(current_edge_sides * 0.95, 0.01)  # Floor at 1%
            adjustments['EDGE_SIDES'] = {
                'current': current_edge_sides,
                'new': round(new_edge, 3),
                'change': '-5%',
                'reason': f'Strong CLV ({avg_clv:.2f}%) - can lower threshold'
            }

        # Kelly fraction tuning based on variance
        stddev_clv = float(performance['stddev_clv'] or 0)
        current_kelly = self.params['KELLY_FRACTION']

        if stddev_clv > 2.0 and current_kelly > 0.15:
            # High variance: reduce Kelly (more conservative)
            new_kelly = current_kelly * 0.9
            adjustments['KELLY_FRACTION'] = {
                'current': current_kelly,
                'new': round(new_kelly, 2),
                'change': '-10%',
                'reason': f'High CLV variance ({stddev_clv:.2f}%) - reduce position sizing'
            }

        return adjustments

    def apply_adjustments(self, adjustments: Dict):
        """Apply parameter adjustments to .env file."""
        if not adjustments:
            print("[AutoTune] No adjustments needed")
            return

        print("\n" + "="*70)
        print("PARAMETER ADJUSTMENTS")
        print("="*70)

        for param, details in adjustments.items():
            print(f"\n{param}:")
            print(f"  Current: {details['current']}")
            print(f"  New: {details['new']} ({details['change']})")
            print(f"  Reason: {details['reason']}")

            if not self.dry_run:
                # Update .env file
                set_key(self.env_file, param, str(details['new']))
                print(f"  ✅ Updated in .env")
            else:
                print(f"  ⏸️  DRY RUN - No changes applied")

        print("\n" + "="*70)

        if not self.dry_run:
            print("\n⚠️  IMPORTANT: Restart signal generation for changes to take effect")
            print("   GitHub Actions will pick up changes on next scheduled run")

        # Log to database
        self.log_tuning(adjustments)

    def log_tuning(self, adjustments: Dict):
        """Log tuning decisions to database."""
        sql = """
            CREATE TABLE IF NOT EXISTS parameter_tuning_log (
                id SERIAL PRIMARY KEY,
                tuning_date TIMESTAMP DEFAULT NOW(),
                adjustments JSONB,
                applied BOOLEAN,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """

        insert_sql = """
            INSERT INTO parameter_tuning_log (adjustments, applied)
            VALUES (%s, %s)
        """

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                cur.execute(insert_sql, (json.dumps(adjustments), not self.dry_run))
                conn.commit()

    def run(self):
        """Run autonomous parameter tuning."""
        print(f"[AutoTune] Running parameter tuning...")
        print(f"[AutoTune] Mode: {'DRY RUN (preview only)' if self.dry_run else 'APPLY CHANGES'}")

        # Get performance
        performance = self.get_recent_performance(days=14)

        print(f"\n📊 Recent Performance (14 days):")
        print(f"   Signals: {performance['total_signals']}")
        print(f"   Avg CLV: {performance['avg_clv']:+.2f}%")
        print(f"   Beat Closing: {performance['beat_close_pct']:.1f}%")
        print(f"   Avg Edge: {performance['avg_edge']:.2f}%")

        # Calculate adjustments
        adjustments = self.calculate_adjustments(performance)

        # Apply or preview
        self.apply_adjustments(adjustments)


def main():
    parser = argparse.ArgumentParser(description='Autonomous parameter tuning')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--dry-run', action='store_true', help='Preview changes without applying')
    group.add_argument('--apply', action='store_true', help='Apply parameter changes')

    args = parser.parse_args()

    tuner = ParameterTuner(dry_run=args.dry_run)
    tuner.run()


if __name__ == '__main__':
    main()
