import { Pool } from 'pg';

// Use read-only database URL for dashboard queries
const pool = new Pool({
  connectionString: process.env.DATABASE_READONLY_URL || process.env.DATABASE_URL,
  max: 10,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

/**
 * Execute a database query using the read-only connection pool
 * @param text SQL query string
 * @param params Query parameters
 * @returns Promise resolving to query results
 */
export async function query<T = any>(text: string, params?: any[]): Promise<T[]> {
  const client = await pool.connect();
  try {
    const result = await client.query(text, params);
    return result.rows as T[];
  } finally {
    client.release();
  }
}

/**
 * Get a client from the pool for transaction support
 * Remember to call client.release() when done
 */
export async function getClient() {
  return await pool.connect();
}

/**
 * Close all connections in the pool
 * Call this when shutting down the application
 */
export async function closePool() {
  await pool.end();
}
