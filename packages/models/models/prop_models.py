"""
Baseline Fair-Odds Models for NFL Props

Implements simple but effective models for:
- Game lines (spread, moneyline, total)
- Player props (anytime TD, receiving yards, etc.)

Uses ELO-based features + statistical distributions.
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Optional, Tuple
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor


class NFLGameLineModel:
    """Baseline model for NFL game lines (spread, total, moneyline)."""

    def __init__(self):
        self.spread_model = None
        self.total_model = None
        self.is_fitted = False

    def fit(self, features_df: pd.DataFrame, targets_df: pd.DataFrame):
        """
        Fit models on historical data.

        Args:
            features_df: Features from NFLFeatureGenerator
            targets_df: DataFrame with 'spread_cover', 'total_over', 'home_win'
        """
        # Spread model (predict if home covers)
        self.spread_model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            random_state=42
        )

        # Total model (predict if over hits)
        self.total_model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            random_state=42
        )

        # Fit models
        self.spread_model.fit(features_df, targets_df['spread_cover'])
        self.total_model.fit(features_df, targets_df['total_over'])
        self.is_fitted = True

    def predict_moneyline(self, features: pd.Series) -> float:
        """
        Predict home win probability (moneyline).

        Uses ELO-based win probability as baseline.
        """
        return features['home_win_prob_elo']

    def predict_spread(self, features: pd.Series, line: float) -> float:
        """
        Predict probability that home team covers spread.

        Args:
            features: Game features
            line: Spread line (negative = home favored)

        Returns:
            Probability home covers
        """
        if not self.is_fitted:
            # Fallback to ELO-based estimate
            elo_diff = features['elo_diff']
            implied_spread = elo_diff / 25  # 25 ELO ~= 1 point
            cover_prob = stats.norm.cdf(implied_spread - line, scale=14)
            return cover_prob

        # Use trained model
        features_array = features.values.reshape(1, -1)
        return self.spread_model.predict_proba(features_array)[0, 1]

    def predict_total(self, features: pd.Series, line: float) -> float:
        """
        Predict probability that game goes over total.

        Args:
            features: Game features
            line: Total line

        Returns:
            Probability of over
        """
        if not self.is_fitted:
            # Fallback to simple estimate
            # Assume league average total ~45 with std dev ~10
            implied_total = 45.0
            over_prob = 1 - stats.norm.cdf(line, loc=implied_total, scale=10)
            return over_prob

        # Use trained model
        features_array = features.values.reshape(1, -1)
        return self.total_model.predict_proba(features_array)[0, 1]


class NFLPlayerPropModel:
    """Baseline model for NFL player props."""

    def __init__(self, prop_type: str = 'receiving_yards'):
        """
        Initialize player prop model.

        Args:
            prop_type: Type of prop (receiving_yards, rushing_yards, anytime_td, etc.)
        """
        self.prop_type = prop_type
        self.model = None
        self.is_fitted = False

    def fit(self, features_df: pd.DataFrame, targets: pd.Series):
        """
        Fit model on historical player performance.

        Args:
            features_df: Player features (usage, opponent rank, etc.)
            targets: Historical stat values or binary outcomes
        """
        if self.prop_type in ['anytime_td', 'first_td']:
            # Binary classification
            self.model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=3,
                learning_rate=0.1,
                random_state=42
            )
        else:
            # Continuous stat prediction
            self.model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=3,
                learning_rate=0.1,
                random_state=42
            )

        self.model.fit(features_df, targets)
        self.is_fitted = True

    def predict_over_probability(
        self,
        player_features: pd.Series,
        line: float,
        historical_stats: Optional[np.ndarray] = None
    ) -> float:
        """
        Predict probability that player goes over prop line.

        Args:
            player_features: Player-specific features
            line: Prop line value
            historical_stats: Recent game stats for distribution fitting

        Returns:
            Probability of going over
        """
        if self.prop_type == 'anytime_td':
            return self._predict_td_probability(player_features)

        # For continuous stats, fit distribution to recent performance
        if historical_stats is not None and len(historical_stats) >= 5:
            mean = np.mean(historical_stats)
            std = np.std(historical_stats)

            # Model as truncated normal (can't have negative yards)
            if std > 0:
                over_prob = 1 - stats.norm.cdf(line, loc=mean, scale=std)
            else:
                over_prob = 1.0 if mean > line else 0.0

            return np.clip(over_prob, 0.01, 0.99)

        # Fallback: use 50/50 if no data
        return 0.5

    def _predict_td_probability(self, player_features: pd.Series) -> float:
        """Predict probability of scoring a touchdown."""
        if not self.is_fitted:
            # Simple heuristic based on position
            position = player_features.get('position', 'WR')

            # Base rates by position (league averages)
            base_rates = {
                'RB': 0.45,   # RBs score ~45% of games
                'WR': 0.35,   # WRs score ~35% of games
                'TE': 0.25,   # TEs score ~25% of games
                'QB': 0.20    # QBs rush TD ~20% of games
            }

            return base_rates.get(position, 0.30)

        # Use trained model
        features_array = player_features.values.reshape(1, -1)

        if hasattr(self.model, 'predict_proba'):
            return self.model.predict_proba(features_array)[0, 1]
        else:
            return self.model.predict(features_array)[0]


class SimplePoissonModel:
    """
    Simple Poisson-based model for scoring props.

    Useful for props like: player touchdowns, team total points, etc.
    """

    @staticmethod
    def predict_poisson_over(
        lambda_param: float,
        line: float
    ) -> float:
        """
        Predict probability of going over using Poisson distribution.

        Args:
            lambda_param: Expected value (mean)
            line: Prop line

        Returns:
            Probability of going over
        """
        # P(X > line) = 1 - P(X <= line)
        # For Poisson, P(X <= k) = CDF(k)

        # Handle half-lines (e.g., 0.5 TDs)
        if line % 1 != 0:
            k = int(np.floor(line))
        else:
            k = int(line)

        return 1 - stats.poisson.cdf(k, lambda_param)

    @staticmethod
    def estimate_lambda_from_history(
        historical_counts: np.ndarray
    ) -> float:
        """
        Estimate Poisson lambda from historical data.

        Args:
            historical_counts: Array of historical count data

        Returns:
            Estimated lambda (mean rate)
        """
        return np.mean(historical_counts)


def create_baseline_fair_odds(
    model_prob: float,
    margin_pct: float = 0.0
) -> Dict[str, float]:
    """
    Convert model probability to fair odds (no vig).

    Args:
        model_prob: Model's estimated probability
        margin_pct: Optional margin to add (default 0 for true fair odds)

    Returns:
        Dict with fair_prob, fair_decimal_odds, fair_american_odds
    """
    from packages.shared.shared.odds_math import decimal_to_american

    # Clip to reasonable bounds
    fair_prob = np.clip(model_prob, 0.01, 0.99)

    # Add margin if specified
    if margin_pct > 0:
        fair_prob = fair_prob * (1 + margin_pct)
        fair_prob = np.clip(fair_prob, 0.01, 0.99)

    # Convert to odds
    fair_decimal = 1 / fair_prob
    fair_american = decimal_to_american(fair_decimal)

    return {
        'fair_prob': fair_prob,
        'fair_decimal_odds': fair_decimal,
        'fair_american_odds': fair_american
    }
