'use server';

import { neon } from '@neondatabase/serverless';

const sql = neon(process.env.DATABASE_READONLY_URL!);

export interface Milestone {
  id: number;
  name: string;
  phase: string;
  description: string;
  criteria: Record<string, any>;
  target_date: string | null;
  completed_at: string | null;
  status: 'pending' | 'in_progress' | 'completed' | 'blocked';
  last_checked: string | null;
  criteria_met: Record<string, any> | null;
  all_criteria_met: boolean | null;
  days_remaining: number | null;
}

export interface MilestoneCheck {
  id: number;
  milestone_id: number;
  checked_at: string;
  criteria_met: Record<string, any>;
  all_criteria_met: boolean;
  notes: string | null;
}

export async function getMilestones(): Promise<Milestone[]> {
  const rows = await sql`
    SELECT
      m.id,
      m.name,
      m.phase,
      m.description,
      m.criteria,
      m.target_date,
      m.completed_at,
      m.status,
      mc.checked_at AS last_checked,
      mc.criteria_met,
      mc.all_criteria_met,
      CASE
        WHEN m.target_date IS NOT NULL THEN m.target_date::date - CURRENT_DATE
        ELSE NULL
      END AS days_remaining
    FROM milestones m
    LEFT JOIN LATERAL (
      SELECT * FROM milestone_checks
      WHERE milestone_id = m.id
      ORDER BY checked_at DESC
      LIMIT 1
    ) mc ON TRUE
    ORDER BY
      CASE m.status
        WHEN 'in_progress' THEN 1
        WHEN 'blocked' THEN 2
        WHEN 'pending' THEN 3
        WHEN 'completed' THEN 4
      END,
      m.target_date NULLS LAST
  `;

  return rows.map(row => ({
    id: row.id,
    name: row.name,
    phase: row.phase,
    description: row.description || '',
    criteria: typeof row.criteria === 'string' ? JSON.parse(row.criteria) : row.criteria,
    target_date: row.target_date,
    completed_at: row.completed_at,
    status: row.status,
    last_checked: row.last_checked,
    criteria_met: row.criteria_met ? (typeof row.criteria_met === 'string' ? JSON.parse(row.criteria_met) : row.criteria_met) : null,
    all_criteria_met: row.all_criteria_met,
    days_remaining: row.days_remaining
  }));
}

export async function getCurrentMilestone(): Promise<Milestone | null> {
  const rows = await sql`
    SELECT
      m.id,
      m.name,
      m.phase,
      m.description,
      m.criteria,
      m.target_date,
      m.completed_at,
      m.status,
      mc.checked_at AS last_checked,
      mc.criteria_met,
      mc.all_criteria_met,
      CASE
        WHEN m.target_date IS NOT NULL THEN m.target_date::date - CURRENT_DATE
        ELSE NULL
      END AS days_remaining
    FROM milestones m
    LEFT JOIN LATERAL (
      SELECT * FROM milestone_checks
      WHERE milestone_id = m.id
      ORDER BY checked_at DESC
      LIMIT 1
    ) mc ON TRUE
    WHERE m.status = 'in_progress'
    ORDER BY m.target_date NULLS LAST
    LIMIT 1
  `;

  if (rows.length === 0) return null;

  const row = rows[0];
  return {
    id: row.id,
    name: row.name,
    phase: row.phase,
    description: row.description || '',
    criteria: typeof row.criteria === 'string' ? JSON.parse(row.criteria) : row.criteria,
    target_date: row.target_date,
    completed_at: row.completed_at,
    status: row.status,
    last_checked: row.last_checked,
    criteria_met: row.criteria_met ? (typeof row.criteria_met === 'string' ? JSON.parse(row.criteria_met) : row.criteria_met) : null,
    all_criteria_met: row.all_criteria_met,
    days_remaining: row.days_remaining
  };
}

export async function getMilestoneChecks(milestoneId: number, limit: number = 10): Promise<MilestoneCheck[]> {
  const rows = await sql`
    SELECT
      id,
      milestone_id,
      checked_at,
      criteria_met,
      all_criteria_met,
      notes
    FROM milestone_checks
    WHERE milestone_id = ${milestoneId}
    ORDER BY checked_at DESC
    LIMIT ${limit}
  `;

  return rows.map(row => ({
    id: row.id,
    milestone_id: row.milestone_id,
    checked_at: row.checked_at,
    criteria_met: typeof row.criteria_met === 'string' ? JSON.parse(row.criteria_met) : row.criteria_met,
    all_criteria_met: row.all_criteria_met,
    notes: row.notes
  }));
}

export async function getSportExpansionMilestones(): Promise<Milestone[]> {
  const rows = await sql`
    SELECT
      m.id,
      m.name,
      m.phase,
      m.description,
      m.criteria,
      m.target_date,
      m.completed_at,
      m.status,
      mc.checked_at AS last_checked,
      mc.criteria_met,
      mc.all_criteria_met,
      NULL AS days_remaining
    FROM milestones m
    LEFT JOIN LATERAL (
      SELECT * FROM milestone_checks
      WHERE milestone_id = m.id
      ORDER BY checked_at DESC
      LIMIT 1
    ) mc ON TRUE
    WHERE m.phase = 'Sport Expansion'
    ORDER BY m.name
  `;

  return rows.map(row => ({
    id: row.id,
    name: row.name,
    phase: row.phase,
    description: row.description || '',
    criteria: typeof row.criteria === 'string' ? JSON.parse(row.criteria) : row.criteria,
    target_date: row.target_date,
    completed_at: row.completed_at,
    status: row.status,
    last_checked: row.last_checked,
    criteria_met: row.criteria_met ? (typeof row.criteria_met === 'string' ? JSON.parse(row.criteria_met) : row.criteria_met) : null,
    all_criteria_met: row.all_criteria_met,
    days_remaining: row.days_remaining
  }));
}

// New function for timeline data
export interface TimelineData {
  paperBetsSettled: number;
  roiPct: number;
  clvPct: number;
  winRate: number;
  avgClv: number;
  targetBets: number;
  targetRoi: number;
  targetClv: number;
  betsPerDay: number;
  daysElapsed: number;
  estimatedDaysRemaining: number;
  startDate: string;
  lineShoppingImplemented: boolean;
  backtestingCompleted: boolean;
}

export async function getTimelineData(): Promise<TimelineData> {
  // Get paper betting stats
  const paperBankroll = await sql`
    SELECT
      balance,
      roi_percent,
      win_rate,
      avg_clv,
      updated_at
    FROM paper_bankroll
    ORDER BY updated_at DESC
    LIMIT 1
  `;

  const paperBetsCount = await sql`
    SELECT COUNT(*) as count
    FROM paper_bets
    WHERE status = 'settled'
  `;

  // Calculate bets per day
  const betsPerDay = await sql`
    SELECT
      COUNT(*) as total_bets,
      EXTRACT(DAY FROM (MAX(settled_at) - MIN(placed_at))) as days_span
    FROM paper_bets
    WHERE status = 'settled'
    AND placed_at IS NOT NULL
    AND settled_at IS NOT NULL
  `;

  // Get earliest paper bet date as start date
  const startDateQuery = await sql`
    SELECT MIN(placed_at) as start_date
    FROM paper_bets
    WHERE placed_at IS NOT NULL
  `;

  // Check if line shopping implemented
  // First check if column exists
  const columnCheck = await sql`
    SELECT EXISTS (
      SELECT FROM information_schema.columns
      WHERE table_name = 'signals'
      AND column_name = 'odds_improvement_pct'
    ) as column_exists
  `;

  let lineShoppingImplemented = false;

  if (columnCheck[0]?.column_exists) {
    const lineShoppingCheck = await sql`
      SELECT COUNT(*) as count
      FROM signals
      WHERE odds_improvement_pct IS NOT NULL
      AND odds_improvement_pct > 0
      AND created_at > NOW() - INTERVAL '14 days'
    `;
    lineShoppingImplemented = Number(lineShoppingCheck[0]?.count || 0) > 0;
  }

  // Check if backtesting completed
  const backtestingCheck = await sql`
    SELECT EXISTS (
      SELECT FROM information_schema.tables
      WHERE table_name = 'backtest_results'
    ) as table_exists
  `;

  const paperBetsSettled = Number(paperBetsCount[0]?.count || 0);
  const targetBets = 1000;
  const targetRoi = 3.0;
  const targetClv = 1.0;

  const roiPct = Number(paperBankroll[0]?.roi_percent || 0);
  const winRate = Number(paperBankroll[0]?.win_rate || 0);
  const avgClv = Number(paperBankroll[0]?.avg_clv || 0);

  const totalBets = Number(betsPerDay[0]?.total_bets || 0);
  const daysSpan = Number(betsPerDay[0]?.days_span || 1);
  const calculatedBetsPerDay = totalBets > 0 && daysSpan > 0 ? totalBets / daysSpan : 5;

  const startDate = startDateQuery[0]?.start_date || new Date().toISOString();
  const daysElapsed = Math.floor(
    (new Date().getTime() - new Date(startDate).getTime()) / (1000 * 60 * 60 * 24)
  );

  const betsRemaining = Math.max(0, targetBets - paperBetsSettled);
  const estimatedDaysRemaining = Math.ceil(betsRemaining / calculatedBetsPerDay);

  const backtestingCompleted = backtestingCheck[0]?.table_exists || false;

  return {
    paperBetsSettled,
    roiPct,
    clvPct: avgClv,
    winRate,
    avgClv,
    targetBets,
    targetRoi,
    targetClv,
    betsPerDay: calculatedBetsPerDay,
    daysElapsed,
    estimatedDaysRemaining,
    startDate,
    lineShoppingImplemented,
    backtestingCompleted
  };
}
