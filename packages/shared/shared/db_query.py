"""
Database Query Helper
Provides a simple query() function for executing SQL with parameters.
Matches the TypeScript query pattern used in the dashboard.
"""

from typing import List, Dict, Optional
from .db import get_db


def query(sql: str, params: Optional[List] = None) -> List[Dict]:
    """
    Execute SQL query and return results as list of dictionaries.

    This matches the TypeScript query() pattern in apps/dashboard/lib/db.ts
    and provides a simpler interface than using Database class directly.

    Args:
        sql: SQL query string (use %s for parameter placeholders)
        params: List of parameters to bind to query

    Returns:
        List of dictionaries (one per row), with column names as keys

    Example:
        >>> results = query("SELECT * FROM signals WHERE id = %s", [123])
        >>> print(results[0]['edge_percent'])
        5.2
    """
    db = get_db()

    with db.get_connection() as conn:
        with conn.cursor() as cur:
            # Execute with parameters
            cur.execute(sql, params or [])

            # Check if query returns results (SELECT vs INSERT/UPDATE/DELETE)
            if cur.description:
                # Get column names from cursor description
                columns = [desc[0] for desc in cur.description]

                # Fetch all rows and convert to list of dicts
                rows = cur.fetchall()
                return [dict(zip(columns, row)) for row in rows]

            # No results to return (INSERT/UPDATE/DELETE)
            return []
