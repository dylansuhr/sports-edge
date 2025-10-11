'use client';

import { ModelReadiness } from '@/actions/performance';
import styles from './ModelReadinessCard.module.css';

interface ModelReadinessCardProps {
  readiness: ModelReadiness;
}

export default function ModelReadinessCard({ readiness }: ModelReadinessCardProps) {
  const getStatusColor = () => {
    switch (readiness.status) {
      case 'ready':
        return styles.ready;
      case 'monitor':
        return styles.monitor;
      case 'not_ready':
        return styles.notReady;
      case 'insufficient_data':
        return styles.insufficientData;
      default:
        return '';
    }
  };

  const getStatusIcon = () => {
    switch (readiness.status) {
      case 'ready':
        return '✅';
      case 'monitor':
        return '⚠️';
      case 'not_ready':
        return '❌';
      case 'insufficient_data':
        return '📊';
      default:
        return '';
    }
  };

  const getStatusLabel = () => {
    switch (readiness.status) {
      case 'ready':
        return 'READY FOR BETTING';
      case 'monitor':
        return 'MONITOR CLOSELY';
      case 'not_ready':
        return 'NOT READY';
      case 'insufficient_data':
        return 'COLLECTING DATA';
      default:
        return '';
    }
  };

  return (
    <div className={`${styles.card} ${getStatusColor()}`}>
      <div className={styles.header}>
        <span className={styles.icon}>{getStatusIcon()}</span>
        <h2 className={styles.title}>{getStatusLabel()}</h2>
      </div>

      <p className={styles.message}>{readiness.message}</p>

      <div className={styles.metrics}>
        <div className={styles.metric}>
          <div className={styles.metricLabel}>Average CLV</div>
          <div className={styles.metricValue}>
            {readiness.clv > 0 ? '+' : ''}{readiness.clv.toFixed(2)}%
          </div>
        </div>

        <div className={styles.metric}>
          <div className={styles.metricLabel}>Beat Closing %</div>
          <div className={styles.metricValue}>{readiness.beat_close_pct.toFixed(1)}%</div>
        </div>

        <div className={styles.metric}>
          <div className={styles.metricLabel}>Signals with CLV</div>
          <div className={styles.metricValue}>
            {readiness.total_signals} / {readiness.min_signals_needed}
          </div>
        </div>
      </div>

      {readiness.status === 'insufficient_data' && (
        <div className={styles.progress}>
          <div
            className={styles.progressBar}
            style={{ width: `${(readiness.total_signals / readiness.min_signals_needed) * 100}%` }}
          />
        </div>
      )}
    </div>
  );
}
