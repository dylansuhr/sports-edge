'use client';

import { useState } from 'react';
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
import type {
  PaperBankroll,
  PaperBet,
  PaperBetDecision,
  DailyPerformance,
  MarketPerformance
} from '@/actions/paper-betting';
import styles from './PaperBetting.module.css';

// Format date to Eastern Time with day of week
function formatGameTime(dateString: string | undefined): string {
  if (!dateString) return 'TBD';
  const date = new Date(dateString);
  return date.toLocaleString('en-US', {
    timeZone: 'America/New_York',
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  }) + ' ET';
}

interface Props {
  bankroll: PaperBankroll | null;
  recentBets: PaperBet[];
  recentDecisions: PaperBetDecision[];
  dailyPerformance: DailyPerformance[];
  marketPerformance: MarketPerformance[];
  stats: {
    total_value: number;
    avg_confidence: number;
    top_market: string;
    recent_streak: string;
  };
}

export default function PaperBettingClient({
  bankroll,
  recentBets,
  recentDecisions,
  dailyPerformance,
  marketPerformance,
  stats
}: Props) {
  const [activeTab, setActiveTab] = useState<'overview' | 'bets' | 'decisions' | 'performance'>('overview');

  if (!bankroll) {
    return (
      <div className={styles.container}>
        <div className={styles.header}>
          <h1>PAPER BETTING</h1>
          <p className={styles.subtitle}>AI-Powered Mock Betting System</p>
        </div>
        <div className={styles.emptyState}>
          <p>No paper betting data available yet.</p>
          <p>The AI agent will start placing paper bets automatically.</p>
        </div>
      </div>
    );
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(value);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    });
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'won':
        return styles.statusWon;
      case 'lost':
        return styles.statusLost;
      case 'push':
        return styles.statusPush;
      case 'pending':
        return styles.statusPending;
      case 'void':
        return styles.statusVoid;
      default:
        return '';
    }
  };

  const getROIColor = (roi: number) => {
    if (roi > 5) return styles.roiHigh;
    if (roi > 0) return styles.roiPositive;
    if (roi < -5) return styles.roiLow;
    return styles.roiNegative;
  };

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <h1>PAPER BETTING</h1>
        <p className={styles.subtitle}>AI-Powered Mock Betting · Zero Risk Validation</p>
      </div>

      {/* Key Metrics Cards */}
      <div className={styles.metricsGrid}>
        <div className={styles.metricCard}>
          <div className={styles.metricLabel}>Paper Bankroll</div>
          <div className={`${styles.metricValue} ${bankroll.total_profit_loss >= 0 ? styles.positive : styles.negative}`}>
            {formatCurrency(bankroll.balance)}
          </div>
          <div className={styles.metricSubtext}>
            Started: {formatCurrency(bankroll.starting_balance)} ·
            P&L: {formatCurrency(bankroll.total_profit_loss)} ({bankroll.total_profit_loss >= 0 ? '+' : ''}{bankroll.roi_percent.toFixed(2)}%)
          </div>
        </div>

        <div className={styles.metricCard}>
          <div className={styles.metricLabel}>Win Rate</div>
          <div className={styles.metricValue}>
            {bankroll.win_rate.toFixed(1)}%
          </div>
          <div className={styles.metricSubtext}>
            {bankroll.win_count}W · {bankroll.loss_count}L · {bankroll.push_count}P
            · {bankroll.total_bets} total bets
          </div>
        </div>

        <div className={styles.metricCard}>
          <div className={styles.metricLabel}>ROI</div>
          <div className={`${styles.metricValue} ${getROIColor(Number(bankroll.roi_percent))}`}>
            {bankroll.roi_percent >= 0 ? '+' : ''}{bankroll.roi_percent.toFixed(2)}%
          </div>
          <div className={styles.metricSubtext}>
            ${bankroll.total_staked.toFixed(2)} staked ·
            Avg Edge: {bankroll.avg_edge !== null && bankroll.avg_edge !== undefined ? bankroll.avg_edge.toFixed(1) : 'N/A'}%
          </div>
        </div>

        <div className={styles.metricCard}>
          <div className={styles.metricLabel}>CLV Performance</div>
          <div className={`${styles.metricValue} ${
            bankroll.avg_clv !== null && bankroll.avg_clv !== undefined && bankroll.avg_clv > 0
              ? styles.positive
              : bankroll.avg_clv !== null && bankroll.avg_clv !== undefined && bankroll.avg_clv < 0
                ? styles.negative
                : ''
          }`}>
            {bankroll.avg_clv !== null && bankroll.avg_clv !== undefined
              ? `${bankroll.avg_clv >= 0 ? '+' : ''}${bankroll.avg_clv.toFixed(2)}%`
              : 'N/A'}
          </div>
          <div className={styles.metricSubtext}>
            Closing Line Value · {stats.recent_streak ? `Streak: ${stats.recent_streak}` : 'Building history...'}
          </div>
        </div>
      </div>

      {/* Info Banner */}
      <div className={styles.infoBanner}>
        <div className={styles.infoBannerIcon}>ℹ️</div>
        <div className={styles.infoBannerContent}>
          <strong>How Paper Betting Works:</strong> The AI agent automatically evaluates signals, places mock bets using sophisticated risk management,
          and tracks performance. This validates the system with zero financial risk before you place real bets. Positive ROI + positive CLV = system is beating the market.
        </div>
      </div>

      {/* Tabs */}
      <div className={styles.tabs}>
        <button
          className={`${styles.tab} ${activeTab === 'overview' ? styles.tabActive : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'bets' ? styles.tabActive : ''}`}
          onClick={() => setActiveTab('bets')}
        >
          Bets ({recentBets.length})
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'decisions' ? styles.tabActive : ''}`}
          onClick={() => setActiveTab('decisions')}
        >
          AI Decisions ({recentDecisions.length})
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'performance' ? styles.tabActive : ''}`}
          onClick={() => setActiveTab('performance')}
        >
          Performance
        </button>
      </div>

      {/* Tab Content */}
      <div className={styles.tabContent}>
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className={styles.overviewGrid}>
            {/* Cumulative P&L Chart */}
            <div className={styles.chartCard}>
              <h3>Cumulative Profit/Loss (30 Days)</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={dailyPerformance.map(d => ({ ...d, date: formatDate(d.date) }))}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis dataKey="date" stroke="#888" />
                  <YAxis stroke="#888" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                    labelStyle={{ color: '#fff' }}
                  />
                  <Legend />
                  <ReferenceLine y={0} stroke="#666" strokeDasharray="3 3" />
                  <Line
                    type="monotone"
                    dataKey="cumulative_pl"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={{ fill: '#3b82f6', r: 3 }}
                    name="Cumulative P&L ($)"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Market Performance */}
            <div className={styles.chartCard}>
              <h3>Performance by Market</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={marketPerformance}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis dataKey="market_name" stroke="#888" />
                  <YAxis stroke="#888" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                    labelStyle={{ color: '#fff' }}
                  />
                  <Legend />
                  <Bar dataKey="total_pl" fill="#3b82f6" name="Total P&L ($)" />
                  <Bar dataKey="win_rate" fill="#22c55e" name="Win Rate (%)" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Market Stats Table */}
            <div className={styles.tableCard}>
              <h3>Market Performance Summary</h3>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Market</th>
                    <th>Bets</th>
                    <th>Win Rate</th>
                    <th>Avg Edge</th>
                    <th>Total P&L</th>
                    <th>ROI</th>
                  </tr>
                </thead>
                <tbody>
                  {marketPerformance.map((market) => (
                    <tr key={market.market_name}>
                      <td>{market.market_name}</td>
                      <td>{market.bets}</td>
                      <td>{market.win_rate.toFixed(1)}%</td>
                      <td>{market.avg_edge.toFixed(1)}%</td>
                      <td className={Number(market.total_pl) >= 0 ? styles.positive : styles.negative}>
                        {formatCurrency(Number(market.total_pl))}
                      </td>
                      <td className={Number(market.roi) >= 0 ? styles.positive : styles.negative}>
                        {Number(market.roi) >= 0 ? '+' : ''}{Number(market.roi).toFixed(1)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Bets Tab */}
        {activeTab === 'bets' && (
          <div className={styles.tableCard}>
            <h3>Recent Paper Bets</h3>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Placed</th>
                  <th>Game</th>
                  <th>Game Time</th>
                  <th>Market</th>
                  <th>Selection</th>
                  <th>Odds</th>
                  <th>Edge</th>
                  <th>Stake</th>
                  <th>Status</th>
                  <th>P&L</th>
                </tr>
              </thead>
              <tbody>
                {recentBets.map((bet) => (
                  <tr key={bet.id}>
                    <td className={styles.dateCell}>{formatDateTime(bet.placed_at)}</td>
                    <td>
                      {bet.home_team && bet.away_team ? (
                        <>
                          <div>{bet.home_team} vs</div>
                          <div className={styles.awayTeam}>{bet.away_team}</div>
                        </>
                      ) : (
                        'N/A'
                      )}
                    </td>
                    <td className={styles.gameTimeCell}>{formatGameTime(bet.scheduled_at)}</td>
                    <td>{bet.market_name}</td>
                    <td className={styles.selectionCell}>{bet.selection}</td>
                    <td>{bet.odds_american > 0 ? '+' : ''}{bet.odds_american}</td>
                    <td className={styles.edgeCell}>{bet.edge_percent.toFixed(1)}%</td>
                    <td>{formatCurrency(Number(bet.stake))}</td>
                    <td>
                      <span className={`${styles.statusBadge} ${getStatusColor(bet.status)}`}>
                        {bet.status.toUpperCase()}
                      </span>
                    </td>
                    <td className={bet.profit_loss && bet.profit_loss >= 0 ? styles.positive : styles.negative}>
                      {bet.profit_loss != null ? formatCurrency(Number(bet.profit_loss)) : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* AI Decisions Tab */}
        {activeTab === 'decisions' && (
          <div className={styles.tableCard}>
            <h3>AI Decision Log</h3>
            <p className={styles.tableSubtitle}>
              Transparent view of every decision the AI makes, including bets placed and skipped
            </p>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Game</th>
                  <th>Game Time</th>
                  <th>Market</th>
                  <th>Decision</th>
                  <th>Confidence</th>
                  <th>Edge</th>
                  <th>Stake</th>
                  <th>Reasoning</th>
                </tr>
              </thead>
              <tbody>
                {recentDecisions.map((decision) => (
                  <tr key={decision.id}>
                    <td className={styles.dateCell}>{formatDateTime(decision.timestamp)}</td>
                    <td>
                      {decision.home_team && decision.away_team ? (
                        <>
                          <div>{decision.home_team} vs</div>
                          <div className={styles.awayTeam}>{decision.away_team}</div>
                        </>
                      ) : (
                        'N/A'
                      )}
                    </td>
                    <td className={styles.gameTimeCell}>{formatGameTime(decision.scheduled_at)}</td>
                    <td>{decision.market_name || 'N/A'}</td>
                    <td>
                      <span className={`${styles.decisionBadge} ${decision.decision === 'place' ? styles.decisionPlace : styles.decisionSkip}`}>
                        {decision.decision.toUpperCase()}
                      </span>
                    </td>
                    <td className={styles.confidenceCell}>
                      {(decision.confidence_score * 100).toFixed(0)}%
                    </td>
                    <td className={styles.edgeCell}>{decision.edge_percent.toFixed(1)}%</td>
                    <td>
                      {decision.actual_stake != null
                        ? formatCurrency(Number(decision.actual_stake))
                        : '-'}
                    </td>
                    <td className={styles.reasoningCell}>{decision.reasoning}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Performance Tab */}
        {activeTab === 'performance' && (
          <div className={styles.overviewGrid}>
            {/* Daily P&L Chart */}
            <div className={styles.chartCard}>
              <h3>Daily Profit/Loss</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={dailyPerformance.map(d => ({ ...d, date: formatDate(d.date) }))}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis dataKey="date" stroke="#888" />
                  <YAxis stroke="#888" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                    labelStyle={{ color: '#fff' }}
                  />
                  <Legend />
                  <ReferenceLine y={0} stroke="#666" />
                  <Bar
                    dataKey="profit_loss"
                    fill="#3b82f6"
                    name="Daily P&L ($)"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Win Rate Over Time */}
            <div className={styles.chartCard}>
              <h3>Win Rate Over Time</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={dailyPerformance.map(d => ({ ...d, date: formatDate(d.date) }))}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis dataKey="date" stroke="#888" />
                  <YAxis stroke="#888" domain={[0, 100]} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                    labelStyle={{ color: '#fff' }}
                  />
                  <Legend />
                  <ReferenceLine y={52.4} stroke="#22c55e" strokeDasharray="3 3" label="Break-even (~52%)" />
                  <Line
                    type="monotone"
                    dataKey="win_rate"
                    stroke="#22c55e"
                    strokeWidth={2}
                    dot={{ fill: '#22c55e', r: 3 }}
                    name="Win Rate (%)"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
