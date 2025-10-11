'use client';

import { useState } from 'react';
import AutomationStatus from '@/components/AutomationStatus';

interface Signal {
  id: number;
  league?: string;
  home_team?: string;
  away_team?: string;
  player_name?: string;
  game_time?: string;
  market_name: string;
  selection?: string;
  line_value?: number;
  odds_american: number;
  fair_probability: number;
  edge_percent: number;
  recommended_stake_pct: number;
  confidence_level: string;
  sportsbook: string;
}

interface SignalsClientProps {
  signals: Signal[];
  filters: {
    league?: string;
    market?: string;
    minEdge?: number;
    page?: number;
  };
  total: number;
  pages: number;
}

type SortField = 'time' | 'matchup' | 'market' | 'selection' | 'line' | 'odds' | 'fair_probability' | 'edge' | 'stake' | 'sportsbook' | 'confidence';
type SortDirection = 'asc' | 'desc';

export default function SignalsClient({ signals, filters, total, pages }: SignalsClientProps) {
  const [activeTab, setActiveTab] = useState<'all' | 'nfl' | 'nba' | 'nhl'>('all');
  const [sortField, setSortField] = useState<SortField>('edge');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  const getEdgeClass = (edge: number) => {
    if (edge >= 5) return 'edge-excellent';
    if (edge >= 3) return 'edge-good';
    if (edge >= 2) return 'edge-fair';
    return 'edge-low';
  };

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = date.getTime() - now.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));

    if (diffHours < 24) {
      return `${diffHours}h`;
    }
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d`;
  };

  const nflCount = signals.filter(s => s.league === 'nfl').length;
  const nbaCount = signals.filter(s => s.league === 'nba').length;
  const nhlCount = signals.filter(s => s.league === 'nhl').length;

  // Filter by tab
  const filteredSignals = signals.filter(s => {
    if (activeTab === 'all') return true;
    if (activeTab === 'nfl') return s.league === 'nfl';
    if (activeTab === 'nba') return s.league === 'nba';
    if (activeTab === 'nhl') return s.league === 'nhl';
    return true;
  });

  // Sort signals
  const sortedSignals = [...filteredSignals].sort((a, b) => {
    let comparison = 0;

    switch (sortField) {
      case 'time':
        comparison = new Date(a.game_time || 0).getTime() - new Date(b.game_time || 0).getTime();
        break;
      case 'matchup':
        const aMatchup = a.player_name || `${a.home_team} vs ${a.away_team}`;
        const bMatchup = b.player_name || `${b.home_team} vs ${b.away_team}`;
        comparison = aMatchup.localeCompare(bMatchup);
        break;
      case 'market':
        comparison = a.market_name.localeCompare(b.market_name);
        break;
      case 'selection':
        comparison = (a.selection || '').localeCompare(b.selection || '');
        break;
      case 'line':
        comparison = (a.line_value || 0) - (b.line_value || 0);
        break;
      case 'odds':
        comparison = a.odds_american - b.odds_american;
        break;
      case 'fair_probability':
        comparison = a.fair_probability - b.fair_probability;
        break;
      case 'edge':
        comparison = a.edge_percent - b.edge_percent;
        break;
      case 'stake':
        comparison = a.recommended_stake_pct - b.recommended_stake_pct;
        break;
      case 'sportsbook':
        comparison = a.sportsbook.localeCompare(b.sportsbook);
        break;
      case 'confidence':
        comparison = a.confidence_level.localeCompare(b.confidence_level);
        break;
    }

    return sortDirection === 'asc' ? comparison : -comparison;
  });

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  return (
    <main className="container">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="terminal-dots">
            <span className="dot red"></span>
            <span className="dot yellow"></span>
            <span className="dot green"></span>
          </div>
          <div className="header-text">
            <h1>
              <span className="accent">&gt;</span> SportsEdge
              <span className="blink">_</span>
            </h1>
            <p className="subtitle mono">Active Betting Signals · {signals.length} opportunities detected</p>
          </div>
        </div>

        {/* Automation Status */}
        <AutomationStatus />

        {/* Sport Tabs */}
        <div className="tabs">
          <button
            className={`tab ${activeTab === 'all' ? 'active' : ''}`}
            onClick={() => setActiveTab('all')}
          >
            <span className="tab-label">ALL</span>
            <span className="tab-count">{signals.length}</span>
          </button>
          <button
            className={`tab ${activeTab === 'nfl' ? 'active' : ''}`}
            onClick={() => setActiveTab('nfl')}
          >
            <span className="tab-label">NFL</span>
            <span className="tab-count">{nflCount}</span>
          </button>
          <button
            className={`tab ${activeTab === 'nba' ? 'active' : ''}`}
            onClick={() => setActiveTab('nba')}
          >
            <span className="tab-label">NBA</span>
            <span className="tab-count">{nbaCount}</span>
          </button>
          <button
            className={`tab ${activeTab === 'nhl' ? 'active' : ''}`}
            onClick={() => setActiveTab('nhl')}
          >
            <span className="tab-label">NHL</span>
            <span className="tab-count">{nhlCount}</span>
          </button>
        </div>
      </header>

      {/* Signals Table */}
      {sortedSignals.length === 0 ? (
        <div className="empty-state">
          <div className="terminal-output mono">
            <p><span className="accent">&gt;</span> No signals detected</p>
            <p>  Waiting for opportunities with edge ≥{filters.minEdge || 2}%...</p>
            <p>  Run: <span style={{ color: 'var(--accent)' }}>make signals</span></p>
          </div>
        </div>
      ) : (
        <div className="table-container">
          <table className="signals-table">
            <thead>
              <tr>
                <th className="sortable" onClick={() => handleSort('time')}>
                  Time
                  {sortField === 'time' && (
                    <span className="sort-indicator">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                  )}
                </th>
                <th className="sortable" onClick={() => handleSort('matchup')}>
                  Matchup
                  {sortField === 'matchup' && (
                    <span className="sort-indicator">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                  )}
                </th>
                <th className="sortable" onClick={() => handleSort('market')}>
                  Market
                  {sortField === 'market' && (
                    <span className="sort-indicator">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                  )}
                </th>
                <th className="sortable" onClick={() => handleSort('selection')}>
                  Selection
                  {sortField === 'selection' && (
                    <span className="sort-indicator">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                  )}
                </th>
                <th className="sortable mono" onClick={() => handleSort('line')}>
                  Line
                  {sortField === 'line' && (
                    <span className="sort-indicator">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                  )}
                </th>
                <th className="sortable mono" onClick={() => handleSort('odds')}>
                  Odds
                  {sortField === 'odds' && (
                    <span className="sort-indicator">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                  )}
                </th>
                <th className="sortable mono" onClick={() => handleSort('fair_probability')}>
                  Fair Prob
                  {sortField === 'fair_probability' && (
                    <span className="sort-indicator">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                  )}
                </th>
                <th className="sortable mono" onClick={() => handleSort('edge')}>
                  Edge %
                  {sortField === 'edge' && (
                    <span className="sort-indicator">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                  )}
                </th>
                <th className="sortable mono" onClick={() => handleSort('stake')}>
                  Stake %
                  {sortField === 'stake' && (
                    <span className="sort-indicator">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                  )}
                </th>
                <th className="sortable" onClick={() => handleSort('sportsbook')}>
                  Book
                  {sortField === 'sportsbook' && (
                    <span className="sort-indicator">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                  )}
                </th>
                <th className="sortable" onClick={() => handleSort('confidence')}>
                  Confidence
                  {sortField === 'confidence' && (
                    <span className="sort-indicator">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                  )}
                </th>
              </tr>
            </thead>
            <tbody>
              {sortedSignals.map((signal) => {
                const matchup = signal.player_name
                  ? `${signal.player_name} (${signal.home_team} vs ${signal.away_team})`
                  : `${signal.home_team} vs ${signal.away_team}`;

                const gameTime = signal.game_time || new Date().toISOString();

                return (
                  <tr key={signal.id} className="signal-row">
                    <td className="mono time-cell">{formatTime(gameTime)}</td>
                    <td className="matchup-cell">{matchup}</td>
                    <td>{signal.market_name}</td>
                    <td className="accent">{signal.selection || '-'}</td>
                    <td className="mono">{signal.line_value ? signal.line_value.toFixed(1) : 'N/A'}</td>
                    <td className="mono odds-cell">
                      {signal.odds_american > 0 ? '+' : ''}{signal.odds_american}
                    </td>
                    <td className="mono">{(signal.fair_probability * 100).toFixed(1)}%</td>
                    <td className={`mono ${getEdgeClass(signal.edge_percent)}`}>
                      {signal.edge_percent.toFixed(1)}%
                    </td>
                    <td className="mono">{signal.recommended_stake_pct.toFixed(2)}%</td>
                    <td>{signal.sportsbook}</td>
                    <td>
                      <span className={`confidence-badge ${signal.confidence_level}`}>
                        {signal.confidence_level}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {pages > 1 && (
        <div className="pagination">
          <div className="pagination-info">
            Showing {((filters.page || 1) - 1) * 50 + 1}-{Math.min((filters.page || 1) * 50, total)} of {total} signals
          </div>
          <div className="pagination-buttons">
            {filters.page && filters.page > 1 && (
              <a href={`/signals?page=${filters.page - 1}${filters.league && filters.league !== 'all' ? `&league=${filters.league}` : ''}`} className="pagination-button">
                ← Previous
              </a>
            )}
            {Array.from({ length: Math.min(pages, 10) }, (_, i) => {
              const pageNum = i + 1;
              const isActive = (filters.page || 1) === pageNum;
              return (
                <a
                  key={pageNum}
                  href={`/signals?page=${pageNum}${filters.league && filters.league !== 'all' ? `&league=${filters.league}` : ''}`}
                  className={`pagination-button ${isActive ? 'active' : ''}`}
                >
                  {pageNum}
                </a>
              );
            })}
            {pages > 10 && <span className="pagination-ellipsis">...</span>}
            {(filters.page || 1) < pages && (
              <a href={`/signals?page=${(filters.page || 1) + 1}${filters.league && filters.league !== 'all' ? `&league=${filters.league}` : ''}`} className="pagination-button">
                Next →
              </a>
            )}
          </div>
        </div>
      )}

      <style jsx>{`
        .container {
          min-height: 100vh;
          background: var(--bg-primary);
          padding: 2rem;
        }

        .header {
          margin-bottom: 2rem;
          background: var(--bg-card);
          border: 1px solid var(--border);
          border-radius: 8px;
          padding: 2rem;
        }

        .header-content {
          display: flex;
          align-items: center;
          gap: 1.5rem;
          margin-bottom: 1.5rem;
        }

        .terminal-dots {
          display: flex;
          gap: 6px;
        }

        .dot {
          width: 12px;
          height: 12px;
          border-radius: 50%;
        }

        .dot.red { background: var(--red); }
        .dot.yellow { background: var(--yellow); }
        .dot.green { background: var(--green); }

        .header-text h1 {
          font-size: 2.5rem;
          font-weight: 600;
          margin: 0;
          color: var(--text-primary);
        }

        .accent { color: var(--accent); }

        .blink {
          animation: blink 1.5s infinite;
        }

        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0; }
        }

        .subtitle {
          margin: 0.5rem 0 0 0;
          color: var(--text-secondary);
          font-size: 0.95rem;
        }

        .mono {
          font-family: 'JetBrains Mono', 'Fira Code', 'Monaco', monospace;
        }

        /* Tabs */
        .tabs {
          display: flex;
          gap: 0.5rem;
          padding-top: 1.5rem;
          border-top: 1px solid var(--border);
        }

        .tab {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.75rem 1.25rem;
          background: var(--bg-secondary);
          border: 1px solid var(--border);
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.2s ease;
          color: var(--text-secondary);
        }

        .tab:hover {
          background: var(--bg-tertiary);
          border-color: var(--accent);
        }

        .tab.active {
          background: var(--accent-glow);
          border-color: var(--accent);
          color: var(--accent);
        }

        .tab-label {
          font-weight: 600;
          font-size: 0.85rem;
          letter-spacing: 0.05em;
        }

        .tab-count {
          font-family: 'JetBrains Mono', monospace;
          font-size: 0.85rem;
          padding: 0.15rem 0.5rem;
          background: var(--bg-card);
          border-radius: 4px;
          border: 1px solid var(--border);
        }

        .tab.active .tab-count {
          background: rgba(0, 255, 136, 0.15);
          border-color: var(--accent);
          color: var(--accent);
        }

        /* Table Container */
        .table-container {
          background: var(--bg-card);
          border: 1px solid var(--border);
          border-radius: 8px;
          overflow-x: auto;
        }

        .signals-table {
          width: 100%;
          border-collapse: collapse;
        }

        /* Table Header */
        .signals-table thead {
          background: var(--bg-tertiary);
          border-bottom: 2px solid var(--border);
        }

        .signals-table th {
          padding: 1rem;
          text-align: left;
          font-size: 0.75rem;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: var(--text-muted);
          white-space: nowrap;
        }

        .signals-table th.sortable {
          cursor: pointer;
          user-select: none;
          transition: color 0.2s ease;
        }

        .signals-table th.sortable:hover {
          color: var(--accent);
        }

        .sort-indicator {
          margin-left: 0.5rem;
          color: var(--accent);
        }

        /* Table Body */
        .signals-table tbody tr {
          border-bottom: 1px solid var(--border);
          transition: all 0.2s ease;
        }

        .signal-row {
          border-left: 2px solid transparent;
        }

        .signal-row:hover {
          background: var(--bg-tertiary);
          border-left-color: var(--accent);
        }

        .signals-table td {
          padding: 1rem;
          color: var(--text-primary);
          font-size: 0.9rem;
        }

        /* Cell Styles */
        .time-cell {
          color: var(--text-secondary);
          font-size: 0.85rem;
        }

        .matchup-cell {
          font-weight: 500;
          max-width: 250px;
        }

        .odds-cell {
          font-weight: 600;
        }

        /* Edge Color Classes */
        .edge-excellent {
          color: var(--green);
          font-weight: 700;
        }

        .edge-good {
          color: var(--accent);
          font-weight: 700;
        }

        .edge-fair {
          color: var(--yellow);
          font-weight: 600;
        }

        .edge-low {
          color: var(--text-muted);
        }

        /* Confidence Badge */
        .confidence-badge {
          display: inline-block;
          padding: 0.35rem 0.75rem;
          border-radius: 4px;
          font-size: 0.7rem;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .confidence-badge.high {
          background: rgba(0, 255, 136, 0.2);
          color: var(--green);
          border: 1px solid var(--green);
        }

        .confidence-badge.medium {
          background: rgba(251, 191, 36, 0.2);
          color: var(--yellow);
          border: 1px solid var(--yellow);
        }

        .confidence-badge.low {
          background: rgba(102, 102, 102, 0.2);
          color: var(--text-muted);
          border: 1px solid var(--text-muted);
        }

        /* Empty State */
        .empty-state {
          display: flex;
          justify-content: center;
          align-items: center;
          min-height: 400px;
        }

        .terminal-output {
          background: var(--code-bg);
          border: 1px solid var(--border);
          border-radius: 8px;
          padding: 2rem;
          color: var(--text-secondary);
          font-size: 0.95rem;
        }

        .terminal-output p {
          margin: 0.5rem 0;
        }

        /* Pagination */
        .pagination {
          margin-top: 2rem;
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 1.5rem;
          background: rgba(0, 0, 0, 0.3);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 8px;
        }

        .pagination-info {
          font-family: var(--font-mono);
          font-size: 14px;
          color: var(--foreground-muted);
        }

        .pagination-buttons {
          display: flex;
          gap: 0.5rem;
          align-items: center;
        }

        .pagination-button {
          padding: 0.5rem 1rem;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 4px;
          color: var(--foreground);
          text-decoration: none;
          font-family: var(--font-mono);
          font-size: 13px;
          transition: all 0.2s;
          cursor: pointer;
        }

        .pagination-button:hover {
          background: rgba(255, 255, 255, 0.1);
          border-color: var(--accent);
        }

        .pagination-button.active {
          background: var(--accent);
          color: var(--background);
          border-color: var(--accent);
        }

        .pagination-ellipsis {
          color: var(--foreground-muted);
          padding: 0 0.5rem;
        }

        /* Responsive */
        @media (max-width: 1200px) {
          .signals-table {
            font-size: 0.85rem;
          }

          .signals-table th,
          .signals-table td {
            padding: 0.75rem;
          }
        }

        @media (max-width: 768px) {
          .container {
            padding: 1rem;
          }

          .header {
            padding: 1.5rem;
          }

          .header-content {
            flex-direction: column;
            align-items: flex-start;
          }

          .tabs {
            overflow-x: auto;
            padding-bottom: 0.5rem;
          }

          .table-container {
            overflow-x: scroll;
          }

          .signals-table {
            min-width: 1200px;
          }
        }
      `}</style>
    </main>
  );
}
