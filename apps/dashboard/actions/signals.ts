'use server';

import { query } from '@/lib/db';

export interface Signal {
  id: number;
  uuid: string;
  game_id: number;
  player_id?: number;
  market_name: string;
  sportsbook: string;
  selection?: string;
  line_value?: number;
  odds_american: number;
  fair_probability: number;
  implied_probability: number;
  edge_percent: number;
  kelly_fraction: number;
  recommended_stake_pct: number;
  confidence_level: string;
  generated_at: string;
  status: string;
  home_team?: string;
  away_team?: string;
  player_name?: string;
  league?: string;
  game_time?: string;
}

export interface SignalFilters {
  league?: string;
  market?: string;
  minEdge?: number;
}

export async function getActiveSignals(filters?: SignalFilters): Promise<Signal[]> {
  const params: any[] = [];
  let paramIndex = 1;

  let sql = `
    SELECT
      s.id,
      s.uuid,
      s.game_id,
      s.player_id,
      s.sportsbook,
      s.line_value,
      s.odds_american,
      s.fair_probability,
      s.implied_probability,
      s.edge_percent,
      s.kelly_fraction,
      s.recommended_stake_pct,
      s.confidence_level,
      s.generated_at,
      s.status,
      m.name as market_name,
      m.category as market_category,
      g.sport as league,
      g.scheduled_at as game_time,
      t_home.name as home_team,
      t_away.name as away_team,
      p.name as player_name,
      (
        SELECT o2.selection
        FROM odds_snapshots o2
        WHERE o2.game_id = s.game_id
          AND o2.market_id = s.market_id
          AND o2.sportsbook = s.sportsbook
          AND o2.odds_american = s.odds_american
        ORDER BY o2.fetched_at DESC
        LIMIT 1
      ) as selection
    FROM signals s
    JOIN markets m ON s.market_id = m.id
    JOIN games g ON s.game_id = g.id
    LEFT JOIN teams t_home ON g.home_team_id = t_home.id
    LEFT JOIN teams t_away ON g.away_team_id = t_away.id
    LEFT JOIN players p ON s.player_id = p.id
    WHERE s.status = 'active'
      AND s.expires_at > NOW()
  `;

  // League filter
  if (filters?.league && filters.league !== 'all') {
    sql += ` AND g.sport = $${paramIndex}`;
    params.push(filters.league);
    paramIndex++;
  }

  // Market filter
  if (filters?.market && filters.market !== 'all') {
    sql += ` AND m.name = $${paramIndex}`;
    params.push(filters.market);
    paramIndex++;
  }

  // Min edge filter
  if (filters?.minEdge && filters.minEdge > 0) {
    sql += ` AND s.edge_percent >= $${paramIndex}`;
    params.push(filters.minEdge);
    paramIndex++;
  }

  sql += `
    ORDER BY s.edge_percent DESC, s.generated_at DESC
    LIMIT 500
  `;

  return await query<Signal>(sql, params);
}

export async function getSignalsByEdge(minEdge: number = 3.0): Promise<Signal[]> {
  const sql = `
    SELECT
      s.id,
      s.uuid,
      s.game_id,
      s.player_id,
      s.sportsbook,
      s.line_value,
      s.odds_american,
      s.fair_probability,
      s.implied_probability,
      s.edge_percent,
      s.kelly_fraction,
      s.recommended_stake_pct,
      s.confidence_level,
      s.generated_at,
      s.status,
      m.name as market_name,
      t_home.name as home_team,
      t_away.name as away_team,
      p.name as player_name
    FROM signals s
    JOIN markets m ON s.market_id = m.id
    JOIN games g ON s.game_id = g.id
    LEFT JOIN teams t_home ON g.home_team_id = t_home.id
    LEFT JOIN teams t_away ON g.away_team_id = t_away.id
    LEFT JOIN players p ON s.player_id = p.id
    WHERE s.status = 'active'
      AND s.edge_percent >= $1
      AND s.expires_at > NOW()
    ORDER BY s.edge_percent DESC
    LIMIT 50
  `;

  return await query<Signal>(sql, [minEdge]);
}
