#!/usr/bin/env python3
"""
Backfill selection fields on historical signals and bets.

This script attempts to populate the new `selection` columns using existing data:
1. Signals with NULL selection fall back to the matching odds snapshot (latest by fetched_at).
2. Bets inherit the selection from their linked signal; any remaining gaps also try the snapshot lookup.

Use the default dry-run mode to inspect what would happen. Pass `--apply`
to execute the updates. Ambiguous rows (e.g., multiple snapshot matches with different
selections) are logged to CSV for manual follow-up.

Usage:
    python ops/scripts/backfill_selection_fields.py            # dry run
    python ops/scripts/backfill_selection_fields.py --apply    # execute updates
"""

import argparse
import csv
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

from dotenv import load_dotenv

# Ensure packages/ is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from packages.shared.shared.db_query import query

load_dotenv()


class SelectionBackfill:
    """Handles backfilling of selection columns for signals and bets."""

    def __init__(self, apply_changes: bool, output_dir: str = "tmp"):
        self.apply = apply_changes
        self.output_dir = output_dir
        self.timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        os.makedirs(self.output_dir, exist_ok=True)
        self.signal_conflicts_path = os.path.join(
            self.output_dir, f"selection_conflicts_signals_{self.timestamp}.csv"
        )
        self.bet_conflicts_path = os.path.join(
            self.output_dir, f"selection_conflicts_bets_{self.timestamp}.csv"
        )

        self.signal_conflicts: List[Dict] = []
        self.bet_conflicts: List[Dict] = []

    # --------------------------------------------------------------------- #
    # Utility helpers
    # --------------------------------------------------------------------- #

    def _find_snapshot_selection(
        self,
        game_id: int,
        market_id: int,
        sportsbook: str,
        odds_american: int
    ) -> Optional[str]:
        """Return the latest selection from odds_snapshots matching the criteria."""
        sql = """
            SELECT selection, fetched_at
            FROM odds_snapshots
            WHERE game_id = %s
              AND market_id = %s
              AND sportsbook = %s
              AND odds_american = %s
              AND selection IS NOT NULL
            ORDER BY fetched_at DESC
            LIMIT 2
        """
        rows = query(sql, [game_id, market_id, sportsbook, odds_american])

        if not rows:
            return None

        if len(rows) > 1 and rows[0]['selection'] != rows[1]['selection']:
            # Ambiguous: same odds recorded with different selections
            return None

        return rows[0]['selection']

    def _log_conflict(self, storage: List[Dict], row: Dict):
        """Append a conflict row for later CSV output."""
        storage.append(row)

    def _write_conflicts(self):
        """Write any logged conflicts to CSV files."""
        if self.signal_conflicts:
            with open(self.signal_conflicts_path, 'w', newline='') as fh:
                writer = csv.DictWriter(
                    fh,
                    fieldnames=list(self.signal_conflicts[0].keys())
                )
                writer.writeheader()
                writer.writerows(self.signal_conflicts)
            print(f"[Backfill] Signal conflicts written to {self.signal_conflicts_path}")

        if self.bet_conflicts:
            with open(self.bet_conflicts_path, 'w', newline='') as fh:
                writer = csv.DictWriter(
                    fh,
                    fieldnames=list(self.bet_conflicts[0].keys())
                )
                writer.writeheader()
                writer.writerows(self.bet_conflicts)
            print(f"[Backfill] Bet conflicts written to {self.bet_conflicts_path}")

    # --------------------------------------------------------------------- #
    # Signals
    # --------------------------------------------------------------------- #

    def backfill_signals(self) -> Dict[str, int]:
        """Populate selection on signals where missing using a bulk SQL query."""
        stats = {"total_missing": 0, "updated": 0, "conflicts": 0, "unmatched": 0}

        # Count signals without selection
        count_sql = "SELECT COUNT(*) FROM signals WHERE selection IS NULL"
        count_result = query(count_sql)
        stats["total_missing"] = int(count_result[0]['count']) if count_result else 0

        print(f"[Backfill] Found {stats['total_missing']} signals without selection")

        if stats["total_missing"] == 0:
            return stats

        if self.apply:
            # Bulk update using a JOIN with a subquery that picks the latest snapshot
            update_sql = """
                UPDATE signals s
                SET selection = latest.selection
                FROM (
                    SELECT DISTINCT ON (o.game_id, o.market_id, o.sportsbook, o.odds_american)
                        o.game_id,
                        o.market_id,
                        o.sportsbook,
                        o.odds_american,
                        o.selection
                    FROM odds_snapshots o
                    WHERE o.selection IS NOT NULL
                    ORDER BY o.game_id, o.market_id, o.sportsbook, o.odds_american, o.fetched_at DESC
                ) latest
                WHERE s.selection IS NULL
                    AND s.game_id = latest.game_id
                    AND s.market_id = latest.market_id
                    AND s.sportsbook = latest.sportsbook
                    AND s.odds_american = latest.odds_american
            """
            query(update_sql)

            # Count how many were updated
            remaining_sql = "SELECT COUNT(*) FROM signals WHERE selection IS NULL"
            remaining_result = query(remaining_sql)
            remaining = int(remaining_result[0]['count']) if remaining_result else 0
            stats["updated"] = stats["total_missing"] - remaining
            stats["unmatched"] = remaining

            print(f"[Backfill] Updated {stats['updated']} signals")
            print(f"[Backfill] {stats['unmatched']} signals remain without selection")
        else:
            # Dry run - estimate how many would be updated
            estimate_sql = """
                SELECT COUNT(DISTINCT s.id) as would_update
                FROM signals s
                JOIN odds_snapshots o ON
                    s.game_id = o.game_id
                    AND s.market_id = o.market_id
                    AND s.sportsbook = o.sportsbook
                    AND s.odds_american = o.odds_american
                WHERE s.selection IS NULL
                    AND o.selection IS NOT NULL
            """
            estimate_result = query(estimate_sql)
            stats["updated"] = int(estimate_result[0]['would_update']) if estimate_result else 0
            stats["unmatched"] = stats["total_missing"] - stats["updated"]

            print(f"[Backfill] Would update {stats['updated']} signals")
            print(f"[Backfill] {stats['unmatched']} signals would remain without selection")

        # Log unmatched signals as conflicts
        if stats["unmatched"] > 0:
            unmatched_sql = """
                SELECT s.id, s.game_id, s.market_id, s.sportsbook, s.odds_american
                FROM signals s
                LEFT JOIN odds_snapshots o ON
                    s.game_id = o.game_id
                    AND s.market_id = o.market_id
                    AND s.sportsbook = o.sportsbook
                    AND s.odds_american = o.odds_american
                    AND o.selection IS NOT NULL
                WHERE s.selection IS NULL
                    AND o.id IS NULL
                LIMIT 100
            """
            unmatched = query(unmatched_sql)
            for signal in unmatched:
                self._log_conflict(
                    self.signal_conflicts,
                    {
                        "signal_id": signal['id'],
                        "game_id": signal['game_id'],
                        "market_id": signal['market_id'],
                        "sportsbook": signal['sportsbook'],
                        "odds_american": signal['odds_american'],
                        "reason": "No matching snapshot with selection"
                    }
                )

        return stats

    # --------------------------------------------------------------------- #
    # Bets
    # --------------------------------------------------------------------- #

    def backfill_bets_from_signals(self) -> int:
        """Copy selection from linked signals into bets."""
        if not self.apply:
            sql = """
                SELECT COUNT(*)
                FROM bets b
                JOIN signals s ON b.signal_id = s.id
                WHERE b.selection IS NULL
                  AND s.selection IS NOT NULL
            """
            result = query(sql)
            return int(result[0]['count']) if result else 0

        # Execute update
        query("""
            UPDATE bets b
            SET selection = s.selection
            FROM signals s
            WHERE b.signal_id = s.id
              AND b.selection IS NULL
              AND s.selection IS NOT NULL
        """)

        # Return count updated (post-update query)
        result = query("""
            SELECT COUNT(*)
            FROM bets
            WHERE selection IS NULL
        """)
        remaining = int(result[0]['count']) if result else 0
        return remaining

    def backfill_remaining_bets(self) -> Dict[str, int]:
        """Handle bets still missing selection after signal copy."""
        stats = {"total_remaining": 0, "updated": 0, "conflicts": 0, "unmatched": 0}

        sql = """
            SELECT id, game_id, market_id, sportsbook, odds_american, stake_amount, placed_at
            FROM bets
            WHERE selection IS NULL
        """
        bets = query(sql)
        stats["total_remaining"] = len(bets)

        for bet in bets:
            snapshot_selection = self._find_snapshot_selection(
                bet['game_id'],
                bet['market_id'],
                bet['sportsbook'],
                bet['odds_american']
            )

            if not snapshot_selection:
                stats["unmatched"] += 1
                self._log_conflict(
                    self.bet_conflicts,
                    {
                        "bet_id": bet['id'],
                        "game_id": bet['game_id'],
                        "market_id": bet['market_id'],
                        "sportsbook": bet['sportsbook'],
                        "odds_american": bet['odds_american'],
                        "stake_amount": bet['stake_amount'],
                        "placed_at": bet['placed_at'],
                        "reason": "No matching snapshot or conflicting selections"
                    }
                )
                continue

            if self.apply:
                query(
                    """
                    UPDATE bets
                    SET selection = %s
                    WHERE id = %s
                    """,
                    [snapshot_selection, bet['id']]
                )

            stats["updated"] += 1

        return stats

    # --------------------------------------------------------------------- #
    # Runner
    # --------------------------------------------------------------------- #

    def run(self):
        print(f"[Backfill] Starting selection backfill (apply={self.apply})")

        signal_stats = self.backfill_signals()
        print(f"[Backfill] Signals needing selection: {signal_stats['total_missing']}")
        print(f"[Backfill] Signals updated: {signal_stats['updated']}")
        print(f"[Backfill] Signals unmatched/conflicts: {signal_stats['unmatched']}")

        remaining_bets_after_signal = self.backfill_bets_from_signals()
        print(f"[Backfill] Bets still missing selection after signal copy: {remaining_bets_after_signal}")

        bet_stats = self.backfill_remaining_bets()
        print(f"[Backfill] Remaining bets processed: {bet_stats['total_remaining']}")
        print(f"[Backfill] Bets updated: {bet_stats['updated']}")
        print(f"[Backfill] Bets unmatched/conflicts: {bet_stats['unmatched']}")

        self._write_conflicts()

        if not self.apply:
            print("[Backfill] Dry run complete. Re-run with --apply to execute these updates.")
        else:
            print("[Backfill] Apply run complete.")


def main():
    parser = argparse.ArgumentParser(description='Backfill selection fields on signals and bets.')
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Execute updates. Omit for dry run.'
    )
    parser.add_argument(
        '--output-dir',
        default='tmp',
        help='Directory to store conflict CSV files (default: tmp)'
    )
    args = parser.parse_args()

    backfill = SelectionBackfill(apply_changes=args.apply, output_dir=args.output_dir)
    backfill.run()


if __name__ == '__main__':
    main()
