"""
The Odds API Provider

Official API for sports betting odds data.
Documentation: https://the-odds-api.com/liveapi/guides/v4/

Rate Limits (free tier):
- 500 requests/month
- ~16 requests/day
- Recommend: Call every 15-30 minutes during game days
"""

import os
import time
from typing import TypedDict, List, Optional, Dict
from datetime import datetime, timezone
import requests


class NormalizedMarketRow(TypedDict):
    """Normalized odds data row for database insertion."""
    league: str
    game_time: str  # ISO format
    home_team: str
    away_team: str
    market_type: str  # moneyline|spread|total|prop
    selection: str  # e.g., 'NE Patriots +3.5' or 'Over 45.5'
    book: str
    price: int  # American odds
    pulled_at: str  # ISO format


class TheOddsAPIProvider:
    """Provider for The Odds API."""

    # Sport mapping: our league codes -> The Odds API sport keys
    SPORT_MAPPING = {
        'nfl': 'americanfootball_nfl',
        'nba': 'basketball_nba',
        'nhl': 'icehockey_nhl',
        'mlb': 'baseball_mlb',
        'ncaaf': 'americanfootball_ncaaf',
        'ncaab': 'basketball_ncaab'
    }

    # Book mapping: The Odds API keys -> our book names
    BOOK_MAPPING = {
        'draftkings': 'draftkings',
        'fanduel': 'fanduel',
        'williamhill_us': 'caesars',  # William Hill = Caesars
        'betmgm': 'betmgm',
        'pointsbetus': 'pointsbet',
        'bovada': 'bovada',
        'mybookieag': 'mybookie'
    }

    def __init__(self, api_key: str, rate_limit_seconds: int = 6, db_connection=None):
        """
        Initialize The Odds API provider.

        Args:
            api_key: The Odds API key
            rate_limit_seconds: Minimum seconds between requests (default 6 = 10 req/min)
            db_connection: Optional database connection for usage logging
        """
        if not api_key:
            raise ValueError("THE_ODDS_API_KEY is required")

        self.api_key = api_key
        self.base_url = 'https://api.the-odds-api.com/v4'
        self.rate_limit_seconds = rate_limit_seconds
        self.last_request_time = 0
        self.db = db_connection

    def _rate_limited_request(self, url: str, params: Dict, league: str = None) -> Optional[Dict]:
        """Make a rate-limited API request with usage logging."""
        # Enforce rate limit
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_seconds:
            time.sleep(self.rate_limit_seconds - elapsed)

        # Add API key to params
        params['apiKey'] = self.api_key

        headers = {
            'User-Agent': 'sports-edge/0.1.0 (research use)',
            'Accept': 'application/json'
        }

        response_status = None
        response_message = None
        success = False
        remaining = None
        used = None

        try:
            response = requests.get(url, params=params, headers=headers, timeout=15)
            self.last_request_time = time.time()
            response_status = response.status_code

            # Check remaining quota
            remaining = response.headers.get('x-requests-remaining')
            used = response.headers.get('x-requests-used')
            if remaining:
                print(f"[TheOddsAPI] Requests remaining: {remaining}/{used}")

            if response.status_code == 200:
                success = True
                self._log_api_usage(url, league, 1, remaining, used, response_status, None, success)
                return response.json()
            elif response.status_code == 401:
                # Check if it's quota exhaustion (common 401 cause)
                response_message = response.text
                if 'quota' in response.text.lower() or 'usage' in response.text.lower():
                    self._log_api_usage(url, league, 1, remaining, used, response_status, response_message, success)
                    raise ValueError(f"🚨 CRITICAL: API QUOTA EXHAUSTED 🚨\n{response.text}\nUpgrade at: https://the-odds-api.com/liveapi/guides/v4/#pricing")
                self._log_api_usage(url, league, 1, remaining, used, response_status, response_message, success)
                raise ValueError(f"Invalid API key: {response.text}")
            elif response.status_code == 429:
                response_message = response.text
                self._log_api_usage(url, league, 1, remaining, used, response_status, response_message, success)
                raise ValueError(f"Rate limit exceeded: {response.text}")
            else:
                response_message = response.text[:200]
                self._log_api_usage(url, league, 1, remaining, used, response_status, response_message, success)
                print(f"[TheOddsAPI] HTTP {response.status_code}: {response.text[:200]}")
                return None

        except requests.exceptions.RequestException as e:
            response_message = str(e)
            self._log_api_usage(url, league, 1, remaining, used, response_status, response_message, success)
            print(f"[TheOddsAPI] Request error: {e}")
            return None

    def _log_api_usage(self, url, league, credits, remaining, used, status, message, success):
        """Log API usage to database for quota tracking."""
        if not self.db:
            return

        try:
            endpoint = url.replace(self.base_url, '')  # Remove base URL
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO api_usage_log (
                            provider, endpoint, league, credits_used,
                            credits_remaining, credits_total,
                            response_status, response_message, success
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        'theoddsapi', endpoint, league, credits,
                        int(remaining) if remaining else None,
                        int(used) if used else None,
                        status, message, success
                    ))
        except Exception as e:
            print(f"[TheOddsAPI] Failed to log API usage: {e}")

    def fetch_odds(
        self,
        league: str,
        markets: List[str] = None,
        regions: str = 'us'
    ) -> List[NormalizedMarketRow]:
        """
        Fetch odds for a league.

        Args:
            league: League code (nfl, nba, nhl, etc.)
            markets: List of markets to fetch (default: h2h, spreads, totals)
            regions: Regions to fetch (default: us)

        Returns:
            List of normalized market rows
        """
        if markets is None:
            markets = ['h2h', 'spreads', 'totals']

        # Map league code to The Odds API sport key
        sport_key = self.SPORT_MAPPING.get(league.lower())
        if not sport_key:
            raise ValueError(f"Unsupported league: {league}")

        url = f"{self.base_url}/sports/{sport_key}/odds/"
        params = {
            'regions': regions,
            'markets': ','.join(markets),
            'oddsFormat': 'american',
            'dateFormat': 'iso'
        }

        print(f"[TheOddsAPI] Fetching {league.upper()} odds for markets: {markets}")

        data = self._rate_limited_request(url, params, league=league)
        if not data:
            return []

        # Normalize response
        return self._normalize_response(data, league)

    def _normalize_response(self, data: List[Dict], league: str) -> List[NormalizedMarketRow]:
        """Transform The Odds API response to normalized schema."""
        rows = []
        pulled_at = datetime.now(timezone.utc).isoformat()

        for event in data:
            game_time = event.get('commence_time')
            home_team = event.get('home_team')
            away_team = event.get('away_team')

            for bookmaker in event.get('bookmakers', []):
                book_key = bookmaker.get('key')
                book_name = self.BOOK_MAPPING.get(book_key, book_key)

                for market in bookmaker.get('markets', []):
                    market_key = market.get('key')  # h2h, spreads, totals
                    market_type = self._map_market_type(market_key)

                    for outcome in market.get('outcomes', []):
                        selection_name = outcome.get('name')
                        price = outcome.get('price')
                        point = outcome.get('point')  # For spreads/totals

                        # Build selection string
                        if point is not None:
                            if market_key == 'spreads':
                                selection = f"{selection_name} {point:+.1f}"
                            elif market_key == 'totals':
                                selection = f"{selection_name} {point:.1f}"
                            else:
                                selection = selection_name
                        else:
                            selection = selection_name

                        rows.append({
                            'league': league,
                            'game_time': game_time,
                            'home_team': home_team,
                            'away_team': away_team,
                            'market_type': market_type,
                            'selection': selection,
                            'book': book_name,
                            'price': int(price),
                            'pulled_at': pulled_at
                        })

        print(f"[TheOddsAPI] Normalized {len(rows)} odds rows")
        return rows

    def _map_market_type(self, api_market_key: str) -> str:
        """Map The Odds API market key to our schema."""
        mapping = {
            'h2h': 'moneyline',
            'spreads': 'spread',
            'totals': 'total',
            'player_points': 'prop',
            'player_rebounds': 'prop',
            'player_assists': 'prop'
        }
        return mapping.get(api_market_key, api_market_key)

    def fetch_player_props(self, league: str, event_id: str = None) -> List[NormalizedMarketRow]:
        """
        Fetch player props (NBA/NFL).

        Note: Player props may require higher API tier or separate endpoint.
        Check The Odds API documentation for availability.
        """
        sport_key = self.SPORT_MAPPING.get(league.lower())
        if not sport_key:
            raise ValueError(f"Unsupported league: {league}")

        # Player props endpoint (if available)
        url = f"{self.base_url}/sports/{sport_key}/events/{event_id}/odds/" if event_id else None

        if not url:
            print(f"[TheOddsAPI] Player props not yet implemented for {league}")
            return []

        # TODO: Implement once player props endpoint is confirmed
        return []


def fetch_odds(league: str, api_key: str = None) -> List[NormalizedMarketRow]:
    """
    Convenience function to fetch odds for a league.

    Args:
        league: League code (nfl, nba, nhl)
        api_key: The Odds API key (defaults to env var)

    Returns:
        List of normalized market rows
    """
    if not api_key:
        api_key = os.getenv('THE_ODDS_API_KEY')

    provider = TheOddsAPIProvider(api_key)
    return provider.fetch_odds(league)
