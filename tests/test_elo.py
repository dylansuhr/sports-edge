"""
Unit tests for ELO rating system
"""
import pytest
import sys
from pathlib import Path

# Add packages to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'packages' / 'models'))

from models.features import ELOModel


class TestELOModel:
    """Test ELO rating calculations"""

    def test_initial_rating(self):
        """Test that teams start with 1500 rating"""
        elo = ELOModel()
        assert elo.get_rating('test_team') == 1500

    def test_home_advantage(self):
        """Test home advantage is applied correctly"""
        elo = ELOModel()
        win_prob = elo.predict_win_probability('home_team', 'away_team', is_home=True)
        # With equal ratings, home team should have >50% win probability
        assert win_prob > 0.5
        assert win_prob < 1.0

    def test_rating_update_winner_gains(self):
        """Test that winning team gains rating points"""
        elo = ELOModel()
        initial_rating = elo.get_rating('winner_team')

        elo.update_rating('winner_team', 'loser_team', home_won=True, is_home=True)

        updated_rating = elo.get_rating('winner_team')
        assert updated_rating > initial_rating

    def test_rating_update_loser_loses(self):
        """Test that losing team loses rating points"""
        elo = ELOModel()
        initial_rating = elo.get_rating('loser_team')

        elo.update_rating('winner_team', 'loser_team', home_won=True, is_home=True)

        updated_rating = elo.get_rating('loser_team')
        assert updated_rating < initial_rating

    def test_rating_conservation(self):
        """Test that total rating points are conserved"""
        elo = ELOModel()
        winner_before = elo.get_rating('team_a')
        loser_before = elo.get_rating('team_b')
        total_before = winner_before + loser_before

        elo.update_rating('team_a', 'team_b', home_won=True, is_home=True)

        winner_after = elo.get_rating('team_a')
        loser_after = elo.get_rating('team_b')
        total_after = winner_after + loser_after

        # Total points should be conserved (within floating point precision)
        assert abs(total_after - total_before) < 0.01

    def test_upset_larger_rating_change(self):
        """Test that upsets result in larger rating changes"""
        elo = ELOModel()

        # Create a strong team and weak team
        elo.ratings['strong_team'] = 1700
        elo.ratings['weak_team'] = 1300

        # Case 1: Favorite wins (expected)
        elo1 = ELOModel()
        elo1.ratings['strong_team'] = 1700
        elo1.ratings['weak_team'] = 1300
        elo1.update_rating('strong_team', 'weak_team', home_won=True, is_home=True)
        favorite_gain = elo1.get_rating('strong_team') - 1700

        # Case 2: Underdog wins (upset)
        elo2 = ELOModel()
        elo2.ratings['strong_team'] = 1700
        elo2.ratings['weak_team'] = 1300
        elo2.update_rating('weak_team', 'strong_team', home_won=False, is_home=False)
        underdog_gain = elo2.get_rating('weak_team') - 1300

        # Underdog should gain more points than favorite
        assert underdog_gain > favorite_gain

    def test_win_probability_bounds(self):
        """Test that win probabilities are between 0 and 1"""
        elo = ELOModel()

        # Test various rating differences
        elo.ratings['team_a'] = 1800
        elo.ratings['team_b'] = 1200

        prob = elo.predict_win_probability('team_a', 'team_b', is_home=True)
        assert 0 < prob < 1

        prob = elo.predict_win_probability('team_b', 'team_a', is_home=True)
        assert 0 < prob < 1

    def test_equal_ratings_equal_probability(self):
        """Test that equal ratings give ~50% win probability (accounting for home advantage)"""
        elo = ELOModel()

        # Without home advantage, should be exactly 50%
        home_prob = elo.predict_win_probability('team_a', 'team_b', is_home=True)
        away_prob = elo.predict_win_probability('team_a', 'team_b', is_home=False)

        # Home team should have advantage
        assert home_prob > 0.5
        assert away_prob < 0.5

        # Should sum to approximately 1.0 if we consider reciprocal
        assert abs((home_prob + (1 - away_prob)) - 1.0) < 0.01


class TestELOEdgeCases:
    """Test edge cases and error handling"""

    def test_same_team_twice(self):
        """Test handling of same team playing itself"""
        elo = ELOModel()
        # This shouldn't happen but should not crash
        prob = elo.predict_win_probability('team_a', 'team_a', is_home=True)
        assert 0 < prob < 1

    def test_extreme_rating_difference(self):
        """Test with extreme rating differences"""
        elo = ELOModel()
        elo.ratings['super_strong'] = 2000
        elo.ratings['super_weak'] = 1000

        prob = elo.predict_win_probability('super_strong', 'super_weak', is_home=True)
        # Should be very high but not 1.0
        assert prob > 0.95
        assert prob < 1.0

    def test_multiple_updates(self):
        """Test multiple rating updates in sequence"""
        elo = ELOModel()

        initial_rating = elo.get_rating('team_x')

        # Win 5 games
        for i in range(5):
            elo.update_rating('team_x', f'opponent_{i}', home_won=True, is_home=True)

        # Rating should increase significantly
        assert elo.get_rating('team_x') > initial_rating + 50


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
