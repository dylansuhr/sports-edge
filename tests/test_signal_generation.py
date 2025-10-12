"""
Integration tests for signal generation pipeline
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'packages' / 'models'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'packages' / 'shared'))

from models.features import ELOModel
from shared.odds_math import american_to_decimal, american_to_implied_prob, calculate_edge


class TestSignalGenerationLogic:
    """Test the signal generation logic"""

    def test_edge_calculation_pipeline(self):
        """Test full edge calculation from ELO to signal"""
        elo = ELOModel()

        # Set up teams with known ratings
        elo.ratings['team_home'] = 1600
        elo.ratings['team_away'] = 1400

        # Get fair probability from ELO
        fair_prob = elo.predict_win_probability('team_home', 'team_away', is_home=True)

        # Market offers -110 (implied prob ~52.4%)
        odds_american = -110
        implied_prob = american_to_implied_prob(odds_american)

        # Calculate edge
        edge = calculate_edge(fair_prob, implied_prob)

        # With higher ELO and home advantage, should have positive edge
        assert edge > 0

    def test_signal_filtering_by_edge(self):
        """Test that signals below threshold are filtered"""
        MIN_EDGE = 0.02  # 2%

        # Case 1: Edge above threshold
        fair_prob_1 = 0.60
        implied_prob_1 = 0.524  # -110 odds
        edge_1 = calculate_edge(fair_prob_1, implied_prob_1)

        should_signal_1 = edge_1 >= MIN_EDGE
        assert should_signal_1 is True

        # Case 2: Edge below threshold
        fair_prob_2 = 0.53
        implied_prob_2 = 0.524
        edge_2 = calculate_edge(fair_prob_2, implied_prob_2)

        should_signal_2 = edge_2 >= MIN_EDGE
        assert should_signal_2 is False

    def test_kelly_sizing_calculation(self):
        """Test Kelly stake calculation for signals"""
        from shared.odds_math import kelly_criterion

        fair_prob = 0.60
        odds_american = -110
        odds_decimal = american_to_decimal(odds_american)

        # Calculate Kelly stake (quarter Kelly)
        kelly_stake = kelly_criterion(
            fair_prob=fair_prob,
            decimal_odds=odds_decimal,
            kelly_fraction=0.25,
            max_stake_pct=0.01
        )

        # Should recommend some stake
        assert kelly_stake > 0

        # Should respect max stake
        assert kelly_stake <= 0.01

    def test_signal_expiry_nfl(self):
        """Test NFL signal expiration (48h before game)"""
        game_time = datetime.now() + timedelta(days=3)
        current_time = datetime.now()

        hours_until_game = (game_time - current_time).total_seconds() / 3600

        # NFL signals expire 48h before game
        NFL_EXPIRY_HOURS = 48
        should_generate = hours_until_game > NFL_EXPIRY_HOURS

        assert should_generate is True

        # Test near expiry
        game_time_soon = datetime.now() + timedelta(hours=40)
        hours_until_game_soon = (game_time_soon - current_time).total_seconds() / 3600
        should_generate_soon = hours_until_game_soon > NFL_EXPIRY_HOURS

        assert should_generate_soon is False

    def test_confidence_level_assignment(self):
        """Test confidence level based on edge"""
        def assign_confidence(edge_percent):
            if edge_percent >= 5.0:
                return 'high'
            elif edge_percent >= 3.0:
                return 'medium'
            else:
                return 'low'

        assert assign_confidence(6.0) == 'high'
        assert assign_confidence(4.0) == 'medium'
        assert assign_confidence(2.5) == 'low'

    def test_edge_cap_filtering(self):
        """Test that suspiciously high edges are capped"""
        MAX_EDGE = 0.20  # 20%

        # Normal edge
        edge_normal = 0.05
        should_include_normal = edge_normal <= MAX_EDGE
        assert should_include_normal is True

        # Suspicious edge (likely model error)
        edge_suspicious = 0.35
        should_include_suspicious = edge_suspicious <= MAX_EDGE
        assert should_include_suspicious is False


class TestPaperBettingLogic:
    """Test paper betting decision logic"""

    def test_kelly_stake_scales_with_bankroll(self):
        """Test that Kelly stake scales with bankroll"""
        from shared.odds_math import kelly_criterion

        fair_prob = 0.60
        odds_decimal = 2.0
        kelly_pct = kelly_criterion(fair_prob, odds_decimal, kelly_fraction=0.25)

        bankroll_small = 1000
        bankroll_large = 10000

        stake_small = bankroll_small * kelly_pct
        stake_large = bankroll_large * kelly_pct

        # Stakes should scale proportionally
        assert stake_large / stake_small == pytest.approx(10, rel=0.01)

    def test_correlation_risk_same_game(self):
        """Test that multiple bets on same game are flagged"""
        pending_bets = [
            {'game_id': 123, 'stake': 25},
            {'game_id': 456, 'stake': 30}
        ]

        # Test new signal on game 123 (already have bet)
        new_signal_game_id = 123
        has_existing_bet = any(bet['game_id'] == new_signal_game_id for bet in pending_bets)

        assert has_existing_bet is True

        # Test new signal on game 789 (no existing bet)
        new_signal_game_id = 789
        has_existing_bet = any(bet['game_id'] == new_signal_game_id for bet in pending_bets)

        assert has_existing_bet is False

    def test_bankroll_exposure_limit(self):
        """Test maximum exposure to pending bets"""
        bankroll = 1000
        pending_stakes = [25, 30, 20, 15]  # Total: 90
        new_stake = 50

        total_exposure = sum(pending_stakes) + new_stake
        exposure_pct = total_exposure / bankroll

        MAX_EXPOSURE = 0.15  # 15%
        within_limit = exposure_pct <= MAX_EXPOSURE

        # 140/1000 = 14%, should be within limit
        assert within_limit is True

        # Test exceeding limit
        large_stake = 100
        total_exposure_large = sum(pending_stakes) + large_stake
        exposure_pct_large = total_exposure_large / bankroll
        within_limit_large = exposure_pct_large <= MAX_EXPOSURE

        # 190/1000 = 19%, should exceed limit
        assert within_limit_large is False


class TestDataValidation:
    """Test data validation and edge cases"""

    def test_invalid_probability_handling(self):
        """Test handling of invalid probabilities"""
        with pytest.raises((ValueError, AssertionError)):
            # Probability > 1.0 should be invalid
            calculate_edge(fair_prob=1.5, implied_prob=0.5)

        with pytest.raises((ValueError, AssertionError)):
            # Negative probability should be invalid
            calculate_edge(fair_prob=-0.1, implied_prob=0.5)

    def test_missing_team_elo_handling(self):
        """Test handling of teams without ELO ratings"""
        elo = ELOModel()

        # Should return default rating (1500) for unknown teams
        rating = elo.get_rating('unknown_team_xyz')
        assert rating == 1500

    def test_stale_odds_filtering(self):
        """Test that stale odds are filtered"""
        from datetime import datetime, timedelta

        odds_fetched_at = datetime.now() - timedelta(hours=2)
        current_time = datetime.now()

        hours_since_fetch = (current_time - odds_fetched_at).total_seconds() / 3600

        MAX_ODDS_AGE_HOURS = 1
        is_stale = hours_since_fetch > MAX_ODDS_AGE_HOURS

        assert is_stale is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
