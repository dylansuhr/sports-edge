import Link from 'next/link';
import { getDashboardKPIs, getRecentStats } from '@/actions/kpis';

export const dynamic = 'force-dynamic';

export default async function Home() {
  const kpis = await getDashboardKPIs();
  const stats = await getRecentStats();

  return (
    <main style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      <h1 style={{
        fontFamily: 'monospace',
        fontSize: '32px',
        marginBottom: '8px',
        letterSpacing: '0.05em'
      }}>
        SPORTSEDGE DASHBOARD
      </h1>
      <p style={{
        color: '#888',
        marginBottom: '32px',
        fontSize: '16px'
      }}>
        Autonomous sports betting research platform - signals only, human-in-the-loop decision making
      </p>

      {/* KPI Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: '16px',
        marginBottom: '32px'
      }}>
        {/* Open Signals */}
        <div style={{
          padding: '20px',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '8px',
          background: 'rgba(0, 0, 0, 0.3)',
          backdropFilter: 'blur(10px)'
        }}>
          <div style={{
            fontSize: '12px',
            color: '#888',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            marginBottom: '8px'
          }}>
            Open Signals
          </div>
          <div style={{
            fontFamily: 'monospace',
            fontSize: '32px',
            fontWeight: 700,
            color: '#00ff88'
          }}>
            {kpis.openSignalsCount}
          </div>
          <div style={{
            fontSize: '12px',
            color: '#888',
            marginTop: '8px'
          }}>
            Active betting opportunities
          </div>
        </div>

        {/* Average Edge */}
        <div style={{
          padding: '20px',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '8px',
          background: 'rgba(0, 0, 0, 0.3)',
          backdropFilter: 'blur(10px)'
        }}>
          <div style={{
            fontSize: '12px',
            color: '#888',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            marginBottom: '8px'
          }}>
            Avg Edge
          </div>
          <div style={{
            fontFamily: 'monospace',
            fontSize: '32px',
            fontWeight: 700,
            color: '#22c55e'
          }}>
            {kpis.avgEdgePercent.toFixed(2)}%
          </div>
          <div style={{
            fontSize: '12px',
            color: '#888',
            marginTop: '8px'
          }}>
            Current active signals
          </div>
        </div>

        {/* 7-Day CLV */}
        <div style={{
          padding: '20px',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '8px',
          background: 'rgba(0, 0, 0, 0.3)',
          backdropFilter: 'blur(10px)'
        }}>
          <div style={{
            fontSize: '12px',
            color: '#888',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            marginBottom: '8px'
          }}>
            7-Day CLV
          </div>
          <div style={{
            fontFamily: 'monospace',
            fontSize: '32px',
            fontWeight: 700,
            color: kpis.clvLast7Days >= 0 ? '#22c55e' : '#ef4444'
          }}>
            {kpis.clvLast7Days >= 0 ? '+' : ''}{kpis.clvLast7Days.toFixed(2)}%
          </div>
          <div style={{
            fontSize: '12px',
            color: '#888',
            marginTop: '8px'
          }}>
            Closing line value
          </div>
        </div>

        {/* Lifetime ROI */}
        <div style={{
          padding: '20px',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '8px',
          background: 'rgba(0, 0, 0, 0.3)',
          backdropFilter: 'blur(10px)'
        }}>
          <div style={{
            fontSize: '12px',
            color: '#888',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            marginBottom: '8px'
          }}>
            Lifetime ROI
          </div>
          <div style={{
            fontFamily: 'monospace',
            fontSize: '32px',
            fontWeight: 700,
            color: kpis.lifetimeROI >= 0 ? '#22c55e' : '#ef4444'
          }}>
            {kpis.lifetimeROI >= 0 ? '+' : ''}{kpis.lifetimeROI.toFixed(2)}%
          </div>
          <div style={{
            fontSize: '12px',
            color: '#888',
            marginTop: '8px'
          }}>
            All-time return on investment
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div style={{
        padding: '20px',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '8px',
        background: 'rgba(0, 0, 0, 0.3)',
        backdropFilter: 'blur(10px)',
        marginBottom: '32px'
      }}>
        <h2 style={{
          fontFamily: 'monospace',
          fontSize: '18px',
          fontWeight: 700,
          marginBottom: '16px',
          letterSpacing: '0.05em',
          textTransform: 'uppercase'
        }}>
          Last 7 Days
        </h2>
        <div style={{ display: 'flex', gap: '48px', flexWrap: 'wrap' }}>
          <div>
            <div style={{
              fontSize: '12px',
              color: '#888',
              textTransform: 'uppercase',
              letterSpacing: '0.05em'
            }}>
              Bets Placed
            </div>
            <div style={{
              fontFamily: 'monospace',
              fontSize: '24px',
              fontWeight: 600,
              marginTop: '4px',
              color: '#00ff88'
            }}>
              {stats.betsPlaced}
            </div>
          </div>
          <div>
            <div style={{
              fontSize: '12px',
              color: '#888',
              textTransform: 'uppercase',
              letterSpacing: '0.05em'
            }}>
              Bets Settled
            </div>
            <div style={{
              fontFamily: 'monospace',
              fontSize: '24px',
              fontWeight: 600,
              marginTop: '4px',
              color: '#00ff88'
            }}>
              {stats.betsSettled}
            </div>
          </div>
          <div>
            <div style={{
              fontSize: '12px',
              color: '#888',
              textTransform: 'uppercase',
              letterSpacing: '0.05em'
            }}>
              Win Rate
            </div>
            <div style={{
              fontFamily: 'monospace',
              fontSize: '24px',
              fontWeight: 600,
              marginTop: '4px',
              color: '#00ff88'
            }}>
              {stats.winRate}%
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Links */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '16px'
      }}>
        <Link href="/signals" style={{
          padding: '20px',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '8px',
          background: 'rgba(0, 0, 0, 0.3)',
          backdropFilter: 'blur(10px)',
          textDecoration: 'none',
          color: '#ffffff',
          fontFamily: 'monospace',
          fontWeight: 500,
          fontSize: '14px',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          transition: 'all 0.2s',
          cursor: 'pointer'
        }}>
          📊 Signals
        </Link>
        <Link href="/performance" style={{
          padding: '20px',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '8px',
          background: 'rgba(0, 0, 0, 0.3)',
          backdropFilter: 'blur(10px)',
          textDecoration: 'none',
          color: '#ffffff',
          fontFamily: 'monospace',
          fontWeight: 500,
          fontSize: '14px',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          transition: 'all 0.2s',
          cursor: 'pointer'
        }}>
          📈 Performance
        </Link>
        <Link href="/paper-betting" style={{
          padding: '20px',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '8px',
          background: 'rgba(0, 0, 0, 0.3)',
          backdropFilter: 'blur(10px)',
          textDecoration: 'none',
          color: '#ffffff',
          fontFamily: 'monospace',
          fontWeight: 500,
          fontSize: '14px',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          transition: 'all 0.2s',
          cursor: 'pointer'
        }}>
          🤖 Paper Betting
        </Link>
        <Link href="/bets" style={{
          padding: '20px',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '8px',
          background: 'rgba(0, 0, 0, 0.3)',
          backdropFilter: 'blur(10px)',
          textDecoration: 'none',
          color: '#ffffff',
          fontFamily: 'monospace',
          fontWeight: 500,
          fontSize: '14px',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          transition: 'all 0.2s',
          cursor: 'pointer'
        }}>
          💰 My Bets
        </Link>
      </div>
    </main>
  );
}
