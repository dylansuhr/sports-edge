#!/usr/bin/env python3
"""
Verification script to test sports-edge setup.

Usage:
    python ops/scripts/verify_setup.py
"""

import os
import sys

# Load .env file at the start
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed. Environment variables from .env won't be loaded.")
    print("   Install with: pip install python-dotenv")

def mask_secret(value: str, show_last: int = 4) -> str:
    """Mask secret value showing only last N characters."""
    if not value or len(value) <= show_last:
        return "xxxxx"
    return f"xxxxx...{value[-show_last:]}"

def check_env_vars():
    """Check required environment variables."""
    print("🔍 Checking environment variables...")

    # Required variables (name, is_secret)
    required = [
        ('DATABASE_URL', True),
        ('DATABASE_READONLY_URL', True),
        ('USE_API', False),
        ('DATA_PROVIDER', False),
        ('THE_ODDS_API_KEY', True),
        ('LEAGUES', False),
        ('EDGE_SIDES', False),
        ('EDGE_PROPS', False),
        ('KELLY_FRACTION', False),
        ('MAX_STAKE_PCT', False),
        ('BANKROLL', False),
    ]

    optional = [
        ('SLACK_WEBHOOK_URL', True),
        ('ENABLE_DK', False),
        ('ENABLE_CAESARS', False),
        ('NEXT_PUBLIC_APP_NAME', False),
    ]

    missing = []
    print("\n  Required:")
    for var, is_secret in required:
        value = os.getenv(var)
        if not value:
            missing.append(var)
            print(f"    ❌ {var} - MISSING")
        else:
            display = mask_secret(value) if is_secret else value
            print(f"    ✅ {var} = {display}")

    print("\n  Optional:")
    for var, is_secret in optional:
        value = os.getenv(var)
        if not value:
            print(f"    ⚠️  {var} - NOT SET")
        else:
            display = mask_secret(value) if is_secret else value
            print(f"    ✅ {var} = {display}")

    return len(missing) == 0

def check_python_packages():
    """Check if required Python packages are installed."""
    print("\n🔍 Checking Python packages...")

    packages = [
        'pandas',
        'numpy',
        'scipy',
        'sklearn',
        'xgboost',
        'statsmodels',
        'requests',
        'pydantic',
        'dotenv',
        'psycopg2'
    ]

    missing = []
    errors = []
    for pkg in packages:
        try:
            if pkg == 'sklearn':
                __import__('sklearn')
            elif pkg == 'dotenv':
                __import__('dotenv')
            else:
                __import__(pkg)
            print(f"  ✅ {pkg}")
        except ImportError:
            missing.append(pkg)
            print(f"  ❌ {pkg} - NOT INSTALLED")
        except Exception as e:
            errors.append((pkg, str(e)[:80]))
            print(f"  ⚠️  {pkg} - IMPORT ERROR")

    if missing:
        print(f"\n  Run: pip install {' '.join(missing)}")

    if errors:
        print(f"\n  ⚠️  Some packages have import issues:")
        for pkg, err in errors:
            print(f"     {pkg}: {err}")
        print(f"\n  For xgboost on Mac: brew install libomp")

    return len(missing) == 0

def check_database_connection():
    """Test database connection with enhanced diagnostics."""
    print("\n🔍 Checking database connection...")

    try:
        import psycopg2
    except ImportError:
        print("  ⚠️  psycopg2 not installed, skipping database test")
        return True

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # Already warned about dotenv earlier

    try:
        from urllib.parse import urlparse
        import socket
    except ImportError:
        pass

    try:
        db_url = os.getenv('DATABASE_URL')

        if not db_url:
            print("  ⚠️  DATABASE_URL not set, skipping connection test")
            return True

        # Parse database URL
        try:
            parsed = urlparse(db_url)
            host = parsed.hostname or 'unknown'
            port = parsed.port or 5432
            database = parsed.path.lstrip('/') or 'unknown'

            print(f"  📍 Target: {host}:{port}/{database}")

            # Test DNS resolution
            try:
                addr_info = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
                resolved_ips = set(addr[4][0] for addr in addr_info)
                print(f"  🌐 DNS resolved: {', '.join(list(resolved_ips)[:3])}")
            except socket.gaierror:
                print(f"  ⚠️  DNS resolution failed for {host}")
            except Exception:
                pass  # Skip DNS check on error

        except Exception:
            print("  ⚠️  Could not parse DATABASE_URL")

        # Add connection timeout
        conn = psycopg2.connect(db_url, connect_timeout=5)
        cur = conn.cursor()
        cur.execute('SELECT 1')
        result = cur.fetchone()
        cur.close()
        conn.close()

        print("  ✅ Database connection successful")
        return True

    except psycopg2.OperationalError as e:
        error_msg = str(e)
        print(f"  ❌ Database connection failed")

        # Print diagnostic checklist
        print("\n  📋 Troubleshooting checklist:")
        print("     □ Check sslmode setting (DB_CONN_OPTS in .env)")
        print("     □ Verify port 5432 is open (not blocked by firewall)")
        print("     □ Confirm your IP is in database allowlist")
        print("     □ Check database provider status page")
        print("     □ Test with: make db-ping")

        if 'timeout' in error_msg.lower():
            print("\n  ⏱️  Timeout detected - likely network/firewall issue")
        elif 'ssl' in error_msg.lower():
            print("\n  🔒 SSL issue - try setting DB_CONN_OPTS=sslmode=disable")
        elif 'authentication' in error_msg.lower() or 'password' in error_msg.lower():
            print("\n  🔐 Authentication failed - check username/password")

        return False

    except Exception as e:
        print(f"  ❌ Database connection failed: {str(e)[:100]}")
        print("\n  💡 Run: make db-ping (for detailed diagnostics)")
        return False

def check_file_structure():
    """Verify key files exist."""
    print("\n🔍 Checking file structure...")

    required_files = [
        'infra/migrations/0001_init.sql',
        'ops/scripts/odds_etl.py',
        'ops/scripts/generate_signals.py',
        'ops/scripts/settle_results.py',
        'packages/models/models/features.py',
        'packages/models/models/prop_models.py',
        'packages/shared/shared/odds_math.py',
        '.env.template'
    ]

    missing = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            missing.append(file_path)
            print(f"  ❌ {file_path} - MISSING")

    return len(missing) == 0

def test_odds_math():
    """Test odds math utilities."""
    print("\n🔍 Testing odds math utilities...")

    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'packages'))
        from shared.shared.odds_math import (
            american_to_decimal,
            implied_probability,
            calculate_edge,
            recommended_stake
        )

        # Test American to Decimal
        decimal = american_to_decimal(-110)
        assert abs(decimal - 1.909) < 0.01, "american_to_decimal failed"

        # Test implied probability
        prob = implied_probability(-110)
        assert abs(prob - 0.5238) < 0.01, "implied_probability failed"

        # Test edge calculation
        edge = calculate_edge(0.55, 0.52)
        assert abs(edge - 3.0) < 0.1, "calculate_edge failed"

        # Test stake recommendation
        stake = recommended_stake(0.55, -110, 1000.0)
        assert stake > 0 and stake < 100, "recommended_stake failed"

        print("  ✅ All odds math tests passed")
        return True

    except Exception as e:
        print(f"  ❌ Odds math tests failed: {e}")
        return False

def main():
    """Run all verification checks."""
    print("=" * 60)
    print("SPORTS EDGE SETUP VERIFICATION")
    print("=" * 60)

    checks = [
        ("Environment Variables", check_env_vars),
        ("Python Packages", check_python_packages),
        ("File Structure", check_file_structure),
        ("Odds Math Library", test_odds_math),
        ("Database Connection", check_database_connection)
    ]

    results = {}
    for name, check_func in checks:
        results[name] = check_func()

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:30} {status}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n🎉 All checks passed! Setup is complete.\n")
        print("Next steps:")
        print("  1. Run: python ops/scripts/odds_etl.py --from-csv data/sample_odds.csv")
        print("  2. Run: python ops/scripts/generate_signals.py")
        print("  3. Start dashboard: cd apps/dashboard && npm run dev")
    else:
        print("\n⚠️  Some checks failed. Review errors above.\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
