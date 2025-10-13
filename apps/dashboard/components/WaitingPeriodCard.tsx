'use client';

import { useEffect, useState } from 'react';
import styles from './WaitingPeriodCard.module.css';

interface WaitingPeriodProps {
  paperBetsSettled: number;
  targetBets: number;
  roiPct: number;
  targetRoi: number;
  clvPct: number;
  targetClv: number;
  daysElapsed: number;
  estimatedDaysRemaining: number;
}

export default function WaitingPeriodCard({
  paperBetsSettled,
  targetBets,
  roiPct,
  targetRoi,
  clvPct,
  targetClv,
  daysElapsed,
  estimatedDaysRemaining
}: WaitingPeriodProps) {
  const [currentDay, setCurrentDay] = useState(daysElapsed);

  useEffect(() => {
    // Update day counter every 24 hours
    const interval = setInterval(() => {
      setCurrentDay(prev => prev + 1);
    }, 86400000); // 24 hours in ms

    return () => clearInterval(interval);
  }, []);

  const totalDays = daysElapsed + estimatedDaysRemaining;
  const progressPct = Math.round((daysElapsed / totalDays) * 100);
  const betsProgressPct = Math.round((paperBetsSettled / targetBets) * 100);

  const getPhaseDescription = () => {
    if (paperBetsSettled < 100) {
      return '📊 Early Calibration - Model learning from initial games';
    } else if (paperBetsSettled < 500) {
      return '🔄 Data Accumulation - Building statistical sample';
    } else if (paperBetsSettled < 1000) {
      return '📈 Nearing Validation - Approaching significance threshold';
    } else {
      return '✅ Statistical Sample Complete - Ready for analysis';
    }
  };

  const getActionGuidance = () => {
    if (paperBetsSettled < 1000) {
      return {
        title: '⏳ Current Action: Wait & Monitor',
        description: 'Your system is autonomously accumulating data. No manual intervention needed.',
        details: [
          'Paper betting AI placing ~5 bets/day',
          'ELO ratings updating after each game',
          'CLV tracking running automatically',
          'Weekly performance analysis generating insights'
        ]
      };
    } else if (roiPct < targetRoi || clvPct < targetClv) {
      return {
        title: '🔍 Current Action: Review & Diagnose',
        description: 'Statistical sample reached but performance below targets.',
        details: [
          'Review /performance dashboard for issues',
          'Check parameter tuning recommendations',
          'Consider edge threshold adjustments',
          'Analyze underperforming markets'
        ]
      };
    } else {
      return {
        title: '🎉 Current Action: Proceed to Backtesting',
        description: 'Validation criteria met! Ready for historical backtesting.',
        details: [
          'Purchase historical data (2+ years)',
          'Run backtest script on historical odds',
          'Validate edge on 1,000+ historical bets',
          'Compare paper vs backtest performance'
        ]
      };
    }
  };

  const guidance = getActionGuidance();

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <div className={styles.icon}>⏳</div>
        <div>
          <h2 className={styles.title}>Data Accumulation Phase</h2>
          <p className={styles.subtitle}>{getPhaseDescription()}</p>
        </div>
      </div>

      <div className={styles.timeline}>
        <div className={styles.timelineHeader}>
          <span className={styles.dayCounter}>Day {currentDay} of ~{totalDays}</span>
          <span className={styles.percentage}>{progressPct}%</span>
        </div>
        <div className={styles.progressBar}>
          <div
            className={styles.progressFill}
            style={{ width: `${progressPct}%` }}
          />
        </div>
        <div className={styles.timelineFooter}>
          <span>Started: {daysElapsed} days ago</span>
          <span>Est. completion: {estimatedDaysRemaining} days</span>
        </div>
      </div>

      <div className={styles.metrics}>
        <div className={styles.metric}>
          <div className={styles.metricHeader}>
            <span className={styles.metricLabel}>Paper Bets</span>
            <span className={styles.metricValue}>{paperBetsSettled} / {targetBets}</span>
          </div>
          <div className={styles.metricBar}>
            <div
              className={styles.metricFill}
              style={{ width: `${Math.min(betsProgressPct, 100)}%` }}
            />
          </div>
          <span className={styles.metricNote}>{betsProgressPct}% complete</span>
        </div>

        <div className={styles.metric}>
          <div className={styles.metricHeader}>
            <span className={styles.metricLabel}>ROI Target</span>
            <span className={`${styles.metricValue} ${roiPct >= targetRoi ? styles.met : styles.notMet}`}>
              {roiPct.toFixed(2)}% / {targetRoi}%
            </span>
          </div>
          <div className={styles.metricBar}>
            <div
              className={`${styles.metricFill} ${roiPct >= targetRoi ? styles.success : ''}`}
              style={{ width: `${Math.min((roiPct / targetRoi) * 100, 100)}%` }}
            />
          </div>
          <span className={styles.metricNote}>
            {roiPct >= targetRoi ? '✅ Target met' : `${(targetRoi - roiPct).toFixed(2)}% to go`}
          </span>
        </div>

        <div className={styles.metric}>
          <div className={styles.metricHeader}>
            <span className={styles.metricLabel}>CLV Target</span>
            <span className={`${styles.metricValue} ${clvPct >= targetClv ? styles.met : styles.notMet}`}>
              {clvPct.toFixed(2)}% / {targetClv}%
            </span>
          </div>
          <div className={styles.metricBar}>
            <div
              className={`${styles.metricFill} ${clvPct >= targetClv ? styles.success : ''}`}
              style={{ width: `${Math.min((clvPct / targetClv) * 100, 100)}%` }}
            />
          </div>
          <span className={styles.metricNote}>
            {clvPct >= targetClv ? '✅ Target met' : `${(targetClv - clvPct).toFixed(2)}% to go`}
          </span>
        </div>
      </div>

      <div className={styles.actionBox}>
        <div className={styles.actionHeader}>
          <h3 className={styles.actionTitle}>{guidance.title}</h3>
          <span className={styles.badge}>AUTO</span>
        </div>
        <p className={styles.actionDescription}>{guidance.description}</p>
        <ul className={styles.actionList}>
          {guidance.details.map((detail, idx) => (
            <li key={idx}>{detail}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
