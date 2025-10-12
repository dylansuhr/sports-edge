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
  page?: number;
  limit?: number;
}

export async function getActiveSignals(filters?: SignalFilters): Promise<{
  signals: Signal[];
  total: number;
  pages: number;
  sportCounts: Record<string, number>;
}> {
  const page = filters?.page || 1;
  const limit = filters?.limit || 50;
  const offset = (page - 1) * limit;

  const filterClauses: string[] = [
    `s.status = 'active'`,
    `s.expires_at > NOW()`
  ];
  const filterParams: any[] = [];

  if (filters?.league && filters.league !== 'all') {
    filterClauses.push(`g.sport = $${filterParams.length + 1}`);
    filterParams.push(filters.league);
  }

  if (filters?.market && filters.market !== 'all') {
    filterClauses.push(`m.name = $${filterParams.length + 1}`);
    filterParams.push(filters.market);
  }

  if (filters?.minEdge && filters.minEdge > 0) {
    filterClauses.push(`s.edge_percent >= $${filterParams.length + 1}`);
    filterParams.push(filters.minEdge);
  }

  const whereClause = filterClauses.join('\n      AND ');
  const baseFrom = `
    FROM signals s
    JOIN markets m ON s.market_id = m.id
    JOIN games g ON s.game_id = g.id
    LEFT JOIN teams t_home ON g.home_team_id = t_home.id
    LEFT JOIN teams t_away ON g.away_team_id = t_away.id
    LEFT JOIN players p ON s.player_id = p.id
    WHERE ${whereClause}
  `;

  const limitPlaceholder = filterParams.length + 1;
  const offsetPlaceholder = filterParams.length + 2;
  const params = [...filterParams, limit, offset];

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
    ${baseFrom}
    ORDER BY s.edge_percent DESC, s.generated_at DESC
    LIMIT $${limitPlaceholder} OFFSET $${offsetPlaceholder}
  `;

  const countSql = `
    SELECT COUNT(*) as total
    ${baseFrom}
  `;

  const countResult = await query<{ total: number }>(countSql, filterParams);
  const total = Number(countResult[0]?.total || 0);
  const pages = total > 0 ? Math.ceil(total / limit) : 0;

  const signalRows = await query<any>(sql, params);

  // Convert numeric fields from strings to numbers
  const signals: Signal[] = signalRows.map(row => ({
    ...row,
    id: Number(row.id),
    game_id: Number(row.game_id),
    player_id: row.player_id ? Number(row.player_id) : undefined,
    line_value: row.line_value ? Number(row.line_value) : undefined,
    odds_american: Number(row.odds_american),
    fair_probability: Number(row.fair_probability),
    implied_probability: Number(row.implied_probability),
    edge_percent: Number(row.edge_percent),
    kelly_fraction: Number(row.kelly_fraction),
    recommended_stake_pct: Number(row.recommended_stake_pct),
  }));

  const sportCountSql = `
    SELECT
      g.sport,
      COUNT(*) as count
    FROM signals s
    JOIN games g ON s.game_id = g.id
    WHERE s.status = 'active'
      AND s.expires_at > NOW()
    GROUP BY g.sport
  `;
  const sportCountRows = await query<{ sport: string; count: number }>(sportCountSql);
  const sportCounts = sportCountRows.reduce<Record<string, number>>((acc, row) => {
    acc[row.sport] = Number(row.count || 0);
    return acc;
  }, {});

  return { signals, total, pages, sportCounts };
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

  const rows = await query<any>(sql, [minEdge]);

  // Convert numeric fields from strings to numbers
  return rows.map(row => ({
    ...row,
    id: Number(row.id),
    game_id: Number(row.game_id),
    player_id: row.player_id ? Number(row.player_id) : undefined,
    line_value: row.line_value ? Number(row.line_value) : undefined,
    odds_american: Number(row.odds_american),
    fair_probability: Number(row.fair_probability),
    implied_probability: Number(row.implied_probability),
    edge_percent: Number(row.edge_percent),
    kelly_fraction: Number(row.kelly_fraction),
    recommended_stake_pct: Number(row.recommended_stake_pct),
  }));
}
