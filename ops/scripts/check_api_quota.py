#!/usr/bin/env python3
"""
API Quota Monitoring Script

Checks The Odds API quota status and alerts when running low.
Integrates with existing api_usage_log table for tracking.
Supports configurable safety buffers for automation gating.
"""

import argparse
import json
import os
import sys
from textwrap import dedent
from dotenv import load_dotenv
import requests

# Load environment
load_dotenv()

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'packages'))

from shared.shared.db import get_db


def ensure_usage_view(db):
    """Ensure api_usage_current_month view matches latest definition."""
    view_sql = dedent("""
        CREATE OR REPLACE VIEW api_usage_current_month AS
        SELECT
            provider,
            COUNT(*) AS requests_this_month,
            SUM(credits_used) AS credits_used_this_month,
            MIN(credits_remaining) AS credits_remaining,
            MAX(credits_total) AS credits_total,
            ROUND(
                (SUM(credits_used)::DECIMAL / NULLIF(MAX(credits_total), 0)) * 100,
                1
            ) AS usage_percent,
            MAX(request_timestamp) AS last_request
        FROM api_usage_log
        WHERE request_timestamp >= DATE_TRUNC('month', CURRENT_TIMESTAMP)
        GROUP BY provider;
    """)

    try:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(view_sql)
            conn.commit()
        print("[Quota Check] Ensured api_usage_current_month view is up to date.")
    except Exception as exc:
        print(f"[WARNING] Could not refresh api_usage_current_month view: {exc}")


def check_quota(min_remaining: int = 0):
    """Check current API quota status."""
    api_key = os.getenv('THE_ODDS_API_KEY')

    if not api_key:
        print("[ERROR] THE_ODDS_API_KEY not set")
        sys.exit(1)

    # Make a minimal API call to check quota
    url = 'https://api.the-odds-api.com/v4/sports'
    params = {'apiKey': api_key}

    try:
        response = requests.get(url, params=params, timeout=10)

        # Extract quota info from headers
        remaining = response.headers.get('x-requests-remaining', 'N/A')
        used = response.headers.get('x-requests-used', 'N/A')

        if remaining == 'N/A' or used == 'N/A':
            print("[WARNING] Could not retrieve quota information from API headers")
            return

        remaining = int(remaining)
        used = int(used)
        total = 500  # Free tier limit

        usage_pct = (used / total * 100) if total > 0 else 0

        print("[Quota Check] ===== API QUOTA STATUS =====")
        print(f"[Quota Check] Used: {used}/{total} ({usage_pct:.1f}%)")
        print(f"[Quota Check] Remaining: {remaining}")

        exit_code = 0
        status = 'healthy'

        # Alert thresholds
        if remaining == 0:
            print("\n[ALERT] 🚨 CRITICAL: API quota EXHAUSTED!")
            print("[ALERT] No more requests possible until quota resets")
            print("[ALERT] Workflows will fail until reset")
            exit_code = 2  # Exit code 2 = quota exhausted

        elif remaining < min_remaining:
            print(f"\n[NOTICE] 📉 Remaining credits ({remaining}) below safety buffer ({min_remaining}).")
            print("[NOTICE] Skipping heavy workflows to preserve emergency capacity.")
            exit_code = 4  # Custom code for automation gating

        elif usage_pct >= 95:
            print(f"\n[ALERT] ⚠️  WARNING: {usage_pct:.1f}% of quota used!")
            print("[ALERT] Consider reducing polling frequency or upgrading plan")
            exit_code = 1  # Exit code 1 = warning threshold

        elif usage_pct >= 90:
            print(f"\n[ALERT] ⚠️  CAUTION: {usage_pct:.1f}% of quota used")
            print("[ALERT] Approaching quota limit")
            status = 'caution'

        elif usage_pct >= 80:
            print(f"\n[NOTICE] 📊 {usage_pct:.1f}% of quota used")
            status = 'notice'

        else:
            print(f"[Quota Check] ✅ Status: Healthy ({usage_pct:.1f}% used)")
            status = 'healthy'

        # Log to database (and ensure monitoring view is up to date)
        db = get_db()
        ensure_usage_view(db)
        try:
            with db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO api_usage_log (
                            provider, endpoint, league, credits_used,
                            credits_remaining, credits_total,
                            response_status, success
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        'theoddsapi', '/sports', 'quota', 1,
                        remaining, total, response.status_code, True
                    ))
                    conn.commit()
        except Exception as e:
            print(f"[WARNING] Failed to log quota check: {e}")

        result = {
            'remaining': remaining,
            'used': used,
            'total': total,
            'usage_pct': usage_pct,
            'status': status,
            'min_remaining': min_remaining
        }
        return result, exit_code

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to check API quota: {e}")
        sys.exit(3)  # Exit code 3 = request error


def main():
    parser = argparse.ArgumentParser(description='Check The Odds API quota status')
    parser.add_argument(
        '--min-remaining',
        type=int,
        default=0,
        help='Minimum credits that must remain to continue heavy workflows (default: 0)'
    )
    parser.add_argument(
        '--json-output',
        type=str,
        help='Optional path to write quota info as JSON'
    )
    args = parser.parse_args()

    result = check_quota(min_remaining=args.min_remaining)
    if not result:
        return

    data, exit_code = result

    if args.json_output:
        try:
            with open(args.json_output, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except OSError as exc:
            print(f"[WARNING] Failed to write JSON output: {exc}")

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
