'use client';

import { useEffect, useState } from 'react';
import styles from './NextActionAlert.module.css';

interface NextAction {
  title: string;
  description: string;
  daysUntil: number;
  estimatedDate: Date;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  actionType: 'none' | 'review' | 'decision' | 'implementation';
  steps?: string[];
}

interface NextActionAlertProps {
  paperBetsSettled: number;
  roiPct: number;
  clvPct: number;
  targetBets: number;
  targetRoi: number;
  targetClv: number;
  betsPerDay: number;
  lineShoppingImplemented: boolean;
  backtestingCompleted: boolean;
}

export default function NextActionAlert({
  paperBetsSettled,
  roiPct,
  clvPct,
  targetBets,
  targetRoi,
  targetClv,
  betsPerDay,
  lineShoppingImplemented,
  backtestingCompleted
}: NextActionAlertProps) {
  const [timeUntilAction, setTimeUntilAction] = useState('');

  const nextAction = getNextAction();

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const target = nextAction.estimatedDate;
      const diff = target.getTime() - now.getTime();

      if (diff <= 0) {
        setTimeUntilAction('NOW');
        return;
      }

      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));

      if (days > 7) {
        setTimeUntilAction(`${days} days`);
      } else if (days > 0) {
        setTimeUntilAction(`${days}d ${hours}h`);
      } else {
        setTimeUntilAction(`${hours} hours`);
      }
    };

    updateTime();
    const interval = setInterval(updateTime, 60000); // Update every minute

    return () => clearInterval(interval);
  }, [nextAction.estimatedDate]);

  function getNextAction(): NextAction {
    const now = new Date();

    // Check if waiting for data accumulation
    if (paperBetsSettled < targetBets) {
      const betsRemaining = targetBets - paperBetsSettled;
      const daysUntil = Math.ceil(betsRemaining / betsPerDay);
      const estimatedDate = new Date(now.getTime() + daysUntil * 24 * 60 * 60 * 1000);

      return {
        title: 'Continue Data Accumulation',
        description: `System is autonomously accumulating paper bets. No action required until ${targetBets} bets milestone.`,
        daysUntil,
        estimatedDate,
        priority: 'low',
        actionType: 'none',
        steps: [
          'Monitor dashboard weekly for anomalies',
          'Check /performance for CLV trends',
          'Verify automation workflows running',
          `Wait for ${betsRemaining} more paper bets to settle`
        ]
      };
    }

    // Check if backtesting needs to be done
    if (!backtestingCompleted) {
      return {
        title: 'Historical Backtesting Required',
        description: '1,000 paper bets milestone reached. Time to validate edge on historical data.',
        daysUntil: 0,
        estimatedDate: now,
        priority: 'urgent',
        actionType: 'implementation',
        steps: [
          'Purchase historical data from The Odds API (2+ years)',
          'Run: python ops/scripts/backtest_historical.py',
          'Target: 1,000+ historical bets, ROI >3%, p-value <0.01',
          'Compare historical ROI vs paper ROI (should be within 2%)',
          'Document results in claude/BACKTEST_RESULTS.md'
        ]
      };
    }

    // Check if performance targets not met
    if (roiPct < targetRoi || clvPct < targetClv) {
      return {
        title: 'Performance Review & Optimization',
        description: 'Statistical sample complete but performance below targets. Diagnosis needed.',
        daysUntil: 0,
        estimatedDate: now,
        priority: 'high',
        actionType: 'review',
        steps: [
          'Review /performance dashboard for underperforming segments',
          'Check which sportsbooks have negative CLV',
          'Analyze which market types (ML/spread/totals) perform worst',
          'Review parameter tuning recommendations',
          'Consider adjusting EDGE_SIDES threshold',
          'May need to iterate on model before real money'
        ]
      };
    }

    // All criteria met - ready for real money
    return {
      title: 'Ready for Real Money Deployment',
      description: 'All validation criteria met. Time to make go/no-go decision.',
      daysUntil: 0,
      estimatedDate: now,
      priority: 'urgent',
      actionType: 'decision',
      steps: [
        'Review complete validation report',
        'Paper ROI: >' + targetRoi + '% ✅',
        'Paper CLV: >' + targetClv + '% ✅',
        'Backtest validated ✅',
        'Statistical significance confirmed ✅',
        '',
        'DECISION: Deploy real money ($1,000 bankroll) or iterate?',
        '',
        'If deploying:',
        '  1. Fund sportsbook accounts',
        '  2. Start with conservative 0.5% stakes',
        '  3. Manual bet placement (no automation)',
        '  4. Track real vs paper performance closely'
      ]
    };
  }

  const getPriorityColor = () => {
    switch (nextAction.priority) {
      case 'urgent': return styles.urgent;
      case 'high': return styles.high;
      case 'medium': return styles.medium;
      case 'low': return styles.low;
    }
  };

  const getPriorityIcon = () => {
    switch (nextAction.priority) {
      case 'urgent': return '🚨';
      case 'high': return '⚠️';
      case 'medium': return '📋';
      case 'low': return '✅';
    }
  };

  const getActionTypeLabel = () => {
    switch (nextAction.actionType) {
      case 'none': return 'Monitoring';
      case 'review': return 'Review Required';
      case 'decision': return 'Decision Point';
      case 'implementation': return 'Action Required';
    }
  };

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  return (
    <div className={`${styles.container} ${getPriorityColor()}`}>
      <div className={styles.header}>
        <div className={styles.iconContainer}>
          <span className={styles.icon}>{getPriorityIcon()}</span>
        </div>
        <div className={styles.headerContent}>
          <div className={styles.headerTop}>
            <h2 className={styles.title}>NEXT ACTION</h2>
            <div className={styles.badges}>
              <span className={`${styles.badge} ${styles[nextAction.actionType]}`}>
                {getActionTypeLabel()}
              </span>
              <span className={`${styles.badge} ${styles[nextAction.priority]}`}>
                {nextAction.priority.toUpperCase()}
              </span>
            </div>
          </div>
          <h3 className={styles.actionTitle}>{nextAction.title}</h3>
        </div>
      </div>

      <div className={styles.timing}>
        <div className={styles.timingItem}>
          <span className={styles.timingLabel}>Time Until Action:</span>
          <span className={styles.timingValue}>{timeUntilAction}</span>
        </div>
        <div className={styles.timingItem}>
          <span className={styles.timingLabel}>Estimated Date:</span>
          <span className={styles.timingValue}>{formatDate(nextAction.estimatedDate)}</span>
        </div>
      </div>

      <div className={styles.description}>
        {nextAction.description}
      </div>

      {nextAction.steps && nextAction.steps.length > 0 && (
        <div className={styles.steps}>
          <h4 className={styles.stepsTitle}>
            {nextAction.actionType === 'none' ? 'Monitoring Checklist:' : 'Action Steps:'}
          </h4>
          <ol className={styles.stepsList}>
            {nextAction.steps.map((step, idx) => (
              step === '' ? (
                <li key={idx} className={styles.separator}></li>
              ) : (
                <li key={idx} className={styles.step}>{step}</li>
              )
            ))}
          </ol>
        </div>
      )}

      {nextAction.actionType === 'none' && (
        <div className={styles.footer}>
          <div className={styles.statusIndicator}>
            <div className={styles.pulse}></div>
            <span>System running autonomously</span>
          </div>
        </div>
      )}
    </div>
  );
}
