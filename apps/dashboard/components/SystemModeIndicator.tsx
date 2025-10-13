'use client';

import styles from './SystemModeIndicator.module.css';

interface SystemModeIndicatorProps {
  paperBetsSettled: number;
  targetBets: number;
  roiPct: number;
  targetRoi: number;
  clvPct: number;
  targetClv: number;
  backtestingCompleted: boolean;
  daysUntilAction: number;
  actionNeeded: boolean;
}

type SystemMode = 'waiting' | 'action' | 'ready' | 'review';

export default function SystemModeIndicator({
  paperBetsSettled,
  targetBets,
  roiPct,
  targetRoi,
  clvPct,
  targetClv,
  backtestingCompleted,
  daysUntilAction,
  actionNeeded
}: SystemModeIndicatorProps) {

  const getSystemMode = (): SystemMode => {
    if (actionNeeded) return 'action';

    if (paperBetsSettled >= targetBets &&
        backtestingCompleted &&
        roiPct >= targetRoi &&
        clvPct >= targetClv) {
      return 'ready';
    }

    if (paperBetsSettled >= targetBets &&
        backtestingCompleted &&
        (roiPct < targetRoi || clvPct < targetClv)) {
      return 'review';
    }

    return 'waiting';
  };

  const mode = getSystemMode();

  const getModeConfig = () => {
    switch (mode) {
      case 'waiting':
        return {
          icon: '⏳',
          title: 'WAITING MODE',
          subtitle: 'Data Accumulation Phase',
          description: `System is autonomously accumulating data. ${daysUntilAction} days until manual intervention needed.`,
          color: 'cyan',
          statusText: 'Autonomous Operation'
        };
      case 'action':
        return {
          icon: '⚠️',
          title: 'ACTION REQUIRED',
          subtitle: 'Manual Intervention Needed',
          description: 'Milestone reached! Time to run historical backtesting and validate edge.',
          color: 'warning',
          statusText: 'Your Action Needed'
        };
      case 'ready':
        return {
          icon: '🎉',
          title: 'SYSTEM READY',
          subtitle: 'Validated Edge Confirmed',
          description: 'All criteria met. System validated and ready for real money deployment decision.',
          color: 'success',
          statusText: 'Ready for Deployment'
        };
      case 'review':
        return {
          icon: '🔍',
          title: 'REVIEW REQUIRED',
          subtitle: 'Performance Below Target',
          description: 'Statistical sample complete but performance metrics below targets. Review needed.',
          color: 'error',
          statusText: 'Needs Review'
        };
    }
  };

  const config = getModeConfig();

  return (
    <div className={`${styles.container} ${styles[config.color]}`}>
      <div className={styles.iconSection}>
        <div className={styles.iconCircle}>
          <span className={styles.icon}>{config.icon}</span>
        </div>
        <div className={styles.pulse} />
      </div>

      <div className={styles.content}>
        <div className={styles.header}>
          <div>
            <h2 className={styles.title}>{config.title}</h2>
            <p className={styles.subtitle}>{config.subtitle}</p>
          </div>
          <div className={`${styles.statusBadge} ${styles[config.color]}`}>
            {config.statusText}
          </div>
        </div>

        <p className={styles.description}>{config.description}</p>

        <div className={styles.metrics}>
          <div className={styles.metric}>
            <span className={styles.metricLabel}>Progress</span>
            <span className={styles.metricValue}>
              {paperBetsSettled} / {targetBets} bets
            </span>
          </div>
          <div className={styles.metric}>
            <span className={styles.metricLabel}>ROI</span>
            <span className={`${styles.metricValue} ${roiPct >= targetRoi ? styles.met : ''}`}>
              {roiPct.toFixed(2)}%
            </span>
          </div>
          <div className={styles.metric}>
            <span className={styles.metricLabel}>CLV</span>
            <span className={`${styles.metricValue} ${clvPct >= targetClv ? styles.met : ''}`}>
              {clvPct.toFixed(2)}%
            </span>
          </div>
          <div className={styles.metric}>
            <span className={styles.metricLabel}>Backtest</span>
            <span className={styles.metricValue}>
              {backtestingCompleted ? '✅' : '❌'}
            </span>
          </div>
        </div>

        {mode === 'waiting' && (
          <div className={styles.footer}>
            <span className={styles.footerText}>
              ✓ Automation active · ✓ Paper betting running · ✓ No action required
            </span>
          </div>
        )}

        {mode === 'action' && (
          <div className={styles.actionFooter}>
            <a href="/progress" className={styles.actionButton}>
              View Next Steps →
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
