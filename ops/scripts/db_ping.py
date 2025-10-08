#!/usr/bin/env python3
"""
Database Ping Utility

Quick connectivity test that shows server version and current database.
Useful for debugging connection issues.

Usage:
    python ops/scripts/db_ping.py
    make db-ping
"""

import os
import sys
import time
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment
load_dotenv()


def mask_secret(value: str, show_last: int = 4) -> str:
    """Mask secret value showing only last N characters."""
    if not value or len(value) <= show_last:
        return "xxxxx"
    return f"xxxxx...{value[-show_last:]}"


def parse_db_url(url: str) -> dict:
    """Parse database URL and extract components (mask password)."""
    try:
        parsed = urlparse(url)
        return {
            'host': parsed.hostname or 'unknown',
            'port': parsed.port or 5432,
            'database': parsed.path.lstrip('/') or 'unknown',
            'user': parsed.username or 'unknown',
            'password_masked': mask_secret(parsed.password) if parsed.password else 'none',
        }
    except Exception:
        return {'host': 'unknown', 'port': 'unknown', 'database': 'unknown', 'user': 'unknown'}


def ping_database():
    """Test database connection and print server info."""
    print("🏓 Database Ping\n")
    print("=" * 60)

    # Check environment variable
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL not set")
        print("\nSet it in .env:")
        print("  DATABASE_URL=postgresql://user:pass@host:5432/db")
        return 1

    # Parse and display connection info
    db_info = parse_db_url(db_url)
    print("\n📋 Connection Info:")
    print(f"  Host:     {db_info['host']}")
    print(f"  Port:     {db_info['port']}")
    print(f"  Database: {db_info['database']}")
    print(f"  User:     {db_info['user']}")
    print(f"  Password: {db_info['password_masked']}")

    # Test connection
    print("\n🔌 Testing Connection...")

    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2 not installed")
        print("\nInstall with:")
        print("  pip install psycopg2-binary")
        return 1

    start_time = time.time()

    try:
        # Connect with timeout
        conn = psycopg2.connect(db_url, connect_timeout=5)
        latency_ms = (time.time() - start_time) * 1000

        # Get server version
        cur = conn.cursor()
        cur.execute("SELECT version()")
        version = cur.fetchone()[0]

        # Get current database
        cur.execute("SELECT current_database()")
        current_db = cur.fetchone()[0]

        # Get server time
        cur.execute("SELECT NOW()")
        server_time = cur.fetchone()[0]

        cur.close()
        conn.close()

        # Display results
        print(f"✅ Connection successful ({latency_ms:.1f}ms)")
        print("\n📊 Server Info:")
        print(f"  Version:  {version.split(',')[0]}")  # First part only
        print(f"  Database: {current_db}")
        print(f"  Time:     {server_time}")

        print("\n" + "=" * 60)
        print("✅ Database is reachable and responsive\n")
        return 0

    except psycopg2.OperationalError as e:
        error_msg = str(e)

        print(f"❌ Connection failed\n")
        print(f"Error: {error_msg[:200]}")

        # Provide helpful diagnostics
        print("\n" + "=" * 60)
        print("🔍 Troubleshooting Checklist:")
        print("=" * 60)

        if 'timeout' in error_msg.lower():
            print("\n⏱️  Connection Timeout:")
            print("  • Check if the database server is online")
            print("  • Verify network/firewall allows port 5432")
            print("  • Confirm host/port are correct")
            print("  • Try increasing DB_CONN_OPTS timeout")

        elif 'could not connect' in error_msg.lower() or 'connection refused' in error_msg.lower():
            print("\n🚫 Connection Refused:")
            print("  • Database server may be down")
            print("  • Port 5432 might be blocked")
            print("  • Check if PostgreSQL is running")
            print(f"  • Test with: telnet {db_info['host']} {db_info['port']}")

        elif 'authentication failed' in error_msg.lower() or 'password' in error_msg.lower():
            print("\n🔐 Authentication Failed:")
            print("  • Verify username/password in DATABASE_URL")
            print("  • Check database user permissions")
            print("  • Confirm database name is correct")

        elif 'ssl' in error_msg.lower():
            print("\n🔒 SSL Error:")
            print("  • Try: DB_CONN_OPTS=sslmode=disable (dev only)")
            print("  • Or: DB_CONN_OPTS=sslmode=require")
            print("  • Check if server requires SSL")

        else:
            print("\n🔍 General Checks:")
            print("  • Verify DATABASE_URL format:")
            print("    postgresql://user:pass@host:5432/dbname")
            print("  • Check DB_CONN_OPTS in .env")
            print("  • Test DNS resolution:")
            print(f"    nslookup {db_info['host']}")
            print("  • Check provider status page")

        print("\n💡 Quick Tests:")
        print("  make verify    - Full environment check")
        print("  make db-ping   - This test")
        print(f"  psql \"{mask_secret(db_url, 20)}\" -c \"SELECT 1\"")

        print()
        return 1

    except Exception as e:
        print(f"❌ Unexpected error: {str(e)[:200]}\n")
        return 1


if __name__ == '__main__':
    try:
        exit_code = ping_database()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Ping interrupted")
        sys.exit(2)
