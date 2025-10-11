"""
NFL Feature Generation - Team Strength & Context Features

Generates features for NFL betting models:
- ELO-style team strength ratings
- Rest days & schedule context
- Injury impact (placeholder for manual tracking)
- Weather conditions (for outdoor games)
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta


class NFLFeatureGenerator:
    """Generate betting features for NFL games."""

    def __init__(self, k_factor: float = 20.0, home_advantage: float = 25.0):
        """
        Initialize NFL feature generator.

        Args:
            k_factor: ELO K-factor (rating volatility)
            home_advantage: Home field advantage in ELO points
        """
        self.k_factor = k_factor
        self.home_advantage = home_advantage
        self.team_elos = {}  # team_id -> current ELO rating

        # Offensive/Defensive ratings (points per game above/below average)
        self.offensive_ratings = {}  # team_id -> offensive rating
        self.defensive_ratings = {}  # team_id -> defensive rating

    def initialize_elos(self, teams: list, default_elo: float = 1500.0):
        """Initialize all teams to default ELO rating."""
        for team_id in teams:
            self.team_elos[team_id] = default_elo

    def expected_score(self, elo_a: float, elo_b: float) -> float:
        """Calculate expected score (win probability) using ELO formula."""
        return 1 / (1 + 10 ** ((elo_b - elo_a) / 400))

    def update_elo(
        self,
        team_id: int,
        opponent_id: int,
        actual_score: float,
        is_home: bool = False
    ) -> float:
        """
        Update team ELO rating after a game.

        Args:
            team_id: Team whose ELO to update
            opponent_id: Opponent team
            actual_score: 1.0 for win, 0.0 for loss, 0.5 for tie
            is_home: Whether team played at home

        Returns:
            New ELO rating for team
        """
        # Get current ELOs
        team_elo = self.team_elos.get(team_id, 1500.0)
        opponent_elo = self.team_elos.get(opponent_id, 1500.0)

        # Apply home advantage
        if is_home:
            team_elo += self.home_advantage

        # Calculate expected score
        expected = self.expected_score(team_elo, opponent_elo)

        # Update ELO
        new_elo = team_elo + self.k_factor * (actual_score - expected)

        # Remove home advantage before storing
        if is_home:
            new_elo -= self.home_advantage

        self.team_elos[team_id] = new_elo
        return new_elo

    def calculate_rest_days(
        self,
        current_game_date: datetime,
        last_game_date: Optional[datetime]
    ) -> int:
        """Calculate days of rest since last game."""
        if last_game_date is None:
            return 7  # Default to standard week rest

        delta = current_game_date - last_game_date
        return max(0, delta.days)

    def rest_advantage(self, team_rest: int, opponent_rest: int) -> float:
        """
        Calculate rest advantage.

        Returns:
            Positive means team has rest advantage, negative means disadvantage
        """
        return (team_rest - opponent_rest) * 0.5

    def weather_impact(
        self,
        is_outdoor: bool,
        temperature: Optional[float] = None,
        wind_speed: Optional[float] = None,
        precipitation: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Calculate weather impact features.

        Args:
            is_outdoor: Whether game is outdoors
            temperature: Temperature in Fahrenheit
            wind_speed: Wind speed in MPH
            precipitation: Precipitation type (rain, snow, none)

        Returns:
            Dictionary of weather features
        """
        features = {
            'is_outdoor': 1.0 if is_outdoor else 0.0,
            'cold_game': 0.0,
            'high_wind': 0.0,
            'precipitation': 0.0
        }

        if not is_outdoor:
            return features

        # Cold weather games (< 32F) tend to favor run-heavy teams
        if temperature is not None and temperature < 32:
            features['cold_game'] = 1.0

        # High wind (> 15 MPH) impacts passing games
        if wind_speed is not None and wind_speed > 15:
            features['high_wind'] = 1.0

        # Precipitation impacts ball handling
        if precipitation and precipitation.lower() in ['rain', 'snow']:
            features['precipitation'] = 1.0

        return features

    def injury_impact(
        self,
        injured_players: list,
        key_positions: list = ['QB', 'RB1', 'WR1', 'LT', 'CB1']
    ) -> float:
        """
        Calculate injury impact score.

        Args:
            injured_players: List of dicts with 'position' and 'impact_score'
            key_positions: Positions considered high-impact

        Returns:
            Injury impact score (0-1 scale, higher = more impact)
        """
        total_impact = 0.0

        for player in injured_players:
            position = player.get('position', '')
            impact = player.get('impact_score', 0.5)  # 0-1 scale

            # Weight QB injuries heavily
            if position == 'QB':
                total_impact += impact * 3.0
            elif position in key_positions:
                total_impact += impact * 1.5
            else:
                total_impact += impact * 0.5

        # Normalize to 0-1 scale
        return min(1.0, total_impact / 5.0)

    def generate_game_features(
        self,
        home_team_id: int,
        away_team_id: int,
        game_date: datetime,
        home_last_game: Optional[datetime] = None,
        away_last_game: Optional[datetime] = None,
        weather: Optional[Dict] = None,
        home_injuries: Optional[list] = None,
        away_injuries: Optional[list] = None
    ) -> pd.Series:
        """
        Generate full feature set for a game.

        Args:
            home_team_id: Home team ID
            away_team_id: Away team ID
            game_date: Game date/time
            home_last_game: Date of home team's last game
            away_last_game: Date of away team's last game
            weather: Weather conditions dict
            home_injuries: List of home team injuries
            away_injuries: List of away team injuries

        Returns:
            Pandas Series with all features
        """
        # ELO ratings
        home_elo = self.team_elos.get(home_team_id, 1500.0)
        away_elo = self.team_elos.get(away_team_id, 1500.0)

        # Apply home advantage to home team
        home_elo_adjusted = home_elo + self.home_advantage

        # Rest days
        home_rest = self.calculate_rest_days(game_date, home_last_game)
        away_rest = self.calculate_rest_days(game_date, away_last_game)
        rest_adv = self.rest_advantage(home_rest, away_rest)

        # Weather
        weather = weather or {}
        weather_features = self.weather_impact(
            is_outdoor=weather.get('is_outdoor', False),
            temperature=weather.get('temperature'),
            wind_speed=weather.get('wind_speed'),
            precipitation=weather.get('precipitation')
        )

        # Injuries
        home_injury_impact = self.injury_impact(home_injuries or [])
        away_injury_impact = self.injury_impact(away_injuries or [])

        # Win probability based on ELO
        win_prob = self.expected_score(home_elo_adjusted, away_elo)

        # Combine features
        features = {
            'home_elo': home_elo,
            'away_elo': away_elo,
            'elo_diff': home_elo_adjusted - away_elo,
            'home_win_prob_elo': win_prob,
            'home_rest_days': home_rest,
            'away_rest_days': away_rest,
            'rest_advantage': rest_adv,
            'home_injury_impact': home_injury_impact,
            'away_injury_impact': away_injury_impact,
            'injury_advantage': away_injury_impact - home_injury_impact,
            **{f'weather_{k}': v for k, v in weather_features.items()}
        }

        return pd.Series(features)

    def update_ratings_from_results(self, results_df: pd.DataFrame):
        """
        Batch update ELO ratings from historical results.

        Args:
            results_df: DataFrame with columns:
                - game_id
                - home_team_id
                - away_team_id
                - home_score
                - away_score
                - game_date
        """
        results_df = results_df.sort_values('game_date')

        for _, row in results_df.iterrows():
            home_id = row['home_team_id']
            away_id = row['away_team_id']
            home_score = row['home_score']
            away_score = row['away_score']

            # Determine outcome
            if home_score > away_score:
                home_result = 1.0
                away_result = 0.0
            elif home_score < away_score:
                home_result = 0.0
                away_result = 1.0
            else:
                home_result = 0.5
                away_result = 0.5

            # Update ELOs
            self.update_elo(home_id, away_id, home_result, is_home=True)
            self.update_elo(away_id, home_id, away_result, is_home=False)

    def get_team_elo(self, team_id: int) -> float:
        """Get current ELO rating for a team."""
        return self.team_elos.get(team_id, 1500.0)

    def update_offensive_rating(self, team_id: int, points_scored: float, opponent_def_rating: float = 0.0):
        """
        Update team's offensive rating based on points scored.

        Rating represents points per game above/below league average.
        Uses exponential moving average for responsiveness.
        """
        if team_id not in self.offensive_ratings:
            self.offensive_ratings[team_id] = 0.0

        # Adjust for opponent defensive strength
        adjusted_points = points_scored - opponent_def_rating

        # Exponential moving average (alpha = 0.15 for ~6 game window)
        alpha = 0.15
        self.offensive_ratings[team_id] = (
            alpha * adjusted_points + (1 - alpha) * self.offensive_ratings[team_id]
        )

    def update_defensive_rating(self, team_id: int, points_allowed: float, opponent_off_rating: float = 0.0):
        """
        Update team's defensive rating based on points allowed.

        Rating represents points per game allowed above/below league average.
        Negative is good defense (allows fewer points).
        """
        if team_id not in self.defensive_ratings:
            self.defensive_ratings[team_id] = 0.0

        # Adjust for opponent offensive strength
        adjusted_points = points_allowed - opponent_off_rating

        # Exponential moving average
        alpha = 0.15
        self.defensive_ratings[team_id] = (
            alpha * adjusted_points + (1 - alpha) * self.defensive_ratings[team_id]
        )

    def calculate_expected_total(
        self,
        home_team_id: int,
        away_team_id: int,
        league_avg_ppg: float = 22.5  # NFL average points per team
    ) -> Tuple[float, float, float]:
        """
        Calculate expected game total using team offensive/defensive ratings.

        Args:
            home_team_id: Home team ID
            away_team_id: Away team ID
            league_avg_ppg: League average points per team per game

        Returns:
            Tuple of (expected_home_points, expected_away_points, expected_total)
        """
        # Get ratings (default to 0 = league average)
        home_off = self.offensive_ratings.get(home_team_id, 0.0)
        home_def = self.defensive_ratings.get(home_team_id, 0.0)
        away_off = self.offensive_ratings.get(away_team_id, 0.0)
        away_def = self.defensive_ratings.get(away_team_id, 0.0)

        # Home team expected points: league avg + their offense + opponent defense
        home_points = league_avg_ppg + home_off + away_def

        # Away team expected points: league avg + their offense + opponent defense
        away_points = league_avg_ppg + away_off + home_def

        # Add home field advantage (~2.5 points in NFL)
        home_points += 2.5

        expected_total = home_points + away_points

        return home_points, away_points, expected_total


def calculate_implied_total(
    home_elo: float,
    away_elo: float,
    league_avg_total: float = 45.0
) -> Tuple[float, float]:
    """
    Calculate implied team totals from ELO ratings.

    Args:
        home_elo: Home team ELO
        away_elo: Away team ELO
        league_avg_total: Average total points in league

    Returns:
        Tuple of (home_implied_points, away_implied_points)
    """
    # Simple model: team strength affects scoring
    elo_diff = home_elo - away_elo
    point_diff = elo_diff / 25  # Rough conversion: 25 ELO ~= 1 point

    avg_per_team = league_avg_total / 2

    home_points = avg_per_team + (point_diff / 2)
    away_points = avg_per_team - (point_diff / 2)

    return home_points, away_points
