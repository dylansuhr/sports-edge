"""
Game Results Provider

Fetches final scores and player stats for settlement.
Can use The Odds API (scores endpoint) or other data sources.
"""

import os
import time
from typing import TypedDict, List, Optional, Dict
from datetime import datetime, date, timezone
import requests


class GameResult(TypedDict):
    """Game result with final score."""
    league: str
    game_time: str  # ISO format
    game_id: str  # External ID from provider
    home_team: str
    away_team: str
    final_home: int
    final_away: int
    status: str  # final, in_progress, scheduled


class PlayerStatLine(TypedDict):
    """Player stat line for prop settlement."""
    game_id: str
    player_name: str
    team: str
    stat_type: str  # points, rebounds, assists, touchdowns, etc.
    stat_value: float


class ResultsProvider:
    """Provider for game results and scores."""

    SPORT_MAPPING = {
        'nfl': 'americanfootball_nfl',
        'nba': 'basketball_nba',
        'nhl': 'icehockey_nhl',
        'mlb': 'baseball_mlb'
    }

    def __init__(self, api_key: str = None, rate_limit_seconds: int = 6):
        """
        Initialize results provider.

        Args:
            api_key: The Odds API key (for scores endpoint)
            rate_limit_seconds: Minimum seconds between requests
        """
        self.api_key = api_key or os.getenv('THE_ODDS_API_KEY')
        self.base_url = 'https://api.the-odds-api.com/v4'
        self.rate_limit_seconds = rate_limit_seconds
        self.last_request_time = 0

    def _rate_limited_request(self, url: str, params: Dict) -> Optional[Dict]:
        """Make a rate-limited API request."""
        # Enforce rate limit
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_seconds:
            time.sleep(self.rate_limit_seconds - elapsed)

        # Add API key to params
        if self.api_key:
            params['apiKey'] = self.api_key

        headers = {
            'User-Agent': 'sports-edge/0.1.0 (research use)',
            'Accept': 'application/json'
        }

        try:
            response = requests.get(url, params=params, headers=headers, timeout=15)
            self.last_request_time = time.time()

            if response.status_code == 200:
                return response.json()
            else:
                print(f"[Results] HTTP {response.status_code}: {response.text[:200]}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"[Results] Request error: {e}")
            return None

    def fetch_results(
        self,
        league: str,
        days_from: int = 1
    ) -> List[GameResult]:
        """
        Fetch completed game results.

        Args:
            league: League code (nfl, nba, nhl)
            days_from: How many days ago to fetch results (default: 1 = yesterday)

        Returns:
            List of game results
        """
        sport_key = self.SPORT_MAPPING.get(league.lower())
        if not sport_key:
            raise ValueError(f"Unsupported league: {league}")

        # The Odds API scores endpoint
        url = f"{self.base_url}/sports/{sport_key}/scores/"
        params = {
            'daysFrom': days_from,
            'dateFormat': 'iso'
        }

        print(f"[Results] Fetching {league.upper()} results from last {days_from} day(s)")

        data = self._rate_limited_request(url, params)
        if not data:
            return []

        # Parse results
        results = []
        for event in data:
            # Only include completed games
            if not event.get('completed'):
                continue

            game_id = event.get('id')
            game_time = event.get('commence_time')
            home_team = event.get('home_team')
            away_team = event.get('away_team')

            # Extract scores
            scores = event.get('scores')
            if not scores or len(scores) < 2:
                continue

            # Find home and away scores
            home_score = None
            away_score = None

            for score in scores:
                team_name = score.get('name')
                team_score = score.get('score')

                if team_score is None:
                    continue

                if team_name == home_team:
                    home_score = int(team_score)
                elif team_name == away_team:
                    away_score = int(team_score)

            if home_score is not None and away_score is not None:
                results.append({
                    'league': league,
                    'game_time': game_time,
                    'game_id': game_id,
                    'home_team': home_team,
                    'away_team': away_team,
                    'final_home': home_score,
                    'final_away': away_score,
                    'status': 'final'
                })

        print(f"[Results] Found {len(results)} completed games")
        return results

    def fetch_player_stats(
        self,
        league: str,
        game_id: str
    ) -> List[PlayerStatLine]:
        """
        Fetch player stats for a game.

        Note: The Odds API does not provide player stats.
        You would need to use a different provider (e.g., ESPN API, NBA API, NFL API)
        or scrape box scores (ToS-compliant sources only).

        This is a placeholder for future implementation.
        """
        print(f"[Results] Player stats not yet implemented for {league}")

        # TODO: Implement using appropriate data source
        # Options:
        # 1. ESPN API (free but limited)
        # 2. NBA/NFL official stats APIs
        # 3. Premium data providers (Sportradar, Stats Perform)

        return []


def fetch_results(league: str, days_from: int = 1) -> List[GameResult]:
    """
    Convenience function to fetch game results.

    Args:
        league: League code (nfl, nba, nhl)
        days_from: How many days ago to fetch results

    Returns:
        List of game results
    """
    provider = ResultsProvider()
    return provider.fetch_results(league, days_from)


def fetch_yesterdays_results(league: str) -> List[GameResult]:
    """Fetch results from yesterday (for nightly settlement)."""
    return fetch_results(league, days_from=1)
