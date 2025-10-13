'use server';

import { neon } from '@neondatabase/serverless';

const sql = neon(process.env.DATABASE_READONLY_URL || 'postgresql://dummy:dummy@localhost:5432/dummy');

// Advanced Performance Tracking
export interface AdvancedPerformanceMetrics {
  by_sportsbook: Array<{
    sportsbook: string;
    count: number;
    avg_clv: number;
    roi: number;
    win_rate: number;
  }>;
  by_market: Array<{
    market: string;
    count: number;
    avg_clv: number;
    roi: number;
    win_rate: number;
  }>;
  by_confidence: Array<{
    confidence: string;
    count: number;
    avg_clv: number;
    roi: number;
    win_rate: number;
  }>;
  by_time_of_day: Array<{
    hour: number;
    count: number;
    avg_clv: number;
  }>;
}

export async function getAdvancedPerformanceMetrics(): Promise<AdvancedPerformanceMetrics> {
  // Performance by sportsbook
  const bySportsbook = await sql`
    SELECT
      pb.sportsbook,
      COUNT(*) as count,
      AVG(s.clv_percentage) as avg_clv,
      (SUM(pb.profit_loss) / SUM(pb.stake)) * 100 as roi,
      (COUNT(*) FILTER (WHERE pb.result = 'won')::float / COUNT(*)) * 100 as win_rate
    FROM paper_bets pb
    LEFT JOIN signals s ON pb.signal_id = s.id
    WHERE pb.status = 'settled'
    GROUP BY pb.sportsbook
    ORDER BY roi DESC
  `;

  // Performance by market
  const byMarket = await sql`
    SELECT
      pb.market_type as market,
      COUNT(*) as count,
      AVG(s.clv_percentage) as avg_clv,
      (SUM(pb.profit_loss) / SUM(pb.stake)) * 100 as roi,
      (COUNT(*) FILTER (WHERE pb.result = 'won')::float / COUNT(*)) * 100 as win_rate
    FROM paper_bets pb
    LEFT JOIN signals s ON pb.signal_id = s.id
    WHERE pb.status = 'settled'
    GROUP BY pb.market_type
    ORDER BY roi DESC
  `;

  // Performance by confidence
  const byConfidence = await sql`
    SELECT
      s.confidence,
      COUNT(*) as count,
      AVG(s.clv_percentage) as avg_clv,
      (SUM(pb.profit_loss) / SUM(pb.stake)) * 100 as roi,
      (COUNT(*) FILTER (WHERE pb.result = 'won')::float / COUNT(*)) * 100 as win_rate
    FROM paper_bets pb
    LEFT JOIN signals s ON pb.signal_id = s.id
    WHERE pb.status = 'settled'
    AND s.confidence IS NOT NULL
    GROUP BY s.confidence
    ORDER BY roi DESC
  `;

  // Performance by time of day (when bet was placed)
  const byTimeOfDay = await sql`
    SELECT
      EXTRACT(HOUR FROM pb.placed_at) as hour,
      COUNT(*) as count,
      AVG(s.clv_percentage) as avg_clv
    FROM paper_bets pb
    LEFT JOIN signals s ON pb.signal_id = s.id
    WHERE pb.status = 'settled'
    AND pb.placed_at IS NOT NULL
    GROUP BY EXTRACT(HOUR FROM pb.placed_at)
    ORDER BY hour
  `;

  return {
    by_sportsbook: bySportsbook.map(row => ({
      sportsbook: row.sportsbook,
      count: Number(row.count),
      avg_clv: Number(row.avg_clv || 0),
      roi: Number(row.roi || 0),
      win_rate: Number(row.win_rate || 0)
    })),
    by_market: byMarket.map(row => ({
      market: row.market,
      count: Number(row.count),
      avg_clv: Number(row.avg_clv || 0),
      roi: Number(row.roi || 0),
      win_rate: Number(row.win_rate || 0)
    })),
    by_confidence: byConfidence.map(row => ({
      confidence: row.confidence,
      count: Number(row.count),
      avg_clv: Number(row.avg_clv || 0),
      roi: Number(row.roi || 0),
      win_rate: Number(row.win_rate || 0)
    })),
    by_time_of_day: byTimeOfDay.map(row => ({
      hour: Number(row.hour),
      count: Number(row.count),
      avg_clv: Number(row.avg_clv || 0)
    }))
  };
}

// Parameter Tuning Monitoring
export interface ParameterHistory {
  date: string;
  edge_threshold: number;
  kelly_fraction: number;
  max_stake_pct: number;
  avg_edge: number;
  signal_count: number;
  clv: number;
}

export async function getParameterTuningHistory(days: number = 30): Promise<ParameterHistory[]> {
  // This would query a parameter_tuning_history table if it exists
  // For now, we'll analyze signal generation patterns over time
  const rows = await sql`
    SELECT
      DATE(created_at) as date,
      AVG(edge_percentage) as avg_edge,
      COUNT(*) as signal_count,
      AVG(clv_percentage) as clv
    FROM signals
    WHERE created_at > NOW() - INTERVAL '${days} days'
    AND status = 'active'
    GROUP BY DATE(created_at)
    ORDER BY date DESC
  `;

  return rows.map(row => ({
    date: row.date,
    edge_threshold: 0.02, // Would come from config
    kelly_fraction: 0.25, // Would come from config
    max_stake_pct: 0.01, // Would come from config
    avg_edge: Number(row.avg_edge || 0),
    signal_count: Number(row.signal_count),
    clv: Number(row.clv || 0)
  }));
}

// Correlation Analysis
export interface CorrelationData {
  edge_vs_clv: number;
  edge_vs_winrate: number;
  confidence_vs_clv: number;
  time_to_game_vs_clv: number;
  correlations: Array<{
    metric1: string;
    metric2: string;
    correlation: number;
    sample_size: number;
  }>;
}

export async function getCorrelationAnalysis(): Promise<CorrelationData> {
  // Get data for correlation calculations
  const data = await sql`
    SELECT
      s.edge_percentage,
      s.confidence,
      s.clv_percentage,
      pb.result,
      EXTRACT(EPOCH FROM (g.scheduled_at - s.created_at)) / 3600 as hours_to_game
    FROM signals s
    LEFT JOIN paper_bets pb ON pb.signal_id = s.id
    LEFT JOIN games g ON s.game_id = g.id
    WHERE pb.status = 'settled'
    AND s.clv_percentage IS NOT NULL
  `;

  // Calculate correlations (simplified - would use proper correlation formula)
  const correlations = [
    {
      metric1: 'Edge %',
      metric2: 'CLV %',
      correlation: calculateCorrelation(
        data.map(r => Number(r.edge_percentage)),
        data.map(r => Number(r.clv_percentage))
      ),
      sample_size: data.length
    },
    {
      metric1: 'Edge %',
      metric2: 'Win Rate',
      correlation: 0, // Placeholder
      sample_size: data.length
    },
    {
      metric1: 'Confidence',
      metric2: 'CLV %',
      correlation: 0, // Placeholder
      sample_size: data.length
    },
    {
      metric1: 'Time to Game',
      metric2: 'CLV %',
      correlation: calculateCorrelation(
        data.map(r => Number(r.hours_to_game || 0)),
        data.map(r => Number(r.clv_percentage))
      ),
      sample_size: data.length
    }
  ];

  return {
    edge_vs_clv: correlations[0].correlation,
    edge_vs_winrate: correlations[1].correlation,
    confidence_vs_clv: correlations[2].correlation,
    time_to_game_vs_clv: correlations[3].correlation,
    correlations
  };
}

// Helper function for correlation calculation
function calculateCorrelation(x: number[], y: number[]): number {
  const n = Math.min(x.length, y.length);
  if (n === 0) return 0;

  const meanX = x.reduce((a, b) => a + b, 0) / n;
  const meanY = y.reduce((a, b) => a + b, 0) / n;

  let numerator = 0;
  let denomX = 0;
  let denomY = 0;

  for (let i = 0; i < n; i++) {
    const dx = x[i] - meanX;
    const dy = y[i] - meanY;
    numerator += dx * dy;
    denomX += dx * dx;
    denomY += dy * dy;
  }

  const denominator = Math.sqrt(denomX * denomY);
  return denominator === 0 ? 0 : numerator / denominator;
}

// Betting Pattern Analysis
export interface BettingPatterns {
  best_performing_combo: {
    sport: string;
    market: string;
    sportsbook: string;
    roi: number;
    count: number;
  } | null;
  worst_performing_combo: {
    sport: string;
    market: string;
    sportsbook: string;
    roi: number;
    count: number;
  } | null;
  optimal_bet_timing: {
    hours_before_game: number;
    avg_clv: number;
    count: number;
  } | null;
}

export async function getBettingPatterns(): Promise<BettingPatterns> {
  // Best performing combination
  const bestCombo = await sql`
    SELECT
      g.sport,
      pb.market_type,
      pb.sportsbook,
      (SUM(pb.profit_loss) / SUM(pb.stake)) * 100 as roi,
      COUNT(*) as count
    FROM paper_bets pb
    LEFT JOIN signals s ON pb.signal_id = s.id
    LEFT JOIN games g ON s.game_id = g.id
    WHERE pb.status = 'settled'
    GROUP BY g.sport, pb.market_type, pb.sportsbook
    HAVING COUNT(*) >= 10
    ORDER BY roi DESC
    LIMIT 1
  `;

  // Worst performing combination
  const worstCombo = await sql`
    SELECT
      g.sport,
      pb.market_type,
      pb.sportsbook,
      (SUM(pb.profit_loss) / SUM(pb.stake)) * 100 as roi,
      COUNT(*) as count
    FROM paper_bets pb
    LEFT JOIN signals s ON pb.signal_id = s.id
    LEFT JOIN games g ON s.game_id = g.id
    WHERE pb.status = 'settled'
    GROUP BY g.sport, pb.market_type, pb.sportsbook
    HAVING COUNT(*) >= 10
    ORDER BY roi ASC
    LIMIT 1
  `;

  // Optimal bet timing
  const optimalTiming = await sql`
    SELECT
      ROUND(EXTRACT(EPOCH FROM (g.scheduled_at - pb.placed_at)) / 3600) as hours_before_game,
      AVG(s.clv_percentage) as avg_clv,
      COUNT(*) as count
    FROM paper_bets pb
    LEFT JOIN signals s ON pb.signal_id = s.id
    LEFT JOIN games g ON s.game_id = g.id
    WHERE pb.status = 'settled'
    AND pb.placed_at IS NOT NULL
    GROUP BY ROUND(EXTRACT(EPOCH FROM (g.scheduled_at - pb.placed_at)) / 3600)
    HAVING COUNT(*) >= 5
    ORDER BY avg_clv DESC
    LIMIT 1
  `;

  return {
    best_performing_combo: bestCombo[0] ? {
      sport: bestCombo[0].sport,
      market: bestCombo[0].market_type,
      sportsbook: bestCombo[0].sportsbook,
      roi: Number(bestCombo[0].roi),
      count: Number(bestCombo[0].count)
    } : null,
    worst_performing_combo: worstCombo[0] ? {
      sport: worstCombo[0].sport,
      market: worstCombo[0].market_type,
      sportsbook: worstCombo[0].sportsbook,
      roi: Number(worstCombo[0].roi),
      count: Number(worstCombo[0].count)
    } : null,
    optimal_bet_timing: optimalTiming[0] ? {
      hours_before_game: Number(optimalTiming[0].hours_before_game),
      avg_clv: Number(optimalTiming[0].avg_clv || 0),
      count: Number(optimalTiming[0].count)
    } : null
  };
}
