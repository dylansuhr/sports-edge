'use client';

import { PerformanceMetrics, SportPerformance, MarketPerformance } from '@/actions/performance';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import styles from './PerformanceCharts.module.css';

interface PerformanceChartsProps {
  dailyData: PerformanceMetrics[];
  sportData: SportPerformance[];
  marketData: MarketPerformance[];
  overall: any;
}

export default function PerformanceCharts({
  dailyData,
  sportData,
  marketData,
  overall
}: PerformanceChartsProps) {
  // Format date for display
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return `${date.getMonth() + 1}/${date.getDate()}`;
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className={styles.tooltip}>
          <p className={styles.tooltipLabel}>{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }}>
              {entry.name}: {typeof entry.value === 'number' ? entry.value.toFixed(2) : entry.value}
              {entry.name.includes('CLV') || entry.name.includes('%') ? '%' : ''}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className={styles.container}>
      {/* Daily CLV Trend */}
      <div className={styles.chartSection}>
        <h2 className={styles.chartTitle}>Closing Line Value Trend (30 Days)</h2>
        <p className={styles.chartSubtitle}>
          Positive CLV indicates the model is finding value that beats closing lines
        </p>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={dailyData.map(d => ({ ...d, date: formatDate(d.date) }))}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis
              dataKey="date"
              stroke="#888"
              style={{ fontSize: '12px' }}
            />
            <YAxis
              stroke="#888"
              style={{ fontSize: '12px' }}
              label={{ value: 'CLV %', angle: -90, position: 'insideLeft', fill: '#888' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <ReferenceLine y={0} stroke="#666" strokeDasharray="3 3" />
            <ReferenceLine y={0.5} stroke="#22c55e" strokeDasharray="3 3" label="Target (0.5%)" />
            <Line
              type="monotone"
              dataKey="avg_clv"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={{ fill: '#3b82f6', r: 4 }}
              name="Avg CLV"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Beat Closing % Trend */}
      <div className={styles.chartSection}>
        <h2 className={styles.chartTitle}>Beat Closing Line % (30 Days)</h2>
        <p className={styles.chartSubtitle}>
          % of signals that beat the closing line (target: 52%+)
        </p>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={dailyData.map(d => ({ ...d, date: formatDate(d.date) }))}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis
              dataKey="date"
              stroke="#888"
              style={{ fontSize: '12px' }}
            />
            <YAxis
              stroke="#888"
              style={{ fontSize: '12px' }}
              domain={[0, 100]}
              label={{ value: 'Beat Close %', angle: -90, position: 'insideLeft', fill: '#888' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <ReferenceLine y={50} stroke="#666" strokeDasharray="3 3" label="Breakeven" />
            <ReferenceLine y={52} stroke="#22c55e" strokeDasharray="3 3" label="Target (52%)" />
            <Line
              type="monotone"
              dataKey="beat_close_pct"
              stroke="#f59e0b"
              strokeWidth={2}
              dot={{ fill: '#f59e0b', r: 4 }}
              name="Beat Close %"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Performance by Sport */}
      <div className={styles.chartSection}>
        <h2 className={styles.chartTitle}>Performance by Sport (Last 14 Days)</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={sportData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis
              dataKey="sport"
              stroke="#888"
              style={{ fontSize: '12px', textTransform: 'uppercase' }}
            />
            <YAxis
              stroke="#888"
              style={{ fontSize: '12px' }}
              label={{ value: 'CLV %', angle: -90, position: 'insideLeft', fill: '#888' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <ReferenceLine y={0} stroke="#666" />
            <Bar dataKey="avg_clv" fill="#3b82f6" name="Avg CLV" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Performance by Market */}
      <div className={styles.chartSection}>
        <h2 className={styles.chartTitle}>Performance by Market (Last 14 Days)</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={marketData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis
              dataKey="market"
              stroke="#888"
              style={{ fontSize: '12px' }}
            />
            <YAxis
              stroke="#888"
              style={{ fontSize: '12px' }}
              label={{ value: 'CLV %', angle: -90, position: 'insideLeft', fill: '#888' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <ReferenceLine y={0} stroke="#666" />
            <Bar dataKey="avg_clv" fill="#f59e0b" name="Avg CLV" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Overall Summary Stats */}
      {overall && (
        <div className={styles.statsGrid}>
          <div className={styles.statCard}>
            <div className={styles.statLabel}>Median CLV</div>
            <div className={styles.statValue}>
              {overall.median_clv > 0 ? '+' : ''}{overall.median_clv}%
            </div>
          </div>
          <div className={styles.statCard}>
            <div className={styles.statLabel}>CLV Std Dev</div>
            <div className={styles.statValue}>{overall.stddev_clv}%</div>
          </div>
          <div className={styles.statCard}>
            <div className={styles.statLabel}>25th Percentile</div>
            <div className={styles.statValue}>
              {overall.p25_clv > 0 ? '+' : ''}{overall.p25_clv}%
            </div>
          </div>
          <div className={styles.statCard}>
            <div className={styles.statLabel}>75th Percentile</div>
            <div className={styles.statValue}>
              {overall.p75_clv > 0 ? '+' : ''}{overall.p75_clv}%
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
