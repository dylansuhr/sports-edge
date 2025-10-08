import { getRecentBets, getBetStats } from '@/actions/bets';

export default async function BetsPage() {
  const [bets, stats] = await Promise.all([
    getRecentBets(100),
    getBetStats()
  ]);

  return (
    <main style={{ padding: '2rem', fontFamily: 'system-ui, sans-serif' }}>
      <h1 style={{ marginBottom: '2rem' }}>Bet History & Performance</h1>

      {/* Stats Summary */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '1rem',
        marginBottom: '2rem'
      }}>
        <div style={{ padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '8px' }}>
          <div style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '0.5rem' }}>
            Total Bets
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
            {stats.total_bets}
          </div>
        </div>

        <div style={{ padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '8px' }}>
          <div style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '0.5rem' }}>
            Total Staked
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
            ${stats.total_staked.toFixed(2)}
          </div>
        </div>

        <div style={{ padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '8px' }}>
          <div style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '0.5rem' }}>
            Total P&L
          </div>
          <div style={{
            fontSize: '1.5rem',
            fontWeight: 'bold',
            color: stats.total_pnl >= 0 ? '#22c55e' : '#ef4444'
          }}>
            {stats.total_pnl >= 0 ? '+' : ''}${stats.total_pnl.toFixed(2)}
          </div>
        </div>

        <div style={{ padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '8px' }}>
          <div style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '0.5rem' }}>
            ROI
          </div>
          <div style={{
            fontSize: '1.5rem',
            fontWeight: 'bold',
            color: stats.roi >= 0 ? '#22c55e' : '#ef4444'
          }}>
            {stats.roi >= 0 ? '+' : ''}{stats.roi.toFixed(2)}%
          </div>
        </div>

        <div style={{ padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '8px' }}>
          <div style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '0.5rem' }}>
            Avg CLV
          </div>
          <div style={{
            fontSize: '1.5rem',
            fontWeight: 'bold',
            color: stats.avg_clv >= 0 ? '#22c55e' : '#ef4444'
          }}>
            {stats.avg_clv >= 0 ? '+' : ''}{stats.avg_clv.toFixed(2)}%
          </div>
        </div>

        <div style={{ padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '8px' }}>
          <div style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '0.5rem' }}>
            Win Rate
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
            {stats.win_rate.toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Bet History Table */}
      <h2 style={{ marginBottom: '1rem', fontSize: '1.25rem' }}>Recent Bets</h2>

      {bets.length === 0 ? (
        <p>No bets recorded yet.</p>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #ddd', textAlign: 'left' }}>
                <th style={{ padding: '0.75rem' }}>Date</th>
                <th style={{ padding: '0.75rem' }}>Game/Player</th>
                <th style={{ padding: '0.75rem' }}>Market</th>
                <th style={{ padding: '0.75rem' }}>Book</th>
                <th style={{ padding: '0.75rem' }}>Line</th>
                <th style={{ padding: '0.75rem' }}>Odds</th>
                <th style={{ padding: '0.75rem' }}>Stake</th>
                <th style={{ padding: '0.75rem' }}>CLV</th>
                <th style={{ padding: '0.75rem' }}>Result</th>
                <th style={{ padding: '0.75rem' }}>P&L</th>
              </tr>
            </thead>
            <tbody>
              {bets.map((bet) => {
                const matchup = bet.player_name
                  ? `${bet.player_name} (${bet.home_team} vs ${bet.away_team})`
                  : `${bet.home_team} vs ${bet.away_team}`;

                return (
                  <tr key={bet.id} style={{ borderBottom: '1px solid #eee' }}>
                    <td style={{ padding: '0.75rem', fontSize: '0.8rem' }}>
                      {new Date(bet.placed_at).toLocaleDateString()}
                    </td>
                    <td style={{ padding: '0.75rem' }}>{matchup}</td>
                    <td style={{ padding: '0.75rem' }}>{bet.market_name}</td>
                    <td style={{ padding: '0.75rem' }}>{bet.sportsbook}</td>
                    <td style={{ padding: '0.75rem' }}>
                      {bet.line_value ? bet.line_value.toFixed(1) : '-'}
                    </td>
                    <td style={{ padding: '0.75rem' }}>
                      {bet.odds_american > 0 ? '+' : ''}{bet.odds_american}
                    </td>
                    <td style={{ padding: '0.75rem' }}>
                      ${bet.stake_amount.toFixed(2)}
                    </td>
                    <td style={{
                      padding: '0.75rem',
                      color: bet.clv_percent && bet.clv_percent > 0 ? '#22c55e' : '#ef4444'
                    }}>
                      {bet.clv_percent
                        ? `${bet.clv_percent > 0 ? '+' : ''}${bet.clv_percent.toFixed(2)}%`
                        : '-'}
                    </td>
                    <td style={{ padding: '0.75rem' }}>
                      {bet.result ? (
                        <span style={{
                          padding: '0.25rem 0.5rem',
                          borderRadius: '4px',
                          fontSize: '0.8rem',
                          backgroundColor: bet.result === 'win' ? '#dcfce7' :
                                          bet.result === 'loss' ? '#fee2e2' : '#f1f5f9',
                          color: bet.result === 'win' ? '#166534' :
                                 bet.result === 'loss' ? '#991b1b' : '#475569'
                        }}>
                          {bet.result}
                        </span>
                      ) : (
                        <span style={{ color: '#94a3b8' }}>pending</span>
                      )}
                    </td>
                    <td style={{
                      padding: '0.75rem',
                      fontWeight: 'bold',
                      color: bet.profit_loss
                        ? (bet.profit_loss >= 0 ? '#22c55e' : '#ef4444')
                        : '#64748b'
                    }}>
                      {bet.profit_loss
                        ? `${bet.profit_loss >= 0 ? '+' : ''}$${bet.profit_loss.toFixed(2)}`
                        : '-'}
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
