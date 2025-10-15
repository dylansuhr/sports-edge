import { Pool } from 'pg';

// Use read-only database URL for dashboard queries
const pool = new Pool({
  connectionString: process.env.DATABASE_READONLY_URL || process.env.DATABASE_URL,
  max: 20, // Increased pool size for better concurrency
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 10000, // Increased from 2s to 10s to prevent premature timeouts
  statement_timeout: 30000, // 30s query timeout
  ssl: {
    rejectUnauthorized: false, // Required for Neon serverless
  },
});

/**
 * Execute a database query using the read-only connection pool with retry logic
 * @param text SQL query string
 * @param params Query parameters
 * @param retries Number of retry attempts (default: 3)
 * @returns Promise resolving to query results
 */
export async function query<T = any>(
  text: string,
  params?: any[],
  retries: number = 3
): Promise<T[]> {
  let lastError: Error | undefined;

  for (let attempt = 0; attempt < retries; attempt++) {
    let client;
    try {
      client = await pool.connect();
      const result = await client.query(text, params);
      return result.rows as T[];
    } catch (error) {
      lastError = error as Error;
      console.error(`Query attempt ${attempt + 1}/${retries} failed:`, error);

      // If this isn't the last attempt, wait before retrying
      if (attempt < retries - 1) {
        const delay = Math.min(1000 * Math.pow(2, attempt), 5000); // Exponential backoff, max 5s
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    } finally {
      if (client) {
        client.release();
      }
    }
  }

  // If all retries failed, throw the last error
  throw new Error(`Query failed after ${retries} attempts: ${lastError?.message}`);
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
