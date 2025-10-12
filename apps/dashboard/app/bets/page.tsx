import { getRecentBets, getBetStats } from '@/actions/bets';

export const dynamic = 'force-dynamic';

export default async function BetsPage() {
  const [bets, stats] = await Promise.all([
    getRecentBets(100),
    getBetStats()
  ]);

  return (
    <main style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      <h1 style={{
        fontFamily: 'var(--font-mono)',
        fontSize: '32px',
        marginBottom: '24px',
        letterSpacing: '0.05em'
      }}>
        BET HISTORY & PERFORMANCE
      </h1>

      {/* Stats Summary */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '16px',
        marginBottom: '32px'
      }}>
        <div style={{
          padding: '20px',
          background: 'rgba(0, 0, 0, 0.3)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '8px',
          backdropFilter: 'blur(10px)'
        }}>
          <div style={{
            fontSize: '12px',
            color: 'var(--foreground-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            marginBottom: '8px'
          }}>
            Total Bets
          </div>
          <div style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '24px',
            fontWeight: 700,
            color: 'var(--accent)'
          }}>
            {stats.total_bets}
          </div>
        </div>

        <div style={{
          padding: '20px',
          background: 'rgba(0, 0, 0, 0.3)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '8px',
          backdropFilter: 'blur(10px)'
        }}>
          <div style={{
            fontSize: '12px',
            color: 'var(--foreground-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            marginBottom: '8px'
          }}>
            Total Staked
          </div>
          <div style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '24px',
            fontWeight: 700,
            color: 'var(--accent)'
          }}>
            ${stats.total_staked.toFixed(2)}
          </div>
        </div>

        <div style={{
          padding: '20px',
          background: 'rgba(0, 0, 0, 0.3)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '8px',
          backdropFilter: 'blur(10px)'
        }}>
          <div style={{
            fontSize: '12px',
            color: 'var(--foreground-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            marginBottom: '8px'
          }}>
            Total P&L
          </div>
          <div style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '24px',
            fontWeight: 700,
            color: stats.total_pnl >= 0 ? '#22c55e' : '#ef4444'
          }}>
            {stats.total_pnl >= 0 ? '+' : ''}${stats.total_pnl.toFixed(2)}
          </div>
        </div>

        <div style={{
          padding: '20px',
          background: 'rgba(0, 0, 0, 0.3)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '8px',
          backdropFilter: 'blur(10px)'
        }}>
          <div style={{
            fontSize: '12px',
            color: 'var(--foreground-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            marginBottom: '8px'
          }}>
            ROI
          </div>
          <div style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '24px',
            fontWeight: 700,
            color: stats.roi >= 0 ? '#22c55e' : '#ef4444'
          }}>
            {stats.roi >= 0 ? '+' : ''}{stats.roi.toFixed(2)}%
          </div>
        </div>

        <div style={{
          padding: '20px',
          background: 'rgba(0, 0, 0, 0.3)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '8px',
          backdropFilter: 'blur(10px)'
        }}>
          <div style={{
            fontSize: '12px',
            color: 'var(--foreground-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            marginBottom: '8px'
          }}>
            Avg CLV
          </div>
          <div style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '24px',
            fontWeight: 700,
            color: stats.avg_clv >= 0 ? '#22c55e' : '#ef4444'
          }}>
            {stats.avg_clv >= 0 ? '+' : ''}{stats.avg_clv.toFixed(2)}%
          </div>
        </div>

        <div style={{
          padding: '20px',
          background: 'rgba(0, 0, 0, 0.3)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '8px',
          backdropFilter: 'blur(10px)'
        }}>
          <div style={{
            fontSize: '12px',
            color: 'var(--foreground-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            marginBottom: '8px'
          }}>
            Win Rate
          </div>
          <div style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '24px',
            fontWeight: 700,
            color: 'var(--accent)'
          }}>
            {stats.win_rate.toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Bet History Table */}
      <div style={{
        background: 'rgba(0, 0, 0, 0.3)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '8px',
        padding: '24px',
        backdropFilter: 'blur(10px)'
      }}>
        <h2 style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '18px',
          fontWeight: 700,
          marginBottom: '16px',
          letterSpacing: '0.05em',
          textTransform: 'uppercase'
        }}>
          Recent Bets
        </h2>

        {bets.length === 0 ? (
          <p style={{ color: 'var(--foreground-muted)' }}>
            No bets recorded yet. Place your first bet after the model shows &quot;Ready&quot; status.
          </p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{
              width: '100%',
              borderCollapse: 'collapse',
              fontFamily: 'var(--font-mono)',
              fontSize: '13px'
            }}>
              <thead>
                <tr style={{
                  borderBottom: '2px solid rgba(255, 255, 255, 0.2)',
                  textAlign: 'left'
                }}>
                  <th style={{ padding: '12px 8px', color: 'var(--foreground-muted)', textTransform: 'uppercase', fontSize: '11px' }}>Date</th>
                  <th style={{ padding: '12px 8px', color: 'var(--foreground-muted)', textTransform: 'uppercase', fontSize: '11px' }}>Game/Player</th>
                  <th style={{ padding: '12px 8px', color: 'var(--foreground-muted)', textTransform: 'uppercase', fontSize: '11px' }}>Market</th>
                  <th style={{ padding: '12px 8px', color: 'var(--foreground-muted)', textTransform: 'uppercase', fontSize: '11px' }}>Book</th>
                  <th style={{ padding: '12px 8px', color: 'var(--foreground-muted)', textTransform: 'uppercase', fontSize: '11px' }}>Line</th>
                  <th style={{ padding: '12px 8px', color: 'var(--foreground-muted)', textTransform: 'uppercase', fontSize: '11px' }}>Odds</th>
                  <th style={{ padding: '12px 8px', color: 'var(--foreground-muted)', textTransform: 'uppercase', fontSize: '11px' }}>Stake</th>
                  <th style={{ padding: '12px 8px', color: 'var(--foreground-muted)', textTransform: 'uppercase', fontSize: '11px' }}>CLV</th>
                  <th style={{ padding: '12px 8px', color: 'var(--foreground-muted)', textTransform: 'uppercase', fontSize: '11px' }}>Result</th>
                  <th style={{ padding: '12px 8px', color: 'var(--foreground-muted)', textTransform: 'uppercase', fontSize: '11px' }}>P&L</th>
                </tr>
              </thead>
              <tbody>
                {bets.map((bet) => {
                  const matchup = bet.player_name
                    ? `${bet.player_name} (${bet.home_team} vs ${bet.away_team})`
                    : `${bet.home_team} vs ${bet.away_team}`;

                  return (
                    <tr key={bet.id} style={{
                      borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                      transition: 'background 0.2s'
                    }}>
                      <td style={{ padding: '12px 8px', fontSize: '12px', color: 'var(--foreground-muted)' }}>
                        {new Date(bet.placed_at).toLocaleDateString()}
                      </td>
                      <td style={{ padding: '12px 8px' }}>{matchup}</td>
                      <td style={{ padding: '12px 8px' }}>{bet.market_name}</td>
                      <td style={{ padding: '12px 8px' }}>{bet.sportsbook}</td>
                      <td style={{ padding: '12px 8px' }}>
                        {bet.line_value ? bet.line_value.toFixed(1) : '-'}
                      </td>
                      <td style={{ padding: '12px 8px' }}>
                        {bet.odds_american > 0 ? '+' : ''}{bet.odds_american}
                      </td>
                      <td style={{ padding: '12px 8px' }}>
                        ${bet.stake_amount.toFixed(2)}
                      </td>
                      <td
                        style={{
                          padding: '12px 8px',
                          color:
                            bet.clv_percent !== null && bet.clv_percent !== undefined && bet.clv_percent > 0
                              ? '#22c55e'
                              : bet.clv_percent !== null && bet.clv_percent !== undefined && bet.clv_percent < 0
                                ? '#ef4444'
                                : 'var(--foreground-muted)',
                          fontWeight: 600
                        }}
                      >
                        {bet.clv_percent !== null && bet.clv_percent !== undefined
                          ? `${bet.clv_percent > 0 ? '+' : ''}${bet.clv_percent.toFixed(2)}%`
                          : '-'}
                      </td>
                      <td style={{ padding: '12px 8px' }}>
                        {bet.result ? (
                          <span style={{
                            padding: '4px 8px',
                            borderRadius: '4px',
                            fontSize: '11px',
                            textTransform: 'uppercase',
                            backgroundColor: bet.result === 'win' ? 'rgba(34, 197, 94, 0.2)' :
                                            bet.result === 'loss' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(255, 255, 255, 0.1)',
                            color: bet.result === 'win' ? '#22c55e' :
                                   bet.result === 'loss' ? '#ef4444' : 'var(--foreground-muted)'
                          }}>
                            {bet.result}
                          </span>
                        ) : (
                          <span style={{ color: 'var(--foreground-muted)' }}>pending</span>
                        )}
                      </td>
                      <td
                        style={{
                          padding: '12px 8px',
                          fontWeight: 700,
                          color:
                            bet.profit_loss !== null && bet.profit_loss !== undefined
                              ? (bet.profit_loss >= 0 ? '#22c55e' : '#ef4444')
                              : 'var(--foreground-muted)'
                        }}
                      >
                        {bet.profit_loss !== null && bet.profit_loss !== undefined
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
      </div>
    </main>
  );
}
