'use server';

import { query } from '@/lib/db';

export interface PerformanceMetrics {
  date: string;
  avg_clv: number;
  beat_close_pct: number;
  total_signals: number;
  avg_edge: number;
}

export interface ModelReadiness {
  status: 'ready' | 'monitor' | 'not_ready' | 'insufficient_data';
  clv: number;
  beat_close_pct: number;
  total_signals: number;
  min_signals_needed: number;
  message: string;
}

export interface SportPerformance {
  sport: string;
  signals: number;
  avg_clv: number;
  beat_close_pct: number;
  avg_edge: number;
}

export interface MarketPerformance {
  market: string;
  signals: number;
  avg_clv: number;
  beat_close_pct: number;
  avg_edge: number;
}

/**
 * Get daily performance metrics for charting
 */
export async function getDailyPerformance(days: number = 30): Promise<PerformanceMetrics[]> {
  const sql = `
    SELECT
      DATE(created_at) as date,
      ROUND(AVG(clv_percent)::numeric, 2) as avg_clv,
      ROUND((COUNT(CASE WHEN clv_percent > 0 THEN 1 END)::float / COUNT(*) * 100)::numeric, 1) as beat_close_pct,
      COUNT(*) as total_signals,
      ROUND(AVG(edge_percent)::numeric, 2) as avg_edge
    FROM signals
    WHERE clv_percent IS NOT NULL
      AND created_at > NOW() - INTERVAL '${days} days'
    GROUP BY DATE(created_at)
    ORDER BY date ASC
  `;

  const rows = await query<any>(sql);
  return rows.map(row => ({
    date: row.date,
    avg_clv: Number(row.avg_clv || 0),
    beat_close_pct: Number(row.beat_close_pct || 0),
    total_signals: Number(row.total_signals || 0),
    avg_edge: Number(row.avg_edge || 0),
  }));
}

/**
 * Get current model readiness status
 */
export async function getModelReadiness(): Promise<ModelReadiness> {
  const sql = `
    SELECT
      COUNT(*) as total_signals,
      ROUND(AVG(clv_percent)::numeric, 2) as avg_clv,
      ROUND((COUNT(CASE WHEN clv_percent > 0 THEN 1 END)::float / COUNT(*) * 100)::numeric, 1) as beat_close_pct
    FROM signals
    WHERE clv_percent IS NOT NULL
      AND created_at > NOW() - INTERVAL '14 days'
  `;

  const result = await query<{
    total_signals: any;
    avg_clv: any;
    beat_close_pct: any;
  }>(sql);

  const rawData = result[0];
  const data = rawData ? {
    total_signals: Number(rawData.total_signals || 0),
    avg_clv: Number(rawData.avg_clv || 0),
    beat_close_pct: Number(rawData.beat_close_pct || 0),
  } : null;

  const MIN_SIGNALS = 100;

  // Insufficient data
  if (!data || data.total_signals < MIN_SIGNALS) {
    return {
      status: 'insufficient_data',
      clv: data?.avg_clv || 0,
      beat_close_pct: data?.beat_close_pct || 0,
      total_signals: data?.total_signals || 0,
      min_signals_needed: MIN_SIGNALS,
      message: `Collecting data... Need ${MIN_SIGNALS - (data?.total_signals || 0)} more signals with CLV.`
    };
  }

  // Ready for betting
  if (data.avg_clv >= 0.5 && data.beat_close_pct >= 52) {
    return {
      status: 'ready',
      clv: data.avg_clv,
      beat_close_pct: data.beat_close_pct,
      total_signals: data.total_signals,
      min_signals_needed: MIN_SIGNALS,
      message: 'Model is beating the market consistently. Ready for live betting.'
    };
  }

  // Monitor closely
  if (data.avg_clv >= 0 && data.beat_close_pct >= 50) {
    return {
      status: 'monitor',
      clv: data.avg_clv,
      beat_close_pct: data.beat_close_pct,
      total_signals: data.total_signals,
      min_signals_needed: MIN_SIGNALS,
      message: 'Model showing positive signs. Continue monitoring before live betting.'
    };
  }

  // Not ready
  return {
    status: 'not_ready',
    clv: data.avg_clv,
    beat_close_pct: data.beat_close_pct,
    total_signals: data.total_signals,
    min_signals_needed: MIN_SIGNALS,
    message: 'Model not beating closing lines. Continue learning - do not bet yet.'
  };
}

/**
 * Get performance by sport
 */
export async function getPerformanceBySport(days: number = 14): Promise<SportPerformance[]> {
  const sql = `
    SELECT
      g.sport,
      COUNT(*) as signals,
      ROUND(AVG(s.clv_percent)::numeric, 2) as avg_clv,
      ROUND((COUNT(CASE WHEN s.clv_percent > 0 THEN 1 END)::float / COUNT(*) * 100)::numeric, 1) as beat_close_pct,
      ROUND(AVG(s.edge_percent)::numeric, 2) as avg_edge
    FROM signals s
    JOIN games g ON s.game_id = g.id
    WHERE s.clv_percent IS NOT NULL
      AND s.created_at > NOW() - INTERVAL '${days} days'
    GROUP BY g.sport
    ORDER BY avg_clv DESC
  `;

  const rows = await query<any>(sql);
  return rows.map(row => ({
    sport: row.sport,
    signals: Number(row.signals || 0),
    avg_clv: Number(row.avg_clv || 0),
    beat_close_pct: Number(row.beat_close_pct || 0),
    avg_edge: Number(row.avg_edge || 0),
  }));
}

/**
 * Get performance by market
 */
export async function getPerformanceByMarket(days: number = 14): Promise<MarketPerformance[]> {
  const sql = `
    SELECT
      m.name as market,
      COUNT(*) as signals,
      ROUND(AVG(s.clv_percent)::numeric, 2) as avg_clv,
      ROUND((COUNT(CASE WHEN s.clv_percent > 0 THEN 1 END)::float / COUNT(*) * 100)::numeric, 1) as beat_close_pct,
      ROUND(AVG(s.edge_percent)::numeric, 2) as avg_edge
    FROM signals s
    JOIN markets m ON s.market_id = m.id
    WHERE s.clv_percent IS NOT NULL
      AND s.created_at > NOW() - INTERVAL '${days} days'
    GROUP BY m.name
    ORDER BY avg_clv DESC
  `;

  const rows = await query<any>(sql);
  return rows.map(row => ({
    market: row.market,
    signals: Number(row.signals || 0),
    avg_clv: Number(row.avg_clv || 0),
    beat_close_pct: Number(row.beat_close_pct || 0),
    avg_edge: Number(row.avg_edge || 0),
  }));
}

/**
 * Get overall performance summary
 */
export async function getOverallPerformance(days: number = 14) {
  const sql = `
    SELECT
      COUNT(*) as total_signals,
      ROUND(AVG(clv_percent)::numeric, 2) as avg_clv,
      ROUND(STDDEV(clv_percent)::numeric, 2) as stddev_clv,
      ROUND((COUNT(CASE WHEN clv_percent > 0 THEN 1 END)::float / COUNT(*) * 100)::numeric, 1) as beat_close_pct,
      ROUND(AVG(edge_percent)::numeric, 2) as avg_edge,
      ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY clv_percent)::numeric, 2) as p25_clv,
      ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY clv_percent)::numeric, 2) as median_clv,
      ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY clv_percent)::numeric, 2) as p75_clv
    FROM signals
    WHERE clv_percent IS NOT NULL
      AND created_at > NOW() - INTERVAL '${days} days'
  `;

  const result = await query<any>(sql);
  const row = result[0];

  if (!row) return null;

  return {
    total_signals: Number(row.total_signals || 0),
    avg_clv: Number(row.avg_clv || 0),
    stddev_clv: Number(row.stddev_clv || 0),
    beat_close_pct: Number(row.beat_close_pct || 0),
    avg_edge: Number(row.avg_edge || 0),
    p25_clv: Number(row.p25_clv || 0),
    median_clv: Number(row.median_clv || 0),
    p75_clv: Number(row.p75_clv || 0),
  };
}
