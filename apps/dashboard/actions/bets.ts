'use server';

import { query } from '@/lib/db';

export interface Bet {
  id: number;
  game_id: number;
  player_id?: number;
  market_name: string;
  sportsbook: string;
  line_value?: number;
  odds_american: number;
  stake_amount: number;
  placed_at: string;
  settled_at?: string;
  result?: string;
  profit_loss?: number;
  clv_percent?: number;
  close_odds_american?: number;
  home_team?: string;
  away_team?: string;
  player_name?: string;
}

export async function getRecentBets(limit: number = 100): Promise<Bet[]> {
  const sql = `
    SELECT
      b.id,
      b.game_id,
      b.player_id,
      b.sportsbook,
      b.line_value,
      b.odds_american,
      b.stake_amount,
      b.placed_at,
      b.settled_at,
      b.result,
      b.profit_loss,
      b.clv_percent,
      b.close_odds_american,
      m.name as market_name,
      t_home.name as home_team,
      t_away.name as away_team,
      p.name as player_name
    FROM bets b
    JOIN markets m ON b.market_id = m.id
    JOIN games g ON b.game_id = g.id
    LEFT JOIN teams t_home ON g.home_team_id = t_home.id
    LEFT JOIN teams t_away ON g.away_team_id = t_away.id
    LEFT JOIN players p ON b.player_id = p.id
    ORDER BY b.placed_at DESC
    LIMIT $1
  `;

  const rows = await query<any>(sql, [limit]);
  return rows.map(row => ({
    ...row,
    id: Number(row.id),
    game_id: Number(row.game_id),
    player_id: row.player_id ? Number(row.player_id) : undefined,
    line_value: row.line_value ? Number(row.line_value) : undefined,
    odds_american: Number(row.odds_american),
    stake_amount: Number(row.stake_amount),
    profit_loss: row.profit_loss ? Number(row.profit_loss) : undefined,
    clv_percent: row.clv_percent ? Number(row.clv_percent) : undefined,
    close_odds_american: row.close_odds_american ? Number(row.close_odds_american) : undefined,
  }));
}

export async function getBetStats(): Promise<{
  total_bets: number;
  total_staked: number;
  total_pnl: number;
  roi: number;
  avg_clv: number;
  win_rate: number;
}> {
  const sql = `
    SELECT
      COUNT(*) as total_bets,
      COALESCE(SUM(stake_amount), 0) as total_staked,
      COALESCE(SUM(profit_loss), 0) as total_pnl,
      CASE
        WHEN SUM(stake_amount) > 0
        THEN (SUM(profit_loss) / SUM(stake_amount)) * 100
        ELSE 0
      END as roi,
      COALESCE(AVG(clv_percent), 0) as avg_clv,
      CASE
        WHEN COUNT(*) > 0
        THEN (COUNT(*) FILTER (WHERE result = 'win')::float / COUNT(*)) * 100
        ELSE 0
      END as win_rate
    FROM bets
    WHERE settled_at IS NOT NULL
  `;

  const results = await query<any>(sql);
  const row = results[0];

  if (!row) {
    return {
      total_bets: 0,
      total_staked: 0,
      total_pnl: 0,
      roi: 0,
      avg_clv: 0,
      win_rate: 0
    };
  }

  return {
    total_bets: Number(row.total_bets || 0),
    total_staked: Number(row.total_staked || 0),
    total_pnl: Number(row.total_pnl || 0),
    roi: Number(row.roi || 0),
    avg_clv: Number(row.avg_clv || 0),
    win_rate: Number(row.win_rate || 0),
  };
}
