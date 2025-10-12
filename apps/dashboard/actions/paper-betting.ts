'use server';

import { query } from '@/lib/db';

export interface PaperBet {
  id: number;
  signal_id: number;
  stake: number;
  odds_american: number;
  odds_decimal: number;
  status: string;
  result?: string;
  profit_loss?: number;
  placed_at: string;
  settled_at?: string;
  game_id: number;
  market_name: string;
  selection: string;
  edge_percent: number;
  confidence_level: string;
  home_team?: string;
  away_team?: string;
  sport?: string;
  scheduled_at?: string;
}

export interface PaperBankroll {
  balance: number;
  starting_balance: number;
  total_bets: number;
  total_staked: number;
  total_profit_loss: number;
  roi_percent: number;
  win_count: number;
  loss_count: number;
  push_count: number;
  win_rate: number;
  avg_edge?: number;
  avg_clv?: number;
  updated_at: string;
}

export interface PaperBetDecision {
  id: number;
  signal_id: number;
  decision: string;
  reasoning: string;
  confidence_score: number;
  kelly_stake?: number;
  actual_stake?: number;
  edge_percent: number;
  bankroll_at_decision: number;
  exposure_pct: number;
  correlation_risk?: string;
  timestamp: string;
  home_team?: string;
  away_team?: string;
  market_name?: string;
  selection?: string;
}

export interface DailyPerformance {
  date: string;
  bets: number;
  profit_loss: number;
  cumulative_pl: number;
  roi: number;
  win_rate: number;
}

export interface MarketPerformance {
  market_name: string;
  bets: number;
  wins: number;
  losses: number;
  win_rate: number;
  total_pl: number;
  avg_edge: number;
  roi: number;
}

export async function getPaperBankroll(): Promise<PaperBankroll | null> {
  const sql = `
    SELECT *
    FROM paper_bankroll
    ORDER BY id DESC
    LIMIT 1
  `;

  const result = await query<PaperBankroll>(sql);
  return result[0] || null;
}

export async function getRecentPaperBets(limit: number = 50): Promise<PaperBet[]> {
  const sql = `
    SELECT
      pb.*,
      g.sport,
      g.scheduled_at,
      t_home.name as home_team,
      t_away.name as away_team
    FROM paper_bets pb
    JOIN games g ON pb.game_id = g.id
    LEFT JOIN teams t_home ON g.home_team_id = t_home.id
    LEFT JOIN teams t_away ON g.away_team_id = t_away.id
    ORDER BY pb.placed_at DESC
    LIMIT $1
  `;

  return await query<PaperBet>(sql, [limit]);
}

export async function getRecentDecisions(limit: number = 50): Promise<PaperBetDecision[]> {
  const sql = `
    SELECT
      pbd.*,
      g.sport,
      t_home.name as home_team,
      t_away.name as away_team,
      m.name as market_name,
      (
        SELECT o.selection
        FROM odds_snapshots o
        JOIN signals s ON s.game_id = o.game_id AND s.market_id = o.market_id
        WHERE s.id = pbd.signal_id
        ORDER BY o.fetched_at DESC
        LIMIT 1
      ) as selection
    FROM paper_bet_decisions pbd
    JOIN signals s ON pbd.signal_id = s.id
    JOIN games g ON s.game_id = g.id
    JOIN markets m ON s.market_id = m.id
    LEFT JOIN teams t_home ON g.home_team_id = t_home.id
    LEFT JOIN teams t_away ON g.away_team_id = t_away.id
    ORDER BY pbd.timestamp DESC
    LIMIT $1
  `;

  return await query<PaperBetDecision>(sql, [limit]);
}

export async function getDailyPerformance(days: number = 30): Promise<DailyPerformance[]> {
  const sql = `
    WITH daily_bets AS (
      SELECT
        DATE(settled_at) as date,
        COUNT(*) as bets,
        SUM(profit_loss) as profit_loss,
        COUNT(CASE WHEN result = 'won' THEN 1 END) as wins,
        COUNT(CASE WHEN result IN ('won', 'lost') THEN 1 END) as decided_bets
      FROM paper_bets
      WHERE status != 'pending'
        AND settled_at IS NOT NULL
        AND settled_at > NOW() - INTERVAL '${days} days'
      GROUP BY DATE(settled_at)
      ORDER BY date ASC
    )
    SELECT
      date,
      bets,
      profit_loss,
      SUM(profit_loss) OVER (ORDER BY date) as cumulative_pl,
      CASE
        WHEN SUM(CASE WHEN profit_loss < 0 THEN ABS(profit_loss) END) OVER (ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) > 0
        THEN (SUM(profit_loss) OVER (ORDER BY date) / SUM(CASE WHEN profit_loss < 0 THEN ABS(profit_loss) END) OVER (ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) * 100)
        ELSE 0
      END as roi,
      CASE
        WHEN decided_bets > 0
        THEN (wins::float / decided_bets * 100)
        ELSE 0
      END as win_rate
    FROM daily_bets
    ORDER BY date ASC
  `;

  return await query<DailyPerformance>(sql);
}

export async function getMarketPerformance(): Promise<MarketPerformance[]> {
  const sql = `
    SELECT
      market_name,
      COUNT(*) as bets,
      COUNT(CASE WHEN result = 'won' THEN 1 END) as wins,
      COUNT(CASE WHEN result = 'lost' THEN 1 END) as losses,
      CASE
        WHEN COUNT(CASE WHEN result IN ('won', 'lost') THEN 1 END) > 0
        THEN ROUND((COUNT(CASE WHEN result = 'won' THEN 1 END)::float /
             COUNT(CASE WHEN result IN ('won', 'lost') THEN 1 END) * 100)::numeric, 1)
        ELSE 0
      END as win_rate,
      ROUND(SUM(profit_loss)::numeric, 2) as total_pl,
      ROUND(AVG(edge_percent)::numeric, 2) as avg_edge,
      CASE
        WHEN SUM(stake) > 0
        THEN ROUND((SUM(profit_loss) / SUM(stake) * 100)::numeric, 1)
        ELSE 0
      END as roi
    FROM paper_bets
    WHERE status != 'pending'
    GROUP BY market_name
    HAVING COUNT(*) >= 3
    ORDER BY total_pl DESC
  `;

  return await query<MarketPerformance>(sql);
}

export async function getPaperBettingStats(): Promise<{
  total_value: number;
  avg_confidence: number;
  top_market: string;
  recent_streak: string;
}> {
  const sql = `
    WITH stats AS (
      SELECT
        SUM(stake) as total_value,
        AVG(
          CASE
            WHEN confidence_level = 'high' THEN 0.8
            WHEN confidence_level = 'medium' THEN 0.5
            ELSE 0.3
          END
        ) as avg_confidence
      FROM paper_bets
      WHERE status = 'pending'
    ),
    top_market AS (
      SELECT market_name
      FROM paper_bets
      WHERE status != 'pending'
      GROUP BY market_name
      ORDER BY SUM(profit_loss) DESC
      LIMIT 1
    ),
    recent_results AS (
      SELECT result
      FROM paper_bets
      WHERE status != 'pending'
      ORDER BY settled_at DESC
      LIMIT 5
    )
    SELECT
      COALESCE(s.total_value, 0) as total_value,
      COALESCE(s.avg_confidence, 0) as avg_confidence,
      COALESCE(tm.market_name, 'N/A') as top_market,
      (
        SELECT string_agg(
          CASE
            WHEN result = 'won' THEN 'W'
            WHEN result = 'lost' THEN 'L'
            WHEN result = 'push' THEN 'P'
            ELSE 'V'
          END,
          ''
          ORDER BY settled_at DESC
        )
        FROM (
          SELECT result, settled_at
          FROM paper_bets
          WHERE status != 'pending'
          ORDER BY settled_at DESC
          LIMIT 5
        ) recent
      ) as recent_streak
    FROM stats s
    CROSS JOIN top_market tm
  `;

  const result = await query<{
    total_value: number;
    avg_confidence: number;
    top_market: string;
    recent_streak: string;
  }>(sql);

  return result[0] || {
    total_value: 0,
    avg_confidence: 0,
    top_market: 'N/A',
    recent_streak: ''
  };
}
