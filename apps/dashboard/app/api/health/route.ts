import { NextResponse } from 'next/server';
import { query } from '@/lib/db';

export const dynamic = 'force-dynamic';

interface HealthCheckResult {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  checks: {
    database: {
      status: 'ok' | 'error';
      latency_ms?: number;
      error?: string;
    };
    signals: {
      status: 'ok' | 'warning' | 'error';
      active_count?: number;
      last_generated?: string;
      staleness_hours?: number;
      error?: string;
    };
    odds: {
      status: 'ok' | 'warning' | 'error';
      last_fetched?: string;
      staleness_hours?: number;
      error?: string;
    };
  };
}

export async function GET() {
  const result: HealthCheckResult = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    checks: {
      database: { status: 'ok' },
      signals: { status: 'ok' },
      odds: { status: 'ok' }
    }
  };

  try {
    // Check database connectivity and latency
    const dbStart = Date.now();
    await query('SELECT 1');
    const dbLatency = Date.now() - dbStart;
    result.checks.database = {
      status: 'ok',
      latency_ms: dbLatency
    };

    // Check signals freshness
    const signalCheck = await query<{
      active_count: number;
      last_generated: string;
      staleness_hours: number;
    }>(`
      SELECT
        COUNT(*) as active_count,
        MAX(generated_at) as last_generated,
        EXTRACT(EPOCH FROM (NOW() - MAX(generated_at))) / 3600 as staleness_hours
      FROM signals
      WHERE status = 'active'
        AND expires_at > NOW()
    `);

    const signalData = signalCheck[0];
    result.checks.signals = {
      status: signalData.staleness_hours > 1 ? 'warning' : 'ok',
      active_count: Number(signalData.active_count),
      last_generated: signalData.last_generated,
      staleness_hours: Number(signalData.staleness_hours.toFixed(2))
    };

    if (signalData.staleness_hours > 2) {
      result.checks.signals.status = 'error';
      result.status = 'degraded';
    }

    // Check odds freshness
    const oddsCheck = await query<{
      last_fetched: string;
      staleness_hours: number;
    }>(`
      SELECT
        MAX(fetched_at) as last_fetched,
        EXTRACT(EPOCH FROM (NOW() - MAX(fetched_at))) / 3600 as staleness_hours
      FROM odds_snapshots
    `);

    const oddsData = oddsCheck[0];
    result.checks.odds = {
      status: oddsData.staleness_hours > 0.5 ? 'warning' : 'ok',
      last_fetched: oddsData.last_fetched,
      staleness_hours: Number(oddsData.staleness_hours.toFixed(2))
    };

    if (oddsData.staleness_hours > 1) {
      result.checks.odds.status = 'error';
      result.status = 'degraded';
    }

  } catch (error) {
    result.status = 'unhealthy';
    result.checks.database = {
      status: 'error',
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }

  // Determine overall status
  const hasError = Object.values(result.checks).some(check => check.status === 'error');
  if (hasError) {
    result.status = 'unhealthy';
  }

  // Return appropriate HTTP status code
  const statusCode = result.status === 'healthy' ? 200 : result.status === 'degraded' ? 503 : 503;

  return NextResponse.json(result, { status: statusCode });
}
