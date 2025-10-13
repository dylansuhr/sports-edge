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
