#!/usr/bin/env python3
"""
API Quota Monitoring Script

Checks The Odds API quota status and alerts when running low.
Integrates with existing api_usage_log table for tracking.
"""

import os
import sys
from dotenv import load_dotenv
import requests

# Load environment
load_dotenv()

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'packages'))

from shared.shared.db import get_db


def check_quota():
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

        # Alert thresholds
        if remaining == 0:
            print("\n[ALERT] 🚨 CRITICAL: API quota EXHAUSTED!")
            print("[ALERT] No more requests possible until quota resets")
            print("[ALERT] Workflows will fail until reset")
            sys.exit(2)  # Exit code 2 = quota exhausted

        elif usage_pct >= 95:
            print(f"\n[ALERT] ⚠️  WARNING: {usage_pct:.1f}% of quota used!")
            print("[ALERT] Consider reducing polling frequency or upgrading plan")
            sys.exit(1)  # Exit code 1 = warning threshold

        elif usage_pct >= 90:
            print(f"\n[ALERT] ⚠️  CAUTION: {usage_pct:.1f}% of quota used")
            print("[ALERT] Approaching quota limit")

        elif usage_pct >= 80:
            print(f"\n[NOTICE] 📊 {usage_pct:.1f}% of quota used")

        else:
            print(f"[Quota Check] ✅ Status: Healthy ({usage_pct:.1f}% used)")

        # Log to database
        db = get_db()
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
                        'theoddsapi', '/sports', 'quota_check', 1,
                        remaining, total, response.status_code, True
                    ))
                    conn.commit()
        except Exception as e:
            print(f"[WARNING] Failed to log quota check: {e}")

        return {
            'remaining': remaining,
            'used': used,
            'total': total,
            'usage_pct': usage_pct
        }

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to check API quota: {e}")
        sys.exit(3)  # Exit code 3 = request error


if __name__ == '__main__':
    check_quota()
