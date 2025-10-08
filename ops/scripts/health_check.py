#!/usr/bin/env python3
"""
Health Check Script

Verifies system health by checking:
- Database connectivity
- Recent data freshness (odds_snapshots, signals)
- Last ETL run time
- Table row counts

Usage:
    python ops/scripts/health_check.py
    python ops/scripts/health_check.py --verbose
"""

import argparse
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
from dotenv import load_dotenv

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'packages'))

from shared.shared.db import get_db

# Load environment
load_dotenv()


class HealthChecker:
    """System health verification."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.db = None
        self.checks_passed = 0
        self.checks_failed = 0

    def log(self, message: str, level: str = 'info'):
        """Print status message."""
        icons = {
            'info': 'ℹ️',
            'success': '✅',
            'warning': '⚠️',
            'error': '❌'
        }
        icon = icons.get(level, 'ℹ️')
        print(f"{icon} {message}")

    def check_database_connectivity(self) -> bool:
        """Verify database connection."""
        self.log("Checking database connectivity...", 'info')

        try:
            self.db = get_db()

            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT version()")
                    version = cur.fetchone()[0]

                    if self.verbose:
                        self.log(f"PostgreSQL version: {version}", 'info')

            self.log("Database connection successful", 'success')
            self.checks_passed += 1
            return True

        except Exception as e:
            self.log(f"Database connection failed: {e}", 'error')
            self.checks_failed += 1
            return False

    def check_table_exists(self, table_name: str) -> bool:
        """Verify table exists."""
        sql = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = %s
            )
        """

        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (table_name,))
                    exists = cur.fetchone()[0]

                    if exists:
                        if self.verbose:
                            self.log(f"Table '{table_name}' exists", 'success')
                        return True
                    else:
                        self.log(f"Table '{table_name}' not found", 'error')
                        self.checks_failed += 1
                        return False

        except Exception as e:
            self.log(f"Error checking table '{table_name}': {e}", 'error')
            self.checks_failed += 1
            return False

    def get_table_row_count(self, table_name: str) -> Optional[int]:
        """Get row count for a table."""
        sql = f"SELECT COUNT(*) FROM {table_name}"

        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql)
                    count = cur.fetchone()[0]
                    return count

        except Exception as e:
            if self.verbose:
                self.log(f"Error counting rows in '{table_name}': {e}", 'error')
            return None

    def check_recent_data(self, table_name: str, timestamp_column: str, hours: int = 24) -> Dict:
        """Check for recent data in a table."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        sql = f"""
            SELECT COUNT(*)
            FROM {table_name}
            WHERE {timestamp_column} >= %s
        """

        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (cutoff_time,))
                    recent_count = cur.fetchone()[0]

            # Get latest timestamp
            latest_sql = f"""
                SELECT MAX({timestamp_column})
                FROM {table_name}
            """

            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(latest_sql)
                    latest_timestamp = cur.fetchone()[0]

            return {
                'recent_count': recent_count,
                'latest_timestamp': latest_timestamp,
                'cutoff_hours': hours
            }

        except Exception as e:
            if self.verbose:
                self.log(f"Error checking recent data in '{table_name}': {e}", 'error')
            return None

    def run_health_checks(self) -> bool:
        """Run all health checks."""
        self.log("\n=== System Health Check ===\n", 'info')

        # 1. Database connectivity
        if not self.check_database_connectivity():
            return False

        # 2. Check core tables exist
        self.log("\nChecking core tables...", 'info')
        required_tables = [
            'teams', 'games', 'markets', 'odds_snapshots',
            'signals', 'bets', 'clv_history'
        ]

        for table in required_tables:
            if not self.check_table_exists(table):
                # Critical tables missing
                return False

        self.log("All core tables exist", 'success')
        self.checks_passed += 1

        # 3. Table row counts
        self.log("\nTable row counts:", 'info')
        for table in required_tables:
            count = self.get_table_row_count(table)
            if count is not None:
                self.log(f"  {table}: {count:,} rows", 'info')

        # 4. Recent odds data
        self.log("\nChecking recent odds data...", 'info')
        odds_data = self.check_recent_data('odds_snapshots', 'fetched_at', hours=24)

        if odds_data:
            recent_count = odds_data['recent_count']
            latest_timestamp = odds_data['latest_timestamp']

            if recent_count > 0:
                self.log(f"Recent odds: {recent_count:,} snapshots in last 24h", 'success')
                if latest_timestamp:
                    age_minutes = (datetime.now(timezone.utc) - latest_timestamp).total_seconds() / 60
                    self.log(f"Latest odds: {age_minutes:.1f} minutes ago", 'info')
                self.checks_passed += 1
            else:
                self.log("No odds data in last 24 hours", 'warning')
                if latest_timestamp:
                    age_hours = (datetime.now(timezone.utc) - latest_timestamp).total_seconds() / 3600
                    self.log(f"Latest odds: {age_hours:.1f} hours ago", 'warning')
                else:
                    self.log("No odds data found", 'error')
                    self.checks_failed += 1
        else:
            self.log("Cannot verify odds data freshness", 'warning')

        # 5. Recent signals
        self.log("\nChecking recent signals...", 'info')
        signals_data = self.check_recent_data('signals', 'created_at', hours=48)

        if signals_data:
            recent_count = signals_data['recent_count']
            latest_timestamp = signals_data['latest_timestamp']

            if recent_count > 0:
                self.log(f"Recent signals: {recent_count:,} in last 48h", 'success')
                if latest_timestamp:
                    age_hours = (datetime.now(timezone.utc) - latest_timestamp).total_seconds() / 3600
                    self.log(f"Latest signal: {age_hours:.1f} hours ago", 'info')
                self.checks_passed += 1
            else:
                self.log("No signals generated in last 48 hours", 'warning')
                if latest_timestamp:
                    age_days = (datetime.now(timezone.utc) - latest_timestamp).total_seconds() / 86400
                    self.log(f"Latest signal: {age_days:.1f} days ago", 'warning')
        else:
            self.log("Cannot verify signals freshness", 'warning')

        # 6. Check environment variables
        self.log("\nChecking environment configuration...", 'info')
        required_env_vars = ['DATABASE_URL', 'THE_ODDS_API_KEY']
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]

        if missing_vars:
            self.log(f"Missing env vars: {', '.join(missing_vars)}", 'error')
            self.checks_failed += 1
        else:
            self.log("Environment variables configured", 'success')
            self.checks_passed += 1

        # Summary
        total_checks = self.checks_passed + self.checks_failed
        self.log(f"\n=== Health Check Summary ===", 'info')
        self.log(f"Passed: {self.checks_passed}/{total_checks}", 'success')

        if self.checks_failed > 0:
            self.log(f"Failed: {self.checks_failed}/{total_checks}", 'error')
            return False

        self.log("\n✅ System health: OK", 'success')
        return True


def main():
    parser = argparse.ArgumentParser(description='System health check')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    # Run health checks
    checker = HealthChecker(verbose=args.verbose)

    try:
        success = checker.run_health_checks()

        # Exit with appropriate code
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\nHealth check interrupted")
        sys.exit(2)
    except Exception as e:
        print(f"\n❌ Fatal error during health check: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(3)


if __name__ == '__main__':
    main()
