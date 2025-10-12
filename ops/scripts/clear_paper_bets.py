#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from packages.shared.shared.db_query import query

query('DELETE FROM paper_bets')
query('DELETE FROM paper_bet_decisions')
query('''
    UPDATE paper_bankroll 
    SET balance = 1000.00,
        total_bets = 0,
        total_staked = 0,
        total_profit_loss = 0,
        roi_percent = 0,
        win_count = 0,
        loss_count = 0,
        push_count = 0,
        win_rate = 0
''')

print('✅ Cleared all paper bets and reset bankroll to $1,000')
