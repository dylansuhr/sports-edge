'use client';

import { useEffect, useState } from 'react';
import styles from './AutomationStatus.module.css';

interface AutomationJob {
  name: string;
  frequency: string;
  intervalMinutes: number;
  description: string;
  colorClass: string;
}

const JOBS: AutomationJob[] = [
  {
    name: 'Odds ETL',
    frequency: 'Every 15 minutes',
    intervalMinutes: 15,
    description: 'Fetches latest odds for NFL, NBA, NHL',
    colorClass: styles.colorBlue,
  },
  {
    name: 'Signal Generation',
    frequency: 'Every 20 minutes',
    intervalMinutes: 20,
    description: 'Analyzes odds and generates betting signals',
    colorClass: styles.colorGreen,
  },
  {
    name: 'Settlement',
    frequency: 'Daily at 2:00 AM ET',
    intervalMinutes: 1440,
    description: 'Settles completed bets and updates ELO ratings',
    colorClass: styles.colorPurple,
  },
];

function getNextRunTime(intervalMinutes: number): Date {
  const now = new Date();

  if (intervalMinutes === 1440) {
    const next = new Date(now);
    next.setUTCHours(6, 0, 0, 0);
    if (now.getUTCHours() >= 6) {
      next.setUTCDate(next.getUTCDate() + 1);
    }
    return next;
  } else {
    const nowMs = now.getTime();
    const intervalMs = intervalMinutes * 60 * 1000;
    const intervalsPassed = Math.floor(nowMs / intervalMs);
    const nextMs = (intervalsPassed + 1) * intervalMs;
    return new Date(nextMs);
  }
}

function formatTimeRemaining(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  if (totalSeconds < 60) {
    return `${totalSeconds}s`;
  } else if (totalSeconds < 3600) {
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes}m ${seconds}s`;
  } else {
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  }
}

export default function AutomationStatus() {
  const [countdowns, setCountdowns] = useState<{ [key: string]: string }>({});

  useEffect(() => {
    const updateCountdowns = () => {
      const now = new Date();
      const newCountdowns: { [key: string]: string } = {};

      JOBS.forEach((job) => {
        const nextRun = getNextRunTime(job.intervalMinutes);
        const remaining = nextRun.getTime() - now.getTime();
        newCountdowns[job.name] = formatTimeRemaining(Math.max(0, remaining));
      });

      setCountdowns(newCountdowns);
    };

    updateCountdowns();
    const interval = setInterval(updateCountdowns, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <span className={`${styles.dot} ${styles.dotRed}`}></span>
        <span className={`${styles.dot} ${styles.dotYellow}`}></span>
        <span className={`${styles.dot} ${styles.dotGreen}`}></span>
        <span className={styles.terminalPrompt}>~/automation</span>
      </div>

      <div className={styles.grid}>
        {JOBS.map((job) => (
          <div key={job.name} className={styles.card}>
            <div className={styles.cardHeader}>
              <span className={`${styles.jobName} ${job.colorClass}`}>
                {job.name}
              </span>
              <span className={styles.frequency}>{job.frequency}</span>
            </div>
            <p className={styles.description}>{job.description}</p>
            <div className={styles.countdown}>
              <span className={styles.countdownLabel}>Next run in:</span>
              <span className={`${styles.countdownValue} ${job.colorClass}`}>
                {countdowns[job.name] || '...'}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
