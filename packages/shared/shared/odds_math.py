"""Odds conversion, vig removal, and Kelly criterion calculations."""

from typing import Tuple
import numpy as np


def american_to_decimal(american_odds: int) -> float:
    """Convert American odds to decimal odds.

    Args:
        american_odds: American odds (e.g., -110, +150)

    Returns:
        Decimal odds (e.g., 1.909, 2.500)
    """
    if american_odds > 0:
        return 1 + (american_odds / 100)
    else:
        return 1 + (100 / abs(american_odds))


def decimal_to_american(decimal_odds: float) -> int:
    """Convert decimal odds to American odds.

    Args:
        decimal_odds: Decimal odds (e.g., 1.909, 2.500)

    Returns:
        American odds (e.g., -110, +150)
    """
    if decimal_odds >= 2.0:
        return int((decimal_odds - 1) * 100)
    else:
        return int(-100 / (decimal_odds - 1))


def implied_probability(american_odds: int) -> float:
    """Calculate implied probability from American odds.

    Args:
        american_odds: American odds (e.g., -110, +150)

    Returns:
        Implied probability as decimal (e.g., 0.5238)
    """
    decimal = american_to_decimal(american_odds)
    return 1 / decimal


def remove_vig_multiplicative(prob_a: float, prob_b: float) -> Tuple[float, float]:
    """Remove vig using multiplicative method (best for two-way markets).

    Args:
        prob_a: Implied probability of outcome A (can be float or Decimal)
        prob_b: Implied probability of outcome B (can be float or Decimal)

    Returns:
        Tuple of (fair_prob_a, fair_prob_b) after vig removal
    """
    # Convert to float to handle Decimal types from database
    prob_a = float(prob_a)
    prob_b = float(prob_b)

    total = prob_a + prob_b
    vig = total - 1.0

    # Multiplicative vig removal
    fair_prob_a = prob_a / total
    fair_prob_b = prob_b / total

    return fair_prob_a, fair_prob_b


def remove_vig_additive(prob_a: float, prob_b: float) -> Tuple[float, float]:
    """Remove vig using additive method (alternative approach).

    Args:
        prob_a: Implied probability of outcome A (can be float or Decimal)
        prob_b: Implied probability of outcome B (can be float or Decimal)

    Returns:
        Tuple of (fair_prob_a, fair_prob_b) after vig removal
    """
    # Convert to float to handle Decimal types from database
    prob_a = float(prob_a)
    prob_b = float(prob_b)

    total = prob_a + prob_b
    vig = total - 1.0

    # Split vig evenly
    fair_prob_a = prob_a - (vig / 2)
    fair_prob_b = prob_b - (vig / 2)

    return fair_prob_a, fair_prob_b


def calculate_edge(fair_prob: float, implied_prob: float) -> float:
    """Calculate edge percentage.

    Args:
        fair_prob: True/fair probability from model
        implied_prob: Implied probability from odds (can be float or Decimal)

    Returns:
        Edge as percentage (e.g., 3.5 means 3.5% edge)
    """
    # Convert to float to handle Decimal types from database
    return (float(fair_prob) - float(implied_prob)) * 100


def kelly_fraction(
    fair_prob: float,
    decimal_odds: float,
    fraction: float = 0.25
) -> float:
    """Calculate fractional Kelly stake.

    Args:
        fair_prob: True/fair probability of winning
        decimal_odds: Decimal odds offered
        fraction: Kelly fraction to use (default 0.25 for quarter-Kelly)

    Returns:
        Recommended stake as fraction of bankroll (e.g., 0.015 = 1.5%)
    """
    # Kelly formula: f = (bp - q) / b
    # where b = decimal_odds - 1, p = fair_prob, q = 1 - fair_prob
    b = decimal_odds - 1
    p = fair_prob
    q = 1 - fair_prob

    kelly_full = (b * p - q) / b

    # Apply fraction and ensure non-negative
    kelly_fractional = max(0, kelly_full * fraction)

    return kelly_fractional


def recommended_stake(
    fair_prob: float,
    american_odds: int,
    bankroll: float,
    fraction: float = 0.25,
    max_stake_pct: float = 0.01
) -> float:
    """Calculate recommended stake in dollars using fractional Kelly.

    Args:
        fair_prob: True/fair probability of winning
        american_odds: American odds offered
        bankroll: Total bankroll in dollars
        fraction: Kelly fraction (default 0.25)
        max_stake_pct: Maximum stake as % of bankroll (default 1%)

    Returns:
        Recommended stake in dollars
    """
    decimal = american_to_decimal(american_odds)
    kelly_pct = kelly_fraction(fair_prob, decimal, fraction)

    # Cap at max stake percentage
    stake_pct = min(kelly_pct, max_stake_pct)

    return bankroll * stake_pct


def calculate_clv(
    entry_odds_american: int,
    close_odds_american: int
) -> float:
    """Calculate Closing Line Value (CLV) as percentage.

    Positive CLV means you got better odds than the closing line.

    Args:
        entry_odds_american: Odds when you placed the bet
        close_odds_american: Closing line odds

    Returns:
        CLV as percentage (e.g., 2.5 means 2.5% better than close)
    """
    entry_prob = implied_probability(entry_odds_american)
    close_prob = implied_probability(close_odds_american)

    # CLV = (close_prob - entry_prob) * 100
    # Positive means you beat the closing line
    return (close_prob - entry_prob) * 100


def expected_value(
    fair_prob: float,
    american_odds: int,
    stake: float
) -> float:
    """Calculate expected value of a bet.

    Args:
        fair_prob: True/fair probability of winning
        american_odds: American odds offered
        stake: Stake amount in dollars

    Returns:
        Expected value in dollars
    """
    decimal = american_to_decimal(american_odds)
    win_amount = stake * (decimal - 1)
    loss_amount = -stake

    ev = (fair_prob * win_amount) + ((1 - fair_prob) * loss_amount)

    return ev


def break_even_probability(american_odds: int) -> float:
    """Calculate break-even win rate for given odds.

    Args:
        american_odds: American odds

    Returns:
        Break-even probability (e.g., 0.524 = need 52.4% win rate)
    """
    return implied_probability(american_odds)


def profit_from_bet(
    stake: float,
    american_odds: int,
    won: bool
) -> float:
    """Calculate profit/loss from a settled bet.

    Args:
        stake: Amount wagered
        american_odds: Odds the bet was placed at
        won: Whether the bet won

    Returns:
        Profit (positive) or loss (negative) in dollars
    """
    if won:
        decimal = american_to_decimal(american_odds)
        return stake * (decimal - 1)
    else:
        return -stake
