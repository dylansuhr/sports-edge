"""
Unit tests for odds_math module.

Tests odds conversions, vig removal, Kelly criterion, CLV, and other betting calculations.

Run with: pytest packages/shared/tests/test_odds_math.py -v
"""

import pytest
import sys
import os

# Add packages to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.odds_math import (
    american_to_decimal,
    decimal_to_american,
    implied_probability,
    remove_vig_multiplicative,
    remove_vig_additive,
    calculate_edge,
    kelly_fraction,
    recommended_stake,
    calculate_clv,
    expected_value,
    break_even_probability,
    profit_from_bet,
)


class TestOddsConversions:
    """Test odds format conversions."""

    def test_american_to_decimal_positive(self):
        """Test converting positive American odds to decimal."""
        assert american_to_decimal(100) == 2.0
        assert american_to_decimal(150) == 2.5
        assert american_to_decimal(200) == 3.0
        assert pytest.approx(american_to_decimal(110), 0.001) == 2.1

    def test_american_to_decimal_negative(self):
        """Test converting negative American odds to decimal."""
        assert pytest.approx(american_to_decimal(-110), 0.001) == 1.909
        assert pytest.approx(american_to_decimal(-200), 0.001) == 1.5
        assert pytest.approx(american_to_decimal(-150), 0.001) == 1.667
        assert american_to_decimal(-100) == 2.0

    def test_decimal_to_american_over_2(self):
        """Test converting decimal odds >= 2.0 to American."""
        assert decimal_to_american(2.0) == 100
        assert decimal_to_american(2.5) == 150
        assert decimal_to_american(3.0) == 200

    def test_decimal_to_american_under_2(self):
        """Test converting decimal odds < 2.0 to American."""
        assert decimal_to_american(1.909) == -110
        assert decimal_to_american(1.5) == -200
        assert decimal_to_american(1.667) == -150

    def test_round_trip_conversion(self):
        """Test that conversions are reversible."""
        test_american_odds = [-200, -150, -110, 100, 110, 150, 200]

        for american in test_american_odds:
            decimal = american_to_decimal(american)
            back_to_american = decimal_to_american(decimal)

            # Allow small rounding difference
            assert abs(american - back_to_american) <= 1


class TestImpliedProbability:
    """Test implied probability calculations."""

    def test_implied_prob_favorites(self):
        """Test implied probability for favorites (negative odds)."""
        # -110 implies ~52.38%
        assert pytest.approx(implied_probability(-110), 0.001) == 0.5238

        # -200 implies ~66.67%
        assert pytest.approx(implied_probability(-200), 0.001) == 0.6667

        # -150 implies ~60%
        assert pytest.approx(implied_probability(-150), 0.001) == 0.6

    def test_implied_prob_underdogs(self):
        """Test implied probability for underdogs (positive odds)."""
        # +100 implies 50%
        assert implied_probability(100) == 0.5

        # +150 implies 40%
        assert implied_probability(150) == 0.4

        # +200 implies 33.33%
        assert pytest.approx(implied_probability(200), 0.001) == 0.3333

    def test_implied_prob_sums_over_100(self):
        """Test that two-way market implied probs sum to > 100% (vig)."""
        home_odds = -110
        away_odds = -110

        home_prob = implied_probability(home_odds)
        away_prob = implied_probability(away_odds)
        total = home_prob + away_prob

        # Should be > 1.0 due to vig
        assert total > 1.0
        assert pytest.approx(total, 0.01) == 1.048  # ~4.8% vig


class TestVigRemoval:
    """Test vig removal methods."""

    def test_multiplicative_vig_removal(self):
        """Test multiplicative vig removal for two-way market."""
        # -110 / -110 market
        prob_a = implied_probability(-110)
        prob_b = implied_probability(-110)

        fair_a, fair_b = remove_vig_multiplicative(prob_a, prob_b)

        # Should sum to 1.0 after vig removal
        assert pytest.approx(fair_a + fair_b, 0.001) == 1.0

        # Should both be 50% for equal odds
        assert pytest.approx(fair_a, 0.001) == 0.5
        assert pytest.approx(fair_b, 0.001) == 0.5

    def test_multiplicative_vig_unequal_odds(self):
        """Test multiplicative vig removal with unequal odds."""
        # -150 (favorite) vs +130 (underdog)
        prob_favorite = implied_probability(-150)
        prob_underdog = implied_probability(130)

        fair_fav, fair_dog = remove_vig_multiplicative(prob_favorite, prob_underdog)

        # Should sum to 1.0
        assert pytest.approx(fair_fav + fair_dog, 0.001) == 1.0

        # Favorite should still be more likely
        assert fair_fav > fair_dog

    def test_additive_vig_removal(self):
        """Test additive vig removal method."""
        prob_a = implied_probability(-110)
        prob_b = implied_probability(-110)

        fair_a, fair_b = remove_vig_additive(prob_a, prob_b)

        # Should sum to 1.0
        assert pytest.approx(fair_a + fair_b, 0.001) == 1.0


class TestEdgeCalculation:
    """Test edge calculation."""

    def test_positive_edge(self):
        """Test calculation with positive edge."""
        fair_prob = 0.55  # 55% true probability
        implied_prob = 0.50  # 50% implied by odds

        edge = calculate_edge(fair_prob, implied_prob)

        assert edge == 5.0  # 5% edge

    def test_negative_edge(self):
        """Test calculation with negative edge."""
        fair_prob = 0.45  # 45% true probability
        implied_prob = 0.50  # 50% implied by odds

        edge = calculate_edge(fair_prob, implied_prob)

        assert edge == -5.0  # -5% edge (bad bet)

    def test_zero_edge(self):
        """Test calculation with no edge."""
        fair_prob = 0.50
        implied_prob = 0.50

        edge = calculate_edge(fair_prob, implied_prob)

        assert edge == 0.0


class TestKellyCriterion:
    """Test Kelly criterion calculations."""

    def test_kelly_fraction_positive_edge(self):
        """Test Kelly stake calculation with positive edge."""
        fair_prob = 0.55  # 55% win rate
        decimal_odds = 2.0  # +100 odds
        fraction = 0.25  # Quarter-Kelly

        kelly_stake = kelly_fraction(fair_prob, decimal_odds, fraction)

        # Should recommend a positive stake
        assert kelly_stake > 0
        assert kelly_stake < 0.1  # Should be reasonable

    def test_kelly_fraction_no_edge(self):
        """Test Kelly stake with no edge."""
        fair_prob = 0.5
        decimal_odds = 2.0
        fraction = 0.25

        kelly_stake = kelly_fraction(fair_prob, decimal_odds, fraction)

        # Should be 0 or very close to it
        assert kelly_stake == 0.0

    def test_kelly_fraction_negative_edge(self):
        """Test Kelly stake with negative edge."""
        fair_prob = 0.45  # Unfavorable odds
        decimal_odds = 2.0
        fraction = 0.25

        kelly_stake = kelly_fraction(fair_prob, decimal_odds, fraction)

        # Should be 0 (never bet negative edge)
        assert kelly_stake == 0.0

    def test_recommended_stake_with_cap(self):
        """Test that stake is capped at max percentage."""
        fair_prob = 0.70  # Very high edge
        american_odds = 100
        bankroll = 1000
        fraction = 0.25
        max_stake_pct = 0.01  # 1% cap

        stake = recommended_stake(fair_prob, american_odds, bankroll, fraction, max_stake_pct)

        # Should be capped at 1% of bankroll
        assert stake == 10.0  # 1% of $1000

    def test_recommended_stake_dollars(self):
        """Test recommended stake returns dollar amount."""
        fair_prob = 0.52
        american_odds = -110
        bankroll = 1000
        fraction = 0.25
        max_stake_pct = 0.01

        stake = recommended_stake(fair_prob, american_odds, bankroll, fraction, max_stake_pct)

        # Should be in dollars
        assert stake >= 0
        assert stake <= bankroll * max_stake_pct


class TestCLV:
    """Test Closing Line Value calculations."""

    def test_positive_clv(self):
        """Test CLV when entry odds better than closing."""
        entry_odds = +110  # Got +110
        close_odds = +100  # Market closed at +100

        clv = calculate_clv(entry_odds, close_odds)

        # Should be positive (you beat the close)
        assert clv > 0

    def test_negative_clv(self):
        """Test CLV when entry odds worse than closing."""
        entry_odds = +100  # Got +100
        close_odds = +110  # Market closed at +110

        clv = calculate_clv(entry_odds, close_odds)

        # Should be negative (you didn't beat the close)
        assert clv < 0

    def test_zero_clv(self):
        """Test CLV when entry and closing odds are equal."""
        entry_odds = +100
        close_odds = +100

        clv = calculate_clv(entry_odds, close_odds)

        # Should be 0
        assert pytest.approx(clv, 0.001) == 0.0

    def test_clv_favorites(self):
        """Test CLV calculation for favorite odds."""
        entry_odds = -105  # Got -105
        close_odds = -110  # Market closed at -110

        clv = calculate_clv(entry_odds, close_odds)

        # Getting -105 when it closes -110 is positive CLV
        assert clv > 0


class TestExpectedValue:
    """Test expected value calculations."""

    def test_positive_ev_bet(self):
        """Test EV calculation for positive edge bet."""
        fair_prob = 0.55  # 55% true win rate
        american_odds = 100  # +100 odds (50% implied)
        stake = 100

        ev = expected_value(fair_prob, american_odds, stake)

        # Should be positive
        assert ev > 0

    def test_negative_ev_bet(self):
        """Test EV calculation for negative edge bet."""
        fair_prob = 0.45  # 45% true win rate
        american_odds = 100  # +100 odds (50% implied)
        stake = 100

        ev = expected_value(fair_prob, american_odds, stake)

        # Should be negative
        assert ev < 0

    def test_zero_ev_bet(self):
        """Test EV calculation for break-even bet."""
        fair_prob = 0.50
        american_odds = 100
        stake = 100

        ev = expected_value(fair_prob, american_odds, stake)

        # Should be close to 0
        assert pytest.approx(ev, 0.01) == 0.0


class TestBreakEvenProbability:
    """Test break-even probability calculations."""

    def test_break_even_even_odds(self):
        """Test break-even for +100 odds."""
        be_prob = break_even_probability(100)

        # +100 requires 50% win rate to break even
        assert be_prob == 0.5

    def test_break_even_favorite(self):
        """Test break-even for favorite odds."""
        be_prob = break_even_probability(-200)

        # -200 requires ~66.67% win rate
        assert pytest.approx(be_prob, 0.001) == 0.6667

    def test_break_even_underdog(self):
        """Test break-even for underdog odds."""
        be_prob = break_even_probability(200)

        # +200 requires 33.33% win rate
        assert pytest.approx(be_prob, 0.001) == 0.3333


class TestProfitFromBet:
    """Test profit/loss calculations for settled bets."""

    def test_profit_winning_underdog(self):
        """Test profit from winning underdog bet."""
        stake = 100
        american_odds = 150  # +150
        won = True

        profit = profit_from_bet(stake, american_odds, won)

        # Should win $150 on $100 stake
        assert profit == 150.0

    def test_profit_winning_favorite(self):
        """Test profit from winning favorite bet."""
        stake = 100
        american_odds = -110
        won = True

        profit = profit_from_bet(stake, american_odds, won)

        # Should win ~$90.91 on $100 stake
        assert pytest.approx(profit, 0.01) == 90.91

    def test_loss_losing_bet(self):
        """Test loss from losing bet."""
        stake = 100
        american_odds = 150  # Odds don't matter for losses
        won = False

        profit = profit_from_bet(stake, american_odds, won)

        # Should lose the full stake
        assert profit == -100.0

    def test_profit_even_odds(self):
        """Test profit from winning +100 bet."""
        stake = 100
        american_odds = 100
        won = True

        profit = profit_from_bet(stake, american_odds, won)

        # Should win exactly the stake
        assert profit == 100.0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_high_favorite(self):
        """Test calculations with very high favorite odds."""
        american_odds = -500
        decimal = american_to_decimal(american_odds)
        implied = implied_probability(american_odds)

        assert decimal < 1.5
        assert implied > 0.8

    def test_very_high_underdog(self):
        """Test calculations with very high underdog odds."""
        american_odds = 500
        decimal = american_to_decimal(american_odds)
        implied = implied_probability(american_odds)

        assert decimal == 6.0
        assert implied < 0.2

    def test_zero_bankroll_stake(self):
        """Test stake calculation with zero bankroll."""
        stake = recommended_stake(
            fair_prob=0.55,
            american_odds=100,
            bankroll=0,
            fraction=0.25,
            max_stake_pct=0.01
        )

        assert stake == 0.0

    def test_100_percent_fair_probability(self):
        """Test calculations with 100% fair probability."""
        # Edge case: model predicts 100% win rate
        fair_prob = 1.0
        american_odds = -110

        edge = calculate_edge(fair_prob, implied_probability(american_odds))

        # Should show massive edge
        assert edge > 40


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
