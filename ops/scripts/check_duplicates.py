#!/usr/bin/env python3
from dotenv import load_dotenv
import sys
import os

load_dotenv()
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from packages.shared.shared.db_query import query

# Check for duplicate signals
result = query('''
    SELECT 
        game_id,
        market_id,
        odds_american,
        sportsbook,
        COUNT(*) as count,
        array_agg(id) as signal_ids
    FROM signals
    WHERE status = 'active'
    GROUP BY game_id, market_id, odds_american, sportsbook
    HAVING COUNT(*) > 1
    ORDER BY COUNT(*) DESC
    LIMIT 20
''')

print(f'=== DUPLICATE SIGNALS ({len(result)} groups) ===')
for row in result:
    print(f"Game {row['game_id']} | Market {row['market_id']} | Odds {row['odds_american']} | {row['sportsbook']} | COUNT: {row['count']}")
    print(f"  Signal IDs: {row['signal_ids']}")
