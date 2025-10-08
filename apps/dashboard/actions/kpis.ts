'use server';

import { query } from '@/lib/db';

export interface DashboardKPIs {
  openSignalsCount: number;
  avgEdgePercent: number;
  clvLast7Days: number;
  lifetimeROI: number;
}

export async function getDashboardKPIs(): Promise<DashboardKPIs> {
  // Open signals count
  const openSignalsSql = `
    SELECT COUNT(*) as count
    FROM signals
    WHERE status = 'active'
      AND expires_at > NOW()
  `;

  const openSignalsResult = await query<{ count: number }>(openSignalsSql);
  const openSignalsCount = openSignalsResult[0]?.count || 0;

  // Average edge percent for active signals
  const avgEdgeSql = `
    SELECT AVG(edge_percent) as avg_edge
    FROM signals
    WHERE status = 'active'
      AND expires_at > NOW()
  `;

  const avgEdgeResult = await query<{ avg_edge: number }>(avgEdgeSql);
  const avgEdgePercent = avgEdgeResult[0]?.avg_edge || 0;

  // CLV last 7 days
  const clvSql = `
    SELECT AVG(clv_percent) as avg_clv
    FROM bets
    WHERE settled_at >= NOW() - INTERVAL '7 days'
      AND clv_percent IS NOT NULL
  `;

  const clvResult = await query<{ avg_clv: number }>(clvSql);
  const clvLast7Days = clvResult[0]?.avg_clv || 0;

  // Lifetime ROI
  const roiSql = `
    SELECT
      SUM(profit_loss) as total_pnl,
      SUM(stake_amount) as total_staked
    FROM bets
    WHERE settled_at IS NOT NULL
  `;

  const roiResult = await query<{ total_pnl: number; total_staked: number }>(roiSql);
  const totalPnL = roiResult[0]?.total_pnl || 0;
  const totalStaked = roiResult[0]?.total_staked || 0;
  const lifetimeROI = totalStaked > 0 ? (totalPnL / totalStaked) * 100 : 0;

  return {
    openSignalsCount,
    avgEdgePercent: Number(avgEdgePercent.toFixed(2)),
    clvLast7Days: Number(clvLast7Days.toFixed(2)),
    lifetimeROI: Number(lifetimeROI.toFixed(2)),
  };
}

export async function getRecentStats() {
  // Bets placed last 7 days
  const betsPlacedSql = `
    SELECT COUNT(*) as count
    FROM bets
    WHERE created_at >= NOW() - INTERVAL '7 days'
  `;

  const betsPlacedResult = await query<{ count: number }>(betsPlacedSql);
  const betsPlaced = betsPlacedResult[0]?.count || 0;

  // Bets settled last 7 days
  const betsSettledSql = `
    SELECT COUNT(*) as count
    FROM bets
    WHERE settled_at >= NOW() - INTERVAL '7 days'
  `;

  const betsSettledResult = await query<{ count: number }>(betsSettledSql);
  const betsSettled = betsSettledResult[0]?.count || 0;

  // Win rate last 7 days
  const winRateSql = `
    SELECT
      COUNT(*) FILTER (WHERE result = 'win') as wins,
      COUNT(*) as total
    FROM bets
    WHERE settled_at >= NOW() - INTERVAL '7 days'
      AND result IN ('win', 'loss')
  `;

  const winRateResult = await query<{ wins: number; total: number }>(winRateSql);
  const wins = winRateResult[0]?.wins || 0;
  const total = winRateResult[0]?.total || 0;
  const winRate = total > 0 ? (wins / total) * 100 : 0;

  return {
    betsPlaced,
    betsSettled,
    winRate: Number(winRate.toFixed(1)),
  };
}
