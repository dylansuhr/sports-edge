'use client';

import { useMemo } from 'react';
import styles from './ActionTimelineCalendar.module.css';

interface TimelineAction {
  week: number;
  date: Date;
  title: string;
  description: string;
  type: 'automated' | 'manual' | 'milestone' | 'seasonal';
  status: 'completed' | 'current' | 'upcoming';
  actionRequired: boolean;
}

interface ActionTimelineCalendarProps {
  startDate: Date;
  paperBetsSettled: number;
  betsPerDay: number;
}

export default function ActionTimelineCalendar({
  startDate,
  paperBetsSettled,
  betsPerDay = 5
}: ActionTimelineCalendarProps) {
  const timelineActions = useMemo(() => {
    const actions: TimelineAction[] = [];
    const now = new Date();

    // Calculate weeks elapsed
    const weeksElapsed = Math.floor((now.getTime() - startDate.getTime()) / (7 * 24 * 60 * 60 * 1000));

    // Calculate estimated weeks to 1000 bets
    const betsRemaining = Math.max(0, 1000 - paperBetsSettled);
    const daysRemaining = Math.ceil(betsRemaining / betsPerDay);
    const weeksRemaining = Math.ceil(daysRemaining / 7);

    // Helper to get date for week offset
    const getWeekDate = (weekOffset: number) => {
      const date = new Date(startDate);
      date.setDate(date.getDate() + (weekOffset * 7));
      return date;
    };

    // Helper to determine status
    const getStatus = (weekNum: number): 'completed' | 'current' | 'upcoming' => {
      if (weekNum < weeksElapsed) return 'completed';
      if (weekNum === weeksElapsed) return 'current';
      return 'upcoming';
    };

    // Week 1: System Launch
    actions.push({
      week: 0,
      date: startDate,
      title: 'System Launch',
      description: 'Automated workflows activated, paper betting begins',
      type: 'milestone',
      status: getStatus(0),
      actionRequired: false
    });

    // Every 4 weeks: Performance review (automated)
    for (let week = 4; week <= weeksElapsed + weeksRemaining; week += 4) {
      actions.push({
        week,
        date: getWeekDate(week),
        title: 'Automated Performance Review',
        description: 'Weekly analysis runs, parameters auto-tuned if needed',
        type: 'automated',
        status: getStatus(week),
        actionRequired: false
      });
    }

    // Week 8: First manual check-in
    if (weeksElapsed + weeksRemaining >= 8) {
      actions.push({
        week: 8,
        date: getWeekDate(8),
        title: 'First Check-In',
        description: 'Review dashboard, verify automation health, check for anomalies',
        type: 'manual',
        status: getStatus(8),
        actionRequired: true
      });
    }

    // Seasonal events
    const nflPlayoffsWeek = getWeekOffsetForDate(startDate, new Date('2026-01-11'));
    if (nflPlayoffsWeek <= weeksElapsed + weeksRemaining + 4) {
      actions.push({
        week: nflPlayoffsWeek,
        date: new Date('2026-01-11'),
        title: 'NFL Playoffs Begin',
        description: 'Playoff games may have different betting dynamics, monitor CLV',
        type: 'seasonal',
        status: getStatus(nflPlayoffsWeek),
        actionRequired: false
      });
    }

    const nbaSeasonWeek = getWeekOffsetForDate(startDate, new Date('2025-10-22'));
    if (nbaSeasonWeek >= 0 && nbaSeasonWeek <= weeksElapsed + weeksRemaining + 4) {
      actions.push({
        week: nbaSeasonWeek,
        date: new Date('2025-10-22'),
        title: 'NBA Season Starts',
        description: 'NBA available for addition if NFL edge validated',
        type: 'seasonal',
        status: getStatus(nbaSeasonWeek),
        actionRequired: false
      });
    }

    const nhlSeasonWeek = getWeekOffsetForDate(startDate, new Date('2025-10-08'));
    if (nhlSeasonWeek >= 0 && nhlSeasonWeek <= weeksElapsed + weeksRemaining + 4) {
      actions.push({
        week: nhlSeasonWeek,
        date: new Date('2025-10-08'),
        title: 'NHL Season Starts',
        description: 'NHL available for addition if NFL edge validated',
        type: 'seasonal',
        status: getStatus(nhlSeasonWeek),
        actionRequired: false
      });
    }

    // Milestone: 500 bets
    const week500 = Math.floor((500 - (paperBetsSettled >= 500 ? 500 : 0)) / (betsPerDay * 7)) + weeksElapsed;
    if (paperBetsSettled < 500 && week500 <= weeksElapsed + weeksRemaining) {
      actions.push({
        week: week500,
        date: getWeekDate(week500),
        title: '500 Paper Bets Milestone',
        description: 'Half-way to statistical significance, review trends',
        type: 'milestone',
        status: getStatus(week500),
        actionRequired: false
      });
    }

    // Milestone: 1000 bets (key milestone)
    const week1000 = weeksElapsed + weeksRemaining;
    actions.push({
      week: week1000,
      date: getWeekDate(week1000),
      title: '1,000 Bets Milestone - ACTION REQUIRED',
      description: 'Statistical significance reached. Purchase historical data, run backtest',
      type: 'milestone',
      status: getStatus(week1000),
      actionRequired: true
    });

    // Post-1000: Backtesting
    actions.push({
      week: week1000 + 2,
      date: getWeekDate(week1000 + 2),
      title: 'Historical Backtesting',
      description: 'Run backtest on 2+ years historical data, validate edge',
      type: 'manual',
      status: getStatus(week1000 + 2),
      actionRequired: true
    });

    // Post-backtest: Decision point
    actions.push({
      week: week1000 + 4,
      date: getWeekDate(week1000 + 4),
      title: 'Go/No-Go Decision',
      description: 'Review paper + backtest results. Decide: real money or iterate',
      type: 'milestone',
      status: getStatus(week1000 + 4),
      actionRequired: true
    });

    // Sort by week
    return actions.sort((a, b) => a.week - b.week);
  }, [startDate, paperBetsSettled, betsPerDay]);

  // Helper function
  function getWeekOffsetForDate(start: Date, target: Date): number {
    return Math.floor((target.getTime() - start.getTime()) / (7 * 24 * 60 * 60 * 1000));
  }

  const getTypeIcon = (type: TimelineAction['type']) => {
    switch (type) {
      case 'automated': return '🤖';
      case 'manual': return '👤';
      case 'milestone': return '🎯';
      case 'seasonal': return '📅';
    }
  };

  const getTypeLabel = (type: TimelineAction['type']) => {
    switch (type) {
      case 'automated': return 'Automated';
      case 'manual': return 'Your Action';
      case 'milestone': return 'Milestone';
      case 'seasonal': return 'Seasonal';
    }
  };

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>Action Timeline</h2>
        <p className={styles.subtitle}>Week-by-week roadmap with intervention points</p>
      </div>

      <div className={styles.legend}>
        <div className={styles.legendItem}>
          <span className={styles.legendIcon}>🤖</span>
          <span>Automated</span>
        </div>
        <div className={styles.legendItem}>
          <span className={styles.legendIcon}>👤</span>
          <span>Your Action</span>
        </div>
        <div className={styles.legendItem}>
          <span className={styles.legendIcon}>🎯</span>
          <span>Milestone</span>
        </div>
        <div className={styles.legendItem}>
          <span className={styles.legendIcon}>📅</span>
          <span>Seasonal</span>
        </div>
      </div>

      <div className={styles.timeline}>
        {timelineActions.map((action, idx) => (
          <div
            key={idx}
            className={`${styles.event} ${styles[action.status]} ${action.actionRequired ? styles.actionRequired : ''}`}
          >
            <div className={styles.eventMarker}>
              <div className={styles.markerDot} />
              {idx < timelineActions.length - 1 && <div className={styles.markerLine} />}
            </div>

            <div className={styles.eventContent}>
              <div className={styles.eventHeader}>
                <div className={styles.eventMeta}>
                  <span className={styles.weekLabel}>Week {action.week}</span>
                  <span className={styles.dateLabel}>{formatDate(action.date)}</span>
                </div>
                <div className={`${styles.typeBadge} ${styles[action.type]}`}>
                  <span className={styles.typeIcon}>{getTypeIcon(action.type)}</span>
                  <span className={styles.typeLabel}>{getTypeLabel(action.type)}</span>
                </div>
              </div>

              <h3 className={styles.eventTitle}>{action.title}</h3>
              <p className={styles.eventDescription}>{action.description}</p>

              {action.actionRequired && action.status === 'upcoming' && (
                <div className={styles.actionBadge}>
                  ⚠️ Action Required
                </div>
              )}

              {action.status === 'current' && (
                <div className={styles.currentBadge}>
                  ▶ In Progress
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
