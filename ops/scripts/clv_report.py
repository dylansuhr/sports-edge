#!/usr/bin/env python3
"""
CLV Performance Report

Analyzes closing line value (CLV) to measure model performance.
Positive CLV is the strongest indicator of long-term profitability.

Usage:
    python ops/scripts/clv_report.py
    python ops/scripts/clv_report.py --days 7
"""

import argparse
import os
import sys
from dotenv import load_dotenv

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'packages'))

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


class CLVReport:
    """Generate CLV performance reports."""

    def __init__(self, days: int = 30):
        self.db = get_db()
        self.days = days

    def get_clv_summary(self):
        """Get overall CLV summary statistics."""
        sql = """
            SELECT
                COUNT(*) as total_signals,
                COUNT(CASE WHEN clv_percent > 0 THEN 1 END) as positive_clv_count,
                ROUND(AVG(clv_percent), 2) as avg_clv,
                ROUND(STDDEV(clv_percent), 2) as stddev_clv,
                ROUND(MIN(clv_percent), 2) as min_clv,
                ROUND(MAX(clv_percent), 2) as max_clv,
                ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY clv_percent)::numeric, 2) as p25_clv,
                ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY clv_percent)::numeric, 2) as median_clv,
                ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY clv_percent)::numeric, 2) as p75_clv
            FROM signals
            WHERE clv_percent IS NOT NULL
                AND created_at > NOW() - INTERVAL '%s days'
        """

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (self.days,))
                columns = [desc[0] for desc in cur.description]
                result = dict(zip(columns, cur.fetchone()))

        return result

    def get_clv_by_sport(self):
        """Get CLV breakdown by sport."""
        sql = """
            SELECT
                g.sport,
                COUNT(*) as total_signals,
                COUNT(CASE WHEN s.clv_percent > 0 THEN 1 END) as positive_clv,
                ROUND(AVG(s.clv_percent), 2) as avg_clv,
                ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY s.clv_percent)::numeric, 2) as median_clv
            FROM signals s
            JOIN games g ON s.game_id = g.id
            WHERE s.clv_percent IS NOT NULL
                AND s.created_at > NOW() - INTERVAL '%s days'
            GROUP BY g.sport
            ORDER BY avg_clv DESC
        """

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (self.days,))
                columns = [desc[0] for desc in cur.description]
                results = [dict(zip(columns, row)) for row in cur.fetchall()]

        return results

    def get_clv_by_market(self):
        """Get CLV breakdown by market type."""
        sql = """
            SELECT
                m.name as market_name,
                COUNT(*) as total_signals,
                COUNT(CASE WHEN s.clv_percent > 0 THEN 1 END) as positive_clv,
                ROUND(AVG(s.clv_percent), 2) as avg_clv,
                ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY s.clv_percent)::numeric, 2) as median_clv
            FROM signals s
            JOIN markets m ON s.market_id = m.id
            WHERE s.clv_percent IS NOT NULL
                AND s.created_at > NOW() - INTERVAL '%s days'
            GROUP BY m.name
            ORDER BY avg_clv DESC
        """

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (self.days,))
                columns = [desc[0] for desc in cur.description]
                results = [dict(zip(columns, row)) for row in cur.fetchall()]

        return results

    def get_clv_by_confidence(self):
        """Get CLV breakdown by confidence level."""
        sql = """
            SELECT
                confidence_level,
                COUNT(*) as total_signals,
                COUNT(CASE WHEN clv_percent > 0 THEN 1 END) as positive_clv,
                ROUND(AVG(clv_percent), 2) as avg_clv,
                ROUND(AVG(edge_percent), 2) as avg_edge
            FROM signals
            WHERE clv_percent IS NOT NULL
                AND created_at > NOW() - INTERVAL '%s days'
            GROUP BY confidence_level
            ORDER BY
                CASE confidence_level
                    WHEN 'high' THEN 1
                    WHEN 'medium' THEN 2
                    WHEN 'low' THEN 3
                END
        """

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (self.days,))
                columns = [desc[0] for desc in cur.description]
                results = [dict(zip(columns, row)) for row in cur.fetchall()]

        return results

    def print_report(self):
        """Generate and print full CLV report."""
        print(f"\n{'='*70}")
        print(f"CLOSING LINE VALUE (CLV) PERFORMANCE REPORT")
        print(f"Period: Last {self.days} days")
        print(f"{'='*70}\n")

        # Overall summary
        summary = self.get_clv_summary()

        if summary['total_signals'] == 0:
            print("❌ No signals with CLV data found in this period.")
            print("   Run 'make clv' to capture closing lines before games start.")
            return

        positive_pct = (summary['positive_clv_count'] / summary['total_signals']) * 100

        print("📊 OVERALL SUMMARY")
        print("-" * 70)
        print(f"Total Signals with CLV:  {summary['total_signals']:,}")
        print(f"Positive CLV Count:      {summary['positive_clv_count']:,} ({positive_pct:.1f}%)")
        print(f"Average CLV:             {summary['avg_clv']:+.2f}%")
        print(f"Median CLV:              {summary['median_clv']:+.2f}%")
        print(f"Std Dev:                 {summary['stddev_clv']:.2f}%")
        print(f"Range:                   {summary['min_clv']:+.2f}% to {summary['max_clv']:+.2f}%")
        print(f"Quartiles (25/50/75):    {summary['p25_clv']:+.2f}% / {summary['median_clv']:+.2f}% / {summary['p75_clv']:+.2f}%")

        # Interpretation
        print("\n💡 INTERPRETATION")
        print("-" * 70)
        if summary['avg_clv'] > 2.0:
            print("✅ EXCELLENT: Strong positive CLV indicates high-quality model")
        elif summary['avg_clv'] > 0.5:
            print("✅ GOOD: Positive CLV suggests profitable long-term edge")
        elif summary['avg_clv'] > -0.5:
            print("⚠️  NEUTRAL: Near-zero CLV - model may need improvement")
        else:
            print("❌ POOR: Negative CLV indicates model is not beating market")

        print(f"\nBeat closing line: {positive_pct:.1f}% of signals")
        if positive_pct > 55:
            print("   Target: >52% (MEETING TARGET ✅)")
        elif positive_pct > 50:
            print("   Target: >52% (Close, keep monitoring)")
        else:
            print("   Target: >52% (BELOW TARGET ❌)")

        # By Sport
        print(f"\n📈 CLV BY SPORT")
        print("-" * 70)
        print(f"{'Sport':<12} {'Signals':>10} {'Positive CLV':>14} {'Avg CLV':>10} {'Median CLV':>12}")
        print("-" * 70)

        by_sport = self.get_clv_by_sport()
        for row in by_sport:
            pos_pct = (row['positive_clv'] / row['total_signals']) * 100
            print(f"{row['sport']:<12} {row['total_signals']:>10,} "
                  f"{row['positive_clv']:>10,} ({pos_pct:>4.1f}%) "
                  f"{row['avg_clv']:>+9.2f}% {row['median_clv']:>+11.2f}%")

        # By Market
        print(f"\n🎯 CLV BY MARKET TYPE")
        print("-" * 70)
        print(f"{'Market':<15} {'Signals':>10} {'Positive CLV':>14} {'Avg CLV':>10} {'Median CLV':>12}")
        print("-" * 70)

        by_market = self.get_clv_by_market()
        for row in by_market:
            pos_pct = (row['positive_clv'] / row['total_signals']) * 100
            print(f"{row['market_name']:<15} {row['total_signals']:>10,} "
                  f"{row['positive_clv']:>10,} ({pos_pct:>4.1f}%) "
                  f"{row['avg_clv']:>+9.2f}% {row['median_clv']:>+11.2f}%")

        # By Confidence
        print(f"\n🔍 CLV BY CONFIDENCE LEVEL")
        print("-" * 70)
        print(f"{'Level':<12} {'Signals':>10} {'Positive CLV':>14} {'Avg CLV':>10} {'Avg Edge':>11}")
        print("-" * 70)

        by_conf = self.get_clv_by_confidence()
        for row in by_conf:
            pos_pct = (row['positive_clv'] / row['total_signals']) * 100
            print(f"{row['confidence_level']:<12} {row['total_signals']:>10,} "
                  f"{row['positive_clv']:>10,} ({pos_pct:>4.1f}%) "
                  f"{row['avg_clv']:>+9.2f}% {row['avg_edge']:>+10.2f}%")

        print(f"\n{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(description='Generate CLV performance report')
    parser.add_argument('--days', type=int, default=30,
                        help='Number of days to analyze (default: 30)')

    args = parser.parse_args()

    # Check environment
    check_env_vars()

    # Generate report
    report = CLVReport(days=args.days)
    report.print_report()


if __name__ == '__main__':
    main()
