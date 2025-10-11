#!/usr/bin/env python3
"""
Autonomous Performance Analysis

Analyzes CLV, model calibration, and market performance.
Generates insights and recommendations for parameter tuning.

Usage:
    python ops/scripts/auto_analyze_performance.py --days 7
"""

import argparse
import os
import sys
import json
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'packages'))

from shared.shared.db import get_db

load_dotenv()


class PerformanceAnalyzer:
    """Autonomous performance analysis and recommendation engine."""

    def __init__(self, days: int = 7):
        self.db = get_db()
        self.days = days

    def analyze_clv(self) -> Dict:
        """Analyze CLV performance."""
        sql = """
            SELECT
                COUNT(*) as total_signals,
                ROUND(AVG(clv_percent), 3) as avg_clv,
                ROUND(STDDEV(clv_percent), 3) as stddev_clv,
                COUNT(CASE WHEN clv_percent > 0 THEN 1 END)::float / COUNT(*) * 100 as beat_close_pct
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

    def analyze_by_sport(self) -> List[Dict]:
        """Analyze performance by sport."""
        sql = """
            SELECT
                g.sport,
                COUNT(*) as signals,
                ROUND(AVG(s.clv_percent), 3) as avg_clv,
                COUNT(CASE WHEN s.clv_percent > 0 THEN 1 END)::float / COUNT(*) * 100 as beat_close_pct,
                ROUND(AVG(s.edge_percent), 2) as avg_edge
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

    def analyze_by_market(self) -> List[Dict]:
        """Analyze performance by market type."""
        sql = """
            SELECT
                m.name as market,
                COUNT(*) as signals,
                ROUND(AVG(s.clv_percent), 3) as avg_clv,
                COUNT(CASE WHEN s.clv_percent > 0 THEN 1 END)::float / COUNT(*) * 100 as beat_close_pct,
                ROUND(AVG(s.edge_percent), 2) as avg_edge
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

    def analyze_by_confidence(self) -> List[Dict]:
        """Analyze if confidence levels are calibrated."""
        sql = """
            SELECT
                confidence_level,
                COUNT(*) as signals,
                ROUND(AVG(clv_percent), 3) as avg_clv,
                COUNT(CASE WHEN clv_percent > 0 THEN 1 END)::float / COUNT(*) * 100 as beat_close_pct,
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

    def generate_recommendations(self) -> Dict:
        """Generate automated recommendations based on analysis."""
        recommendations = {
            'parameter_adjustments': [],
            'market_filters': [],
            'confidence_recalibration': [],
            'alerts': []
        }

        # Analyze overall CLV
        overall = self.analyze_clv()

        if overall['total_signals'] < 50:
            recommendations['alerts'].append({
                'type': 'insufficient_data',
                'message': f"Only {overall['total_signals']} signals with CLV. Need 100+ for reliable analysis.",
                'action': 'continue_collecting'
            })
            return recommendations

        # Overall CLV recommendations
        if overall['avg_clv'] < -0.5:
            recommendations['parameter_adjustments'].append({
                'parameter': 'edge_threshold',
                'current': '2%',
                'recommended': '3-4%',
                'reason': f"Negative CLV ({overall['avg_clv']:.2f}%) indicates model not beating market"
            })
        elif overall['avg_clv'] > 2.0:
            recommendations['parameter_adjustments'].append({
                'parameter': 'edge_threshold',
                'current': '2%',
                'recommended': '1-1.5%',
                'reason': f"High CLV ({overall['avg_clv']:.2f}%) suggests room to lower threshold"
            })

        # Beat closing % recommendations
        if overall['beat_close_pct'] < 48:
            recommendations['alerts'].append({
                'type': 'poor_performance',
                'message': f"Only beating closing {overall['beat_close_pct']:.1f}% (target: >52%)",
                'action': 'increase_edge_threshold_or_review_model'
            })

        # Sport-specific recommendations
        by_sport = self.analyze_by_sport()
        for sport_data in by_sport:
            if sport_data['avg_clv'] < -1.0:
                recommendations['market_filters'].append({
                    'sport': sport_data['sport'],
                    'action': 'reduce_signals',
                    'reason': f"Negative CLV ({sport_data['avg_clv']:.2f}%) in {sport_data['sport']}"
                })

        # Market-specific recommendations
        by_market = self.analyze_by_market()
        for market_data in by_market:
            if market_data['avg_clv'] < -1.0 and market_data['signals'] > 10:
                recommendations['market_filters'].append({
                    'market': market_data['market'],
                    'action': 'disable_or_increase_threshold',
                    'reason': f"Negative CLV ({market_data['avg_clv']:.2f}%) in {market_data['market']} market"
                })

        # Confidence calibration
        by_confidence = self.analyze_by_confidence()
        if len(by_confidence) >= 2:
            # Check if high confidence actually performs better
            high_conf = next((x for x in by_confidence if x['confidence_level'] == 'high'), None)
            low_conf = next((x for x in by_confidence if x['confidence_level'] == 'low'), None)

            if high_conf and low_conf:
                if high_conf['avg_clv'] <= low_conf['avg_clv']:
                    recommendations['confidence_recalibration'].append({
                        'issue': 'high_confidence_not_better',
                        'high_clv': float(high_conf['avg_clv']),
                        'low_clv': float(low_conf['avg_clv']),
                        'action': 'review_confidence_thresholds'
                    })

        return recommendations

    def save_analysis(self, analysis: Dict):
        """Save analysis results to database for tracking."""
        sql = """
            CREATE TABLE IF NOT EXISTS performance_analysis (
                id SERIAL PRIMARY KEY,
                analysis_date DATE NOT NULL,
                period_days INTEGER,
                overall_clv DECIMAL(5, 2),
                beat_close_pct DECIMAL(5, 2),
                total_signals INTEGER,
                recommendations JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """

        insert_sql = """
            INSERT INTO performance_analysis (
                analysis_date, period_days, overall_clv, beat_close_pct,
                total_signals, recommendations
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                cur.execute(insert_sql, (
                    datetime.now().date(),
                    self.days,
                    analysis['overall']['avg_clv'],
                    analysis['overall']['beat_close_pct'],
                    analysis['overall']['total_signals'],
                    json.dumps(analysis['recommendations'])
                ))
                conn.commit()

    def run_analysis(self) -> Dict:
        """Run full autonomous analysis."""
        print(f"[AutoAnalysis] Running performance analysis for last {self.days} days...")

        analysis = {
            'timestamp': datetime.now().isoformat(),
            'period_days': self.days,
            'overall': self.analyze_clv(),
            'by_sport': self.analyze_by_sport(),
            'by_market': self.analyze_by_market(),
            'by_confidence': self.analyze_by_confidence(),
            'recommendations': self.generate_recommendations()
        }

        # Save to database
        try:
            self.save_analysis(analysis)
            print("[AutoAnalysis] ✅ Analysis saved to database")
        except Exception as e:
            print(f"[AutoAnalysis] ⚠️  Could not save analysis: {e}")

        # Print summary
        print("\n" + "="*70)
        print("AUTONOMOUS PERFORMANCE ANALYSIS")
        print("="*70)
        print(f"\n📊 Overall (Last {self.days} days):")
        print(f"   Signals with CLV: {analysis['overall']['total_signals']}")
        print(f"   Average CLV: {analysis['overall']['avg_clv']:+.2f}%")
        print(f"   Beat Closing: {analysis['overall']['beat_close_pct']:.1f}%")

        print(f"\n🎯 Recommendations:")
        recs = analysis['recommendations']

        if recs['alerts']:
            print(f"\n⚠️  ALERTS:")
            for alert in recs['alerts']:
                print(f"   - {alert['message']}")
                print(f"     Action: {alert['action']}")

        if recs['parameter_adjustments']:
            print(f"\n🔧 PARAMETER ADJUSTMENTS:")
            for adj in recs['parameter_adjustments']:
                print(f"   - {adj['parameter']}: {adj['current']} → {adj['recommended']}")
                print(f"     Reason: {adj['reason']}")

        if recs['market_filters']:
            print(f"\n🚫 MARKET FILTERS:")
            for filt in recs['market_filters']:
                sport_or_market = filt.get('sport') or filt.get('market')
                print(f"   - {sport_or_market}: {filt['action']}")
                print(f"     Reason: {filt['reason']}")

        if recs['confidence_recalibration']:
            print(f"\n📉 CONFIDENCE RECALIBRATION:")
            for cal in recs['confidence_recalibration']:
                print(f"   - Issue: {cal['issue']}")
                print(f"     High confidence CLV: {cal['high_clv']:+.2f}%")
                print(f"     Low confidence CLV: {cal['low_clv']:+.2f}%")

        print("\n" + "="*70 + "\n")

        return analysis


def main():
    parser = argparse.ArgumentParser(description='Autonomous performance analysis')
    parser.add_argument('--days', type=int, default=7, help='Days to analyze (default: 7)')

    args = parser.parse_args()

    analyzer = PerformanceAnalyzer(days=args.days)
    analysis = analyzer.run_analysis()

    # Output JSON for automation
    print(json.dumps(analysis, indent=2, default=str))


if __name__ == '__main__':
    main()
