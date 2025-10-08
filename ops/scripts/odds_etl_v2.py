#!/usr/bin/env python3
"""
Odds ETL Script (API-Only Mode - No CSV)

Fetches odds from The Odds API and writes to Postgres.
Fully automated with proper error handling and rate limiting.

Usage:
    python ops/scripts/odds_etl_v2.py
    python ops/scripts/odds_etl_v2.py --leagues nfl,nba
"""

import argparse
import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'packages'))

from providers.theoddsapi import TheOddsAPIProvider, NormalizedMarketRow
from shared.shared.db import get_db
from shared.shared.odds_math import american_to_decimal, implied_probability

# Load environment
load_dotenv()


def check_env_vars():
    """Validate required environment variables."""
    use_api = os.getenv('USE_API', 'true').lower() == 'true'

    if use_api:
        required_vars = ['DATABASE_URL', 'THE_ODDS_API_KEY']
        missing = [var for var in required_vars if not os.getenv(var)]

        if missing:
            print(f"[ERROR] Missing required environment variables: {', '.join(missing)}")
            print("[ERROR] Set USE_API=true requires THE_ODDS_API_KEY and DATABASE_URL")
            sys.exit(1)

    return use_api


def parse_line_value(selection: str, market_type: str) -> float:
    """
    Parse line value from selection string.

    Args:
        selection: Selection string (e.g., "Team Name +7.5", "Over 45.5")
        market_type: Market type (spread, total, moneyline)

    Returns:
        Line value as float, or None if not applicable
    """
    import re

    if market_type not in ['spread', 'total']:
        return None

    # Extract numeric value from selection string
    # Examples:
    # "Philadelphia Eagles -7.5" -> -7.5
    # "Over 45.5" -> 45.5
    # "Under 45.5" -> 45.5

    match = re.search(r'([+-]?\d+\.?\d*)', selection)
    if match:
        line = float(match.group(1))

        # For totals, store the line as positive (we track Over/Under separately)
        if market_type == 'total':
            return abs(line)

        # For spreads, preserve sign
        return line

    return None


def process_odds_for_league(league: str, provider: TheOddsAPIProvider, db) -> int:
    """
    Fetch and store odds for a single league.

    Returns:
        Number of odds snapshots inserted
    """
    print(f"\n[ETL] Processing {league.upper()}...")

    # Fetch odds from API
    try:
        market_rows = provider.fetch_odds(league)
    except Exception as e:
        print(f"[ETL] Failed to fetch odds for {league}: {e}")
        return 0

    if not market_rows:
        print(f"[ETL] No odds data for {league}")
        return 0

    print(f"[ETL] Fetched {len(market_rows)} market rows for {league}")

    # Group by game to batch insert
    games_by_id = {}
    for row in market_rows:
        game_key = (row['home_team'], row['away_team'], row['game_time'])
        if game_key not in games_by_id:
            games_by_id[game_key] = []
        games_by_id[game_key].append(row)

    total_snapshots = 0

    # Process each game
    for (home_team, away_team, game_time), game_rows in games_by_id.items():
        try:
            # Upsert teams
            home_team_id = db.upsert_team(
                external_id=f"{league}_{home_team.lower().replace(' ', '_')}",
                name=home_team,
                abbreviation=home_team[:3].upper(),
                sport=league
            )

            away_team_id = db.upsert_team(
                external_id=f"{league}_{away_team.lower().replace(' ', '_')}",
                name=away_team,
                abbreviation=away_team[:3].upper(),
                sport=league
            )

            # Upsert game
            game_external_id = f"{league}_{home_team}_{away_team}_{game_time}".replace(' ', '_').replace(':', '')
            game_id = db.upsert_game(
                external_id=game_external_id,
                sport=league,
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                scheduled_at=game_time
            )

            # Process each market row
            snapshots = []
            for row in game_rows:
                # Upsert market
                market_id = db.upsert_market(
                    name=row['market_type'],
                    category='game',  # TODO: distinguish player props
                    sport=league
                )

                # Parse line value from selection string
                line_value = parse_line_value(row['selection'], row['market_type'])

                # Prepare snapshot
                odds_decimal = american_to_decimal(row['price'])
                implied_prob = implied_probability(row['price'])

                snapshots.append({
                    'game_id': game_id,
                    'market_id': market_id,
                    'sportsbook': row['book'],
                    'selection': row['selection'],  # Store which side (team/over/under)
                    'line_value': line_value,
                    'odds_american': row['price'],
                    'odds_decimal': odds_decimal,
                    'implied_probability': implied_prob,
                    'fetched_at': row['pulled_at']
                })

            # Bulk insert odds snapshots
            if snapshots:
                db.bulk_insert_odds_snapshots(snapshots)
                total_snapshots += len(snapshots)

        except Exception as e:
            print(f"[ETL] Error processing game {home_team} vs {away_team}: {e}")
            continue

    print(f"[ETL] Inserted {total_snapshots} odds snapshots for {league}")
    return total_snapshots


def main():
    parser = argparse.ArgumentParser(description='Fetch and store sports odds (API-only mode)')
    parser.add_argument('--leagues', type=str, help='Comma-separated leagues (default: from LEAGUES env var)')

    args = parser.parse_args()

    # Check environment
    use_api = check_env_vars()
    if not use_api:
        print("[ERROR] USE_API=false is not supported. This script is API-only.")
        sys.exit(1)

    # Get leagues to process
    leagues_str = args.leagues or os.getenv('LEAGUES', 'nfl')
    leagues = [l.strip() for l in leagues_str.split(',')]

    print(f"[ETL] Starting odds ETL for leagues: {', '.join(leagues)}")
    print(f"[ETL] Timestamp: {datetime.now(timezone.utc).isoformat()}")

    # Initialize provider
    api_key = os.getenv('THE_ODDS_API_KEY')
    provider = TheOddsAPIProvider(api_key, rate_limit_seconds=6)

    # Initialize database
    db = get_db()

    # Check for core tables before proceeding
    print(f"\n[ETL] Checking database schema...")
    all_exist, missing = db.check_core_tables(['teams', 'games', 'markets', 'odds_snapshots'])

    if not all_exist:
        print(f"[ERROR] Required database tables are missing: {', '.join(missing)}")
        print(f"[ERROR] Run migrations to create tables:")
        print(f"[ERROR]   make migrate")
        print(f"[ERROR]   OR: psql $DATABASE_URL -f infra/migrations/0001_init.sql")
        sys.exit(1)

    print(f"[ETL] ✓ Database schema verified")

    # Process each league
    total_snapshots = 0
    for league in leagues:
        count = process_odds_for_league(league, provider, db)
        total_snapshots += count

    # Summary
    print(f"\n[ETL] ===== SUMMARY =====")
    print(f"[ETL] Leagues processed: {len(leagues)}")
    print(f"[ETL] Total odds snapshots: {total_snapshots}")
    print(f"[ETL] Status: {'SUCCESS' if total_snapshots > 0 else 'NO DATA'}")


if __name__ == '__main__':
    main()
