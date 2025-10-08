'use client';

import { useEffect, useState } from 'react';

interface AutomationJob {
  name: string;
  frequency: string; // cron format or description
  intervalMinutes: number; // for countdown
  description: string;
  color: string;
}

const JOBS: AutomationJob[] = [
  {
    name: 'Odds ETL',
    frequency: 'Every 15 minutes',
    intervalMinutes: 15,
    description: 'Fetches latest odds for NFL, NBA, NHL',
    color: 'var(--blue)',
  },
  {
    name: 'Signal Generation',
    frequency: 'Every 20 minutes',
    intervalMinutes: 20,
    description: 'Analyzes odds and generates betting signals',
    color: 'var(--accent)',
  },
  {
    name: 'Settlement',
    frequency: 'Daily at 2:00 AM ET',
    intervalMinutes: 1440, // 24 hours
    description: 'Settles completed bets and updates ELO ratings',
    color: 'var(--purple)',
  },
];

function getNextRunTime(intervalMinutes: number): Date {
  const now = new Date();

  if (intervalMinutes === 1440) {
    // Settlement runs at 2 AM ET (6 AM UTC)
    const next = new Date(now);
    next.setUTCHours(6, 0, 0, 0);

    // If we've passed 2 AM ET today, move to tomorrow
    if (now.getUTCHours() >= 6) {
      next.setUTCDate(next.getUTCDate() + 1);
    }

    return next;
  } else {
    // For interval-based jobs, calculate next interval boundary
    const nowMs = now.getTime();
    const intervalMs = intervalMinutes * 60 * 1000;

    // Find the next interval boundary
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
    <div className="automation-status">
      <div className="status-header">
        <span className="status-dot status-dot-green"></span>
        <span className="status-dot status-dot-yellow"></span>
        <span className="status-dot status-dot-red"></span>
        <span className="terminal-prompt">~/automation</span>
      </div>

      <div className="jobs-grid">
        {JOBS.map((job) => (
          <div key={job.name} className="job-card">
            <div className="job-header">
              <span className="job-name" style={{ color: job.color }}>
                {job.name}
              </span>
              <span className="job-frequency">{job.frequency}</span>
            </div>
            <p className="job-description">{job.description}</p>
            <div className="job-countdown">
              <span className="countdown-label">Next run in:</span>
              <span className="countdown-value" style={{ color: job.color }}>
                {countdowns[job.name] || '...'}
              </span>
            </div>
          </div>
        ))}
      </div>

      <style jsx>{`
        .automation-status {
          background: var(--bg-card);
          border: 1px solid var(--border);
          border-radius: 8px;
          padding: 20px;
          margin-bottom: 24px;
        }

        .status-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 20px;
          padding-bottom: 16px;
          border-bottom: 1px solid var(--border);
        }

        .status-dot {
          width: 12px;
          height: 12px;
          border-radius: 50%;
        }

        .status-dot-red {
          background: var(--red);
        }

        .status-dot-yellow {
          background: var(--yellow);
        }

        .status-dot-green {
          background: var(--green);
        }

        .terminal-prompt {
          font-family: 'JetBrains Mono', monospace;
          color: var(--text-secondary);
          font-size: 14px;
          margin-left: 8px;
        }

        .jobs-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
          gap: 16px;
        }

        .job-card {
          background: var(--bg-tertiary);
          border: 1px solid var(--border);
          border-radius: 6px;
          padding: 16px;
          transition: all 0.2s ease;
        }

        .job-card:hover {
          border-color: var(--accent);
          box-shadow: 0 0 12px var(--accent-glow);
        }

        .job-header {
          display: flex;
          justify-content: space-between;
          align-items: baseline;
          margin-bottom: 8px;
        }

        .job-name {
          font-family: 'JetBrains Mono', monospace;
          font-size: 16px;
          font-weight: 600;
        }

        .job-frequency {
          font-family: 'JetBrains Mono', monospace;
          font-size: 12px;
          color: var(--text-muted);
        }

        .job-description {
          font-size: 13px;
          color: var(--text-secondary);
          margin: 8px 0 12px 0;
          line-height: 1.5;
        }

        .job-countdown {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding-top: 12px;
          border-top: 1px solid var(--border-light);
        }

        .countdown-label {
          font-size: 12px;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .countdown-value {
          font-family: 'JetBrains Mono', monospace;
          font-size: 18px;
          font-weight: 600;
        }
      `}</style>
    </div>
  );
}
