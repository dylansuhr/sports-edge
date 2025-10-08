#!/usr/bin/env python3
"""
Odds ETL Script - ToS-compliant data ingestion for DraftKings & Caesars

This script fetches pregame odds from legal sportsbooks with read-only access.
Respects robots.txt and ToS. Includes manual CSV import fallback.

Usage:
    python ops/scripts/odds_etl.py --live              # Fetch live odds
    python ops/scripts/odds_etl.py --from-csv path.csv # Import from CSV
"""

import argparse
import csv
import os
import sys
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional
import requests
from dotenv import load_dotenv
import json

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'packages'))

from shared.shared.odds_math import american_to_decimal, implied_probability

# Load environment
load_dotenv()

# Database connection (using environment variable)
DATABASE_URL = os.getenv('DATABASE_URL')

# ToS-Compliant Configuration
USER_AGENT = 'sports-edge-research/0.1.0 (educational use; dylan@example.com)'
RATE_LIMIT_SECONDS = 10  # Minimum seconds between requests
MAX_RETRIES = 3


class OddsAdapter:
    """Base class for sportsbook odds adapters."""

    def __init__(self, rate_limit: int = RATE_LIMIT_SECONDS):
        self.rate_limit = rate_limit
        self.last_request_time = 0

    def _rate_limited_request(self, url: str, headers: Dict = None) -> Optional[Dict]:
        """Make a rate-limited HTTP request."""
        # Enforce rate limit
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)

        # Default headers
        if headers is None:
            headers = {}
        headers['User-Agent'] = USER_AGENT

        # Make request with retries
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(url, headers=headers, timeout=15)
                self.last_request_time = time.time()

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Rate limited
                    wait_time = self.rate_limit * (attempt + 1)
                    print(f"Rate limited. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"HTTP {response.status_code}: {response.text[:200]}")
                    return None

            except requests.exceptions.RequestException as e:
                print(f"Request error (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)

        return None

    def fetch_odds(self, sport: str = 'nfl') -> List[Dict]:
        """Fetch odds for a given sport. Override in subclass."""
        raise NotImplementedError


class DraftKingsAdapter(OddsAdapter):
    """
    DraftKings odds adapter.

    NOTE: This is a PLACEHOLDER implementation. DraftKings does not provide
    a public API. In production, you must either:
    1. Use an official data provider (The Odds API, etc.)
    2. Manually export data and use CSV import
    3. Use a ToS-compliant third-party aggregator

    DO NOT scrape DraftKings website - it violates their ToS.
    """

    def fetch_odds(self, sport: str = 'nfl') -> List[Dict]:
        """
        Placeholder for DraftKings odds fetching.

        In production, replace with:
        - Official API integration (if available)
        - Manual CSV export workflow
        - Licensed data provider
        """
        print("[DraftKings] No official API available. Use manual CSV import.")
        print("[DraftKings] See docs for CSV format: data/sample_odds.csv")
        return []


class CaesarsAdapter(OddsAdapter):
    """
    Caesars odds adapter.

    NOTE: This is a PLACEHOLDER implementation. Caesars does not provide
    a public API for odds. Same restrictions as DraftKings apply.
    """

    def fetch_odds(self, sport: str = 'nfl') -> List[Dict]:
        """
        Placeholder for Caesars odds fetching.

        In production, replace with licensed data provider or manual CSV import.
        """
        print("[Caesars] No official API available. Use manual CSV import.")
        print("[Caesars] See docs for CSV format: data/sample_odds.csv")
        return []


class TheOddsAPIAdapter(OddsAdapter):
    """
    The Odds API adapter (ToS-compliant third-party aggregator).

    Requires API key: https://the-odds-api.com/
    Free tier: 500 requests/month
    """

    def __init__(self, api_key: str):
        super().__init__(rate_limit=2)  # Max 10 requests/minute on free tier
        self.api_key = api_key
        self.base_url = 'https://api.the-odds-api.com/v4'

    def fetch_odds(self, sport: str = 'americanfootball_nfl') -> List[Dict]:
        """Fetch odds from The Odds API."""
        url = f"{self.base_url}/sports/{sport}/odds/"
        params = {
            'apiKey': self.api_key,
            'regions': 'us',
            'markets': 'h2h,spreads,totals',
            'oddsFormat': 'american',
            'bookmakers': 'draftkings,williamhill_us'  # williamhill = Caesars
        }

        full_url = f"{url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
        data = self._rate_limited_request(full_url)

        if not data:
            return []

        # Transform to our schema
        return self._transform_odds_api_response(data)

    def _transform_odds_api_response(self, data: List[Dict]) -> List[Dict]:
        """Transform The Odds API response to our schema."""
        odds_snapshots = []
        fetched_at = datetime.now(timezone.utc)

        for game in data:
            game_id = game.get('id')
            home_team = game.get('home_team')
            away_team = game.get('away_team')
            commence_time = game.get('commence_time')

            for bookmaker in game.get('bookmakers', []):
                sportsbook = bookmaker.get('key')

                for market in bookmaker.get('markets', []):
                    market_type = market.get('key')  # h2h, spreads, totals

                    for outcome in market.get('outcomes', []):
                        team_name = outcome.get('name')
                        odds_american = outcome.get('price')
                        line_value = outcome.get('point')  # For spreads/totals

                        odds_snapshots.append({
                            'game_external_id': game_id,
                            'home_team': home_team,
                            'away_team': away_team,
                            'scheduled_at': commence_time,
                            'sportsbook': sportsbook,
                            'market_type': market_type,
                            'team_or_outcome': team_name,
                            'line_value': line_value,
                            'odds_american': odds_american,
                            'odds_decimal': american_to_decimal(odds_american),
                            'implied_probability': implied_probability(odds_american),
                            'fetched_at': fetched_at.isoformat()
                        })

        return odds_snapshots


def import_from_csv(csv_path: str) -> List[Dict]:
    """
    Import odds from CSV file (manual export fallback).

    CSV format:
        game_id, home_team, away_team, scheduled_at, sportsbook, market_type,
        team_or_outcome, line_value, odds_american
    """
    odds_snapshots = []
    fetched_at = datetime.now(timezone.utc)

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            odds_american = int(row['odds_american'])
            line_value = float(row['line_value']) if row.get('line_value') else None

            odds_snapshots.append({
                'game_external_id': row['game_id'],
                'home_team': row['home_team'],
                'away_team': row['away_team'],
                'scheduled_at': row['scheduled_at'],
                'sportsbook': row['sportsbook'],
                'market_type': row['market_type'],
                'team_or_outcome': row.get('team_or_outcome', ''),
                'line_value': line_value,
                'odds_american': odds_american,
                'odds_decimal': american_to_decimal(odds_american),
                'implied_probability': implied_probability(odds_american),
                'fetched_at': fetched_at.isoformat()
            })

    return odds_snapshots


def save_to_database(odds_snapshots: List[Dict]):
    """Save odds snapshots to Postgres."""
    # TODO: Implement database insert using psycopg2 or SQLAlchemy
    # For now, just print summary
    print(f"\n[DB] Would insert {len(odds_snapshots)} odds snapshots")

    if odds_snapshots:
        print(f"[DB] Sample: {json.dumps(odds_snapshots[0], indent=2)}")

    # Placeholder for actual database logic:
    # import psycopg2
    # conn = psycopg2.connect(DATABASE_URL)
    # cur = conn.cursor()
    # for snapshot in odds_snapshots:
    #     cur.execute("""
    #         INSERT INTO odds_snapshots (game_id, sportsbook, market_id, ...)
    #         VALUES (%s, %s, %s, ...)
    #     """, (...))
    # conn.commit()
    # conn.close()


def main():
    parser = argparse.ArgumentParser(description='Fetch and store sportsbook odds (ToS-compliant)')
    parser.add_argument('--live', action='store_true', help='Fetch live odds from API')
    parser.add_argument('--from-csv', type=str, help='Import from CSV file')
    parser.add_argument('--sport', type=str, default='nfl', help='Sport to fetch (default: nfl)')
    parser.add_argument('--api', type=str, default='the-odds-api',
                        choices=['the-odds-api', 'draftkings', 'caesars'],
                        help='Data source to use')

    args = parser.parse_args()

    if args.from_csv:
        print(f"[ETL] Importing from CSV: {args.from_csv}")
        odds_snapshots = import_from_csv(args.from_csv)
    elif args.live:
        print(f"[ETL] Fetching live odds for {args.sport} from {args.api}...")

        if args.api == 'the-odds-api':
            api_key = os.getenv('THE_ODDS_API_KEY')
            if not api_key:
                print("[ERROR] THE_ODDS_API_KEY not set in .env")
                sys.exit(1)

            adapter = TheOddsAPIAdapter(api_key)
            odds_snapshots = adapter.fetch_odds(sport='americanfootball_nfl')
        elif args.api == 'draftkings':
            adapter = DraftKingsAdapter()
            odds_snapshots = adapter.fetch_odds(sport=args.sport)
        elif args.api == 'caesars':
            adapter = CaesarsAdapter()
            odds_snapshots = adapter.fetch_odds(sport=args.sport)
    else:
        print("[ERROR] Must specify --live or --from-csv")
        sys.exit(1)

    # Save to database
    if odds_snapshots:
        save_to_database(odds_snapshots)
        print(f"\n[SUCCESS] Processed {len(odds_snapshots)} odds snapshots")
    else:
        print("\n[WARNING] No odds data fetched")


if __name__ == '__main__':
    main()
