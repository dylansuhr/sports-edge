'use client';

import {
  AdvancedPerformanceMetrics,
  ParameterHistory,
  CorrelationData,
  BettingPatterns
} from '@/actions/analytics';
import styles from './Analytics.module.css';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface Props {
  performanceMetrics: AdvancedPerformanceMetrics;
  parameterHistory: ParameterHistory[];
  correlationData: CorrelationData;
  bettingPatterns: BettingPatterns;
}

export default function AnalyticsDashboard({
  performanceMetrics,
  parameterHistory,
  correlationData,
  bettingPatterns
}: Props) {
  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>🔬 Advanced Analytics</h1>
        <p className={styles.subtitle}>Deep dive into system performance and optimization opportunities</p>
      </div>

      {/* Betting Patterns Insights */}
      <div className={styles.insightsSection}>
        <h2 className={styles.sectionTitle}>🎯 Key Insights</h2>
        <div className={styles.insightGrid}>
          {bettingPatterns.best_performing_combo && (
            <div className={`${styles.insightCard} ${styles.success}`}>
              <div className={styles.insightIcon}>🏆</div>
              <div className={styles.insightContent}>
                <h3 className={styles.insightTitle}>Best Performing Combo</h3>
                <p className={styles.insightValue}>
                  {bettingPatterns.best_performing_combo.sport} · {bettingPatterns.best_performing_combo.market} · {bettingPatterns.best_performing_combo.sportsbook}
                </p>
                <p className={styles.insightMetric}>
                  ROI: {bettingPatterns.best_performing_combo.roi.toFixed(2)}% ({bettingPatterns.best_performing_combo.count} bets)
                </p>
              </div>
            </div>
          )}

          {bettingPatterns.worst_performing_combo && (
            <div className={`${styles.insightCard} ${styles.warning}`}>
              <div className={styles.insightIcon}>⚠️</div>
              <div className={styles.insightContent}>
                <h3 className={styles.insightTitle}>Worst Performing Combo</h3>
                <p className={styles.insightValue}>
                  {bettingPatterns.worst_performing_combo.sport} · {bettingPatterns.worst_performing_combo.market} · {bettingPatterns.worst_performing_combo.sportsbook}
                </p>
                <p className={styles.insightMetric}>
                  ROI: {bettingPatterns.worst_performing_combo.roi.toFixed(2)}% ({bettingPatterns.worst_performing_combo.count} bets)
                </p>
              </div>
            </div>
          )}

          {bettingPatterns.optimal_bet_timing && (
            <div className={`${styles.insightCard} ${styles.info}`}>
              <div className={styles.insightIcon}>⏰</div>
              <div className={styles.insightContent}>
                <h3 className={styles.insightTitle}>Optimal Bet Timing</h3>
                <p className={styles.insightValue}>
                  {bettingPatterns.optimal_bet_timing.hours_before_game} hours before game
                </p>
                <p className={styles.insightMetric}>
                  Avg CLV: {bettingPatterns.optimal_bet_timing.avg_clv.toFixed(2)}% ({bettingPatterns.optimal_bet_timing.count} bets)
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Performance by Sportsbook */}
      <div className={styles.chartSection}>
        <h2 className={styles.sectionTitle}>Performance by Sportsbook</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={performanceMetrics.by_sportsbook}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey="sportsbook" stroke="#888" style={{ fontSize: '12px' }} />
            <YAxis stroke="#888" style={{ fontSize: '12px' }} />
            <Tooltip
              contentStyle={{ background: '#1a1a1a', border: '1px solid #333', borderRadius: '4px' }}
              labelStyle={{ color: '#fff' }}
            />
            <Legend />
            <Bar dataKey="roi" fill="#00d4ff" name="ROI %" />
            <Bar dataKey="avg_clv" fill="#00ff88" name="Avg CLV %" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Performance by Market */}
      <div className={styles.chartSection}>
        <h2 className={styles.sectionTitle}>Performance by Market Type</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={performanceMetrics.by_market}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey="market" stroke="#888" style={{ fontSize: '12px' }} />
            <YAxis stroke="#888" style={{ fontSize: '12px' }} />
            <Tooltip
              contentStyle={{ background: '#1a1a1a', border: '1px solid #333', borderRadius: '4px' }}
              labelStyle={{ color: '#fff' }}
            />
            <Legend />
            <Bar dataKey="roi" fill="#00d4ff" name="ROI %" />
            <Bar dataKey="win_rate" fill="#ff9500" name="Win Rate %" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Performance by Confidence */}
      <div className={styles.chartSection}>
        <h2 className={styles.sectionTitle}>Performance by Confidence Level</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={performanceMetrics.by_confidence}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey="confidence" stroke="#888" style={{ fontSize: '12px' }} />
            <YAxis stroke="#888" style={{ fontSize: '12px' }} />
            <Tooltip
              contentStyle={{ background: '#1a1a1a', border: '1px solid #333', borderRadius: '4px' }}
              labelStyle={{ color: '#fff' }}
            />
            <Legend />
            <Bar dataKey="roi" fill="#00d4ff" name="ROI %" />
            <Bar dataKey="avg_clv" fill="#00ff88" name="Avg CLV %" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Parameter Tuning History */}
      <div className={styles.chartSection}>
        <h2 className={styles.sectionTitle}>Signal Generation Trends (30 Days)</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={parameterHistory}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis
              dataKey="date"
              stroke="#888"
              style={{ fontSize: '12px' }}
              tickFormatter={(val) => new Date(val).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
            />
            <YAxis stroke="#888" style={{ fontSize: '12px' }} />
            <Tooltip
              contentStyle={{ background: '#1a1a1a', border: '1px solid #333', borderRadius: '4px' }}
              labelStyle={{ color: '#fff' }}
              labelFormatter={(val) => new Date(val).toLocaleDateString()}
            />
            <Legend />
            <Line type="monotone" dataKey="avg_edge" stroke="#00d4ff" name="Avg Edge %" strokeWidth={2} />
            <Line type="monotone" dataKey="clv" stroke="#00ff88" name="CLV %" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Correlation Analysis */}
      <div className={styles.correlationSection}>
        <h2 className={styles.sectionTitle}>Correlation Analysis</h2>
        <div className={styles.correlationGrid}>
          {correlationData.correlations.map((corr, idx) => (
            <div key={idx} className={styles.correlationCard}>
              <h3 className={styles.correlationTitle}>
                {corr.metric1} vs {corr.metric2}
              </h3>
              <div className={`${styles.correlationValue} ${getCorrelationClass(corr.correlation)}`}>
                {corr.correlation.toFixed(3)}
              </div>
              <p className={styles.correlationInterpretation}>
                {interpretCorrelation(corr.correlation)}
              </p>
              <p className={styles.correlationSample}>
                n = {corr.sample_size}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* CLV by Time of Day */}
      <div className={styles.chartSection}>
        <h2 className={styles.sectionTitle}>CLV by Hour of Day (Bet Placement)</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={performanceMetrics.by_time_of_day}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis
              dataKey="hour"
              stroke="#888"
              style={{ fontSize: '12px' }}
              label={{ value: 'Hour (24h format)', position: 'insideBottom', offset: -5, fill: '#888' }}
            />
            <YAxis stroke="#888" style={{ fontSize: '12px' }} label={{ value: 'Avg CLV %', angle: -90, position: 'insideLeft', fill: '#888' }} />
            <Tooltip
              contentStyle={{ background: '#1a1a1a', border: '1px solid #333', borderRadius: '4px' }}
              labelStyle={{ color: '#fff' }}
            />
            <Line type="monotone" dataKey="avg_clv" stroke="#00ff88" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function getCorrelationClass(correlation: number): string {
  const abs = Math.abs(correlation);
  if (abs > 0.7) return 'strong';
  if (abs > 0.4) return 'moderate';
  return 'weak';
}

function interpretCorrelation(correlation: number): string {
  const abs = Math.abs(correlation);
  const direction = correlation > 0 ? 'positive' : 'negative';

  if (abs > 0.7) return `Strong ${direction} correlation`;
  if (abs > 0.4) return `Moderate ${direction} correlation`;
  if (abs > 0.2) return `Weak ${direction} correlation`;
  return 'No significant correlation';
}
