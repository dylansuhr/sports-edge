import { getActiveSignals } from '@/actions/signals';
import SignalsFilter from './SignalsFilter';
import { Suspense } from 'react';

export default async function SignalsPage({
  searchParams,
}: {
  searchParams: { league?: string; market?: string; minEdge?: string };
}) {
  const filters = {
    league: searchParams.league,
    market: searchParams.market,
    minEdge: searchParams.minEdge ? parseFloat(searchParams.minEdge) : undefined,
  };

  const signals = await getActiveSignals(filters);

  return (
    <main style={{ padding: '2rem', fontFamily: 'system-ui, sans-serif' }}>
      <h1 style={{ marginBottom: '1rem' }}>Active Signals</h1>
      <p style={{ color: '#666', marginBottom: '1rem' }}>
        {signals.length} active betting opportunities
      </p>

      <Suspense fallback={<div>Loading filters...</div>}>
        <SignalsFilter />
      </Suspense>

      {signals.length === 0 ? (
        <p>No active signals. Run generate_signals.py to create signals.</p>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #ddd', textAlign: 'left' }}>
                <th style={{ padding: '0.75rem' }}>Game/Player</th>
                <th style={{ padding: '0.75rem' }}>Market</th>
                <th style={{ padding: '0.75rem' }}>Side</th>
                <th style={{ padding: '0.75rem' }}>Book</th>
                <th style={{ padding: '0.75rem' }}>Line</th>
                <th style={{ padding: '0.75rem' }}>Odds</th>
                <th style={{ padding: '0.75rem' }}>Fair Prob</th>
                <th style={{ padding: '0.75rem' }}>Edge %</th>
                <th style={{ padding: '0.75rem' }}>Stake %</th>
                <th style={{ padding: '0.75rem' }}>Confidence</th>
                <th style={{ padding: '0.75rem' }}>Generated</th>
              </tr>
            </thead>
            <tbody>
              {signals.map((signal) => {
                const matchup = signal.player_name
                  ? `${signal.player_name} (${signal.home_team} vs ${signal.away_team})`
                  : `${signal.home_team} vs ${signal.away_team}`;

                const edgeColor = signal.edge_percent >= 5 ? '#22c55e' :
                                 signal.edge_percent >= 3 ? '#f59e0b' : '#64748b';

                // Determine side display
                const sideDisplay = signal.selection || '-';

                return (
                  <tr key={signal.id} style={{ borderBottom: '1px solid #eee' }}>
                    <td style={{ padding: '0.75rem' }}>{matchup}</td>
                    <td style={{ padding: '0.75rem' }}>{signal.market_name}</td>
                    <td style={{ padding: '0.75rem', fontSize: '0.85rem' }}>{sideDisplay}</td>
                    <td style={{ padding: '0.75rem' }}>{signal.sportsbook}</td>
                    <td style={{ padding: '0.75rem' }}>
                      {signal.line_value ? signal.line_value.toFixed(1) : '-'}
                    </td>
                    <td style={{ padding: '0.75rem' }}>
                      {signal.odds_american > 0 ? '+' : ''}{signal.odds_american}
                    </td>
                    <td style={{ padding: '0.75rem' }}>
                      {(signal.fair_probability * 100).toFixed(1)}%
                    </td>
                    <td style={{ padding: '0.75rem', fontWeight: 'bold', color: edgeColor }}>
                      {signal.edge_percent.toFixed(2)}%
                    </td>
                    <td style={{ padding: '0.75rem' }}>
                      {signal.recommended_stake_pct.toFixed(2)}%
                    </td>
                    <td style={{ padding: '0.75rem' }}>
                      <span style={{
                        padding: '0.25rem 0.5rem',
                        borderRadius: '4px',
                        fontSize: '0.8rem',
                        backgroundColor: signal.confidence_level === 'high' ? '#dcfce7' :
                                        signal.confidence_level === 'medium' ? '#fef3c7' : '#f1f5f9',
                        color: signal.confidence_level === 'high' ? '#166534' :
                               signal.confidence_level === 'medium' ? '#854d0e' : '#475569'
                      }}>
                        {signal.confidence_level}
                      </span>
                    </td>
                    <td style={{ padding: '0.75rem', fontSize: '0.8rem', color: '#666' }}>
                      {new Date(signal.generated_at).toLocaleString()}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
