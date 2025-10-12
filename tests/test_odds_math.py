"""
Unit tests for odds mathematics
"""
import pytest
import sys
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'packages' / 'shared'))

from shared.odds_math import (
    american_to_decimal,
    decimal_to_american,
    american_to_implied_prob,
    decimal_to_implied_prob,
    kelly_criterion,
    calculate_edge
)


class TestOddsConversions:
    """Test odds format conversions"""

    def test_american_to_decimal_positive(self):
        """Test positive American odds to decimal"""
        assert american_to_decimal(100) == pytest.approx(2.0, rel=0.01)
        assert american_to_decimal(200) == pytest.approx(3.0, rel=0.01)
        assert american_to_decimal(150) == pytest.approx(2.5, rel=0.01)

    def test_american_to_decimal_negative(self):
        """Test negative American odds to decimal"""
        assert american_to_decimal(-110) == pytest.approx(1.909, rel=0.01)
        assert american_to_decimal(-200) == pytest.approx(1.5, rel=0.01)
        assert american_to_decimal(-150) == pytest.approx(1.667, rel=0.01)

    def test_decimal_to_american_favorites(self):
        """Test decimal to American for favorites"""
        assert decimal_to_american(1.5) == pytest.approx(-200, rel=1)
        assert decimal_to_american(1.909) == pytest.approx(-110, rel=1)

    def test_decimal_to_american_underdogs(self):
        """Test decimal to American for underdogs"""
        assert decimal_to_american(2.0) == pytest.approx(100, rel=1)
        assert decimal_to_american(3.0) == pytest.approx(200, rel=1)

    def test_round_trip_american_decimal(self):
        """Test round-trip conversion accuracy"""
        for odds in [100, -110, 200, -200, 150, -150]:
            decimal = american_to_decimal(odds)
            back_to_american = decimal_to_american(decimal)
            assert back_to_american == pytest.approx(odds, rel=0.01)


class TestImpliedProbability:
    """Test implied probability calculations"""

    def test_american_to_implied_prob_even(self):
        """Test even odds (+100) = 50% probability"""
        prob = american_to_implied_prob(100)
        assert prob == pytest.approx(0.5, rel=0.01)

    def test_american_to_implied_prob_favorite(self):
        """Test favorite odds imply >50% probability"""
        prob = american_to_implied_prob(-200)
        assert prob > 0.5
        assert prob == pytest.approx(0.667, rel=0.01)

    def test_american_to_implied_prob_underdog(self):
        """Test underdog odds imply <50% probability"""
        prob = american_to_implied_prob(200)
        assert prob < 0.5
        assert prob == pytest.approx(0.333, rel=0.01)

    def test_decimal_to_implied_prob(self):
        """Test decimal odds to implied probability"""
        assert decimal_to_implied_prob(2.0) == pytest.approx(0.5, rel=0.01)
        assert decimal_to_implied_prob(1.5) == pytest.approx(0.667, rel=0.01)
        assert decimal_to_implied_prob(3.0) == pytest.approx(0.333, rel=0.01)

    def test_probability_bounds(self):
        """Test that probabilities are always between 0 and 1"""
        for odds in [100, -100, 500, -500, 1000, -1000]:
            prob = american_to_implied_prob(odds)
            assert 0 < prob < 1


class TestKellyCriterion:
    """Test Kelly Criterion bet sizing"""

    def test_kelly_positive_edge(self):
        """Test Kelly with positive edge"""
        # Fair prob 60%, odds imply 50%, positive edge
        fair_prob = 0.6
        decimal_odds = 2.0
        stake = kelly_criterion(fair_prob, decimal_odds)

        assert stake > 0
        assert stake < 1  # Should never bet entire bankroll

    def test_kelly_zero_edge(self):
        """Test Kelly with zero edge"""
        # Fair prob = implied prob, no edge
        fair_prob = 0.5
        decimal_odds = 2.0
        stake = kelly_criterion(fair_prob, decimal_odds)

        assert stake == 0

    def test_kelly_negative_edge(self):
        """Test Kelly with negative edge"""
        # Fair prob 40%, odds imply 50%, negative edge
        fair_prob = 0.4
        decimal_odds = 2.0
        stake = kelly_criterion(fair_prob, decimal_odds)

        assert stake == 0  # Should not bet

    def test_kelly_with_fraction(self):
        """Test fractional Kelly"""
        fair_prob = 0.6
        decimal_odds = 2.0

        full_kelly = kelly_criterion(fair_prob, decimal_odds, kelly_fraction=1.0)
        half_kelly = kelly_criterion(fair_prob, decimal_odds, kelly_fraction=0.5)
        quarter_kelly = kelly_criterion(fair_prob, decimal_odds, kelly_fraction=0.25)

        # Fractional Kelly should be proportionally smaller
        assert half_kelly == pytest.approx(full_kelly * 0.5, rel=0.01)
        assert quarter_kelly == pytest.approx(full_kelly * 0.25, rel=0.01)

    def test_kelly_respects_max_stake(self):
        """Test that Kelly respects max stake parameter"""
        # Create scenario with large edge
        fair_prob = 0.8
        decimal_odds = 2.0

        stake_with_max = kelly_criterion(fair_prob, decimal_odds, max_stake_pct=0.05)

        assert stake_with_max <= 0.05


class TestEdgeCalculation:
    """Test edge percentage calculations"""

    def test_calculate_edge_positive(self):
        """Test positive edge calculation"""
        fair_prob = 0.6
        implied_prob = 0.5
        edge = calculate_edge(fair_prob, implied_prob)

        assert edge > 0
        assert edge == pytest.approx(0.2, rel=0.01)  # 20% edge

    def test_calculate_edge_negative(self):
        """Test negative edge calculation"""
        fair_prob = 0.4
        implied_prob = 0.5
        edge = calculate_edge(fair_prob, implied_prob)

        assert edge < 0
        assert edge == pytest.approx(-0.2, rel=0.01)  # -20% edge

    def test_calculate_edge_zero(self):
        """Test zero edge"""
        fair_prob = 0.5
        implied_prob = 0.5
        edge = calculate_edge(fair_prob, implied_prob)

        assert edge == pytest.approx(0, abs=0.001)


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_zero_odds(self):
        """Test handling of zero odds"""
        with pytest.raises((ValueError, ZeroDivisionError)):
            american_to_decimal(0)

    def test_probability_exactly_one(self):
        """Test probability of exactly 1.0"""
        decimal_odds = 1.0
        prob = decimal_to_implied_prob(decimal_odds)
        assert prob == 1.0

    def test_very_long_odds(self):
        """Test very long odds (longshot)"""
        prob = american_to_implied_prob(10000)  # +10000 odds
        assert 0 < prob < 0.1
        assert prob == pytest.approx(0.0099, rel=0.01)

    def test_very_short_odds(self):
        """Test very short odds (heavy favorite)"""
        prob = american_to_implied_prob(-10000)  # -10000 odds
        assert 0.99 < prob < 1.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
