'use client';

import { useEffect, useState, CSSProperties } from 'react';

interface AutomationJob {
  name: string;
  frequency: string;
  intervalMinutes: number;
  description: string;
  color: string;
}

const JOBS: AutomationJob[] = [
  {
    name: 'Odds ETL',
    frequency: 'Every 15 minutes',
    intervalMinutes: 15,
    description: 'Fetches latest odds for NFL, NBA, NHL',
    color: '#00a8ff',
  },
  {
    name: 'Signal Generation',
    frequency: 'Every 20 minutes',
    intervalMinutes: 20,
    description: 'Analyzes odds and generates betting signals',
    color: '#00ff88',
  },
  {
    name: 'Settlement',
    frequency: 'Daily at 2:00 AM ET',
    intervalMinutes: 1440,
    description: 'Settles completed bets and updates ELO ratings',
    color: '#a855f7',
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

const styles: { [key: string]: CSSProperties } = {
  container: {
    background: '#141414',
    border: '1px solid #2a2a2a',
    borderRadius: '8px',
    padding: '20px',
    marginBottom: '24px',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '20px',
    paddingBottom: '16px',
    borderBottom: '1px solid #2a2a2a',
  },
  dot: {
    width: '12px',
    height: '12px',
    borderRadius: '50%',
  },
  dotRed: { backgroundColor: '#ff4444' },
  dotYellow: { backgroundColor: '#fbbf24' },
  dotGreen: { backgroundColor: '#00ff88' },
  terminalPrompt: {
    fontFamily: "'JetBrains Mono', monospace",
    color: '#a0a0a0',
    fontSize: '14px',
    marginLeft: '8px',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    gap: '16px',
  },
  card: {
    background: '#1a1a1a',
    border: '1px solid #2a2a2a',
    borderRadius: '6px',
    padding: '16px',
    transition: 'all 0.2s ease',
  },
  cardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'baseline',
    marginBottom: '8px',
  },
  jobName: {
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: '16px',
    fontWeight: 600,
  },
  frequency: {
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: '12px',
    color: '#666666',
  },
  description: {
    fontSize: '13px',
    color: '#a0a0a0',
    margin: '8px 0 12px 0',
    lineHeight: 1.5,
  },
  countdown: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: '12px',
    borderTop: '1px solid #333333',
  },
  countdownLabel: {
    fontSize: '12px',
    color: '#666666',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.5px',
  },
  countdownValue: {
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: '18px',
    fontWeight: 600,
  },
};

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
    <div style={styles.container}>
      <div style={styles.header}>
        <span style={{ ...styles.dot, ...styles.dotRed }}></span>
        <span style={{ ...styles.dot, ...styles.dotYellow }}></span>
        <span style={{ ...styles.dot, ...styles.dotGreen }}></span>
        <span style={styles.terminalPrompt}>~/automation</span>
      </div>

      <div style={styles.grid}>
        {JOBS.map((job) => (
          <div key={job.name} style={styles.card}>
            <div style={styles.cardHeader}>
              <span style={{ ...styles.jobName, color: job.color }}>
                {job.name}
              </span>
              <span style={styles.frequency}>{job.frequency}</span>
            </div>
            <p style={styles.description}>{job.description}</p>
            <div style={styles.countdown}>
              <span style={styles.countdownLabel}>Next run in:</span>
              <span style={{ ...styles.countdownValue, color: job.color }}>
                {countdowns[job.name] || '...'}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
