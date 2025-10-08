import Link from 'next/link';
import { getDashboardKPIs, getRecentStats } from '@/actions/kpis';

export default async function Home() {
  const kpis = await getDashboardKPIs();
  const stats = await getRecentStats();

  return (
    <main style={{ padding: '2rem', fontFamily: 'system-ui, sans-serif' }}>
      <h1 style={{ fontSize: 32, marginBottom: 8, fontWeight: 600 }}>sports-edge</h1>
      <p style={{ color: '#666', marginBottom: '2rem' }}>
        Read-only dashboard for signals, bets, CLV/ROI, and promos.
      </p>

      {/* KPI Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: '1.5rem',
        marginBottom: '3rem'
      }}>
        {/* Open Signals */}
        <div style={{
          padding: '1.5rem',
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
          backgroundColor: '#fff'
        }}>
          <div style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.5rem' }}>
            Open Signals
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 600, color: '#111827' }}>
            {kpis.openSignalsCount}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.5rem' }}>
            Active betting opportunities
          </div>
        </div>

        {/* Average Edge */}
        <div style={{
          padding: '1.5rem',
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
          backgroundColor: '#fff'
        }}>
          <div style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.5rem' }}>
            Avg Edge
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 600, color: '#22c55e' }}>
            {kpis.avgEdgePercent.toFixed(2)}%
          </div>
          <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.5rem' }}>
            Current active signals
          </div>
        </div>

        {/* 7-Day CLV */}
        <div style={{
          padding: '1.5rem',
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
          backgroundColor: '#fff'
        }}>
          <div style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.5rem' }}>
            7-Day CLV
          </div>
          <div style={{
            fontSize: '2rem',
            fontWeight: 600,
            color: kpis.clvLast7Days >= 0 ? '#22c55e' : '#ef4444'
          }}>
            {kpis.clvLast7Days >= 0 ? '+' : ''}{kpis.clvLast7Days.toFixed(2)}%
          </div>
          <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.5rem' }}>
            Closing line value
          </div>
        </div>

        {/* Lifetime ROI */}
        <div style={{
          padding: '1.5rem',
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
          backgroundColor: '#fff'
        }}>
          <div style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.5rem' }}>
            Lifetime ROI
          </div>
          <div style={{
            fontSize: '2rem',
            fontWeight: 600,
            color: kpis.lifetimeROI >= 0 ? '#22c55e' : '#ef4444'
          }}>
            {kpis.lifetimeROI >= 0 ? '+' : ''}{kpis.lifetimeROI.toFixed(2)}%
          </div>
          <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.5rem' }}>
            All-time return on investment
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div style={{
        padding: '1.5rem',
        border: '1px solid #e5e7eb',
        borderRadius: '8px',
        backgroundColor: '#fff',
        marginBottom: '2rem'
      }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '1rem' }}>
          Last 7 Days
        </h2>
        <div style={{ display: 'flex', gap: '3rem' }}>
          <div>
            <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>Bets Placed</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 600, marginTop: '0.25rem' }}>
              {stats.betsPlaced}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>Bets Settled</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 600, marginTop: '0.25rem' }}>
              {stats.betsSettled}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>Win Rate</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 600, marginTop: '0.25rem' }}>
              {stats.winRate}%
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Links */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '1rem'
      }}>
        <Link href="/signals" style={{
          padding: '1.5rem',
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
          backgroundColor: '#fff',
          textDecoration: 'none',
          color: '#111827',
          fontWeight: 500,
          transition: 'border-color 0.2s',
        }}>
          📊 Signals
        </Link>
        <Link href="/bets" style={{
          padding: '1.5rem',
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
          backgroundColor: '#fff',
          textDecoration: 'none',
          color: '#111827',
          fontWeight: 500,
          transition: 'border-color 0.2s',
        }}>
          💰 Bets
        </Link>
        <Link href="/promos" style={{
          padding: '1.5rem',
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
          backgroundColor: '#fff',
          textDecoration: 'none',
          color: '#111827',
          fontWeight: 500,
          transition: 'border-color 0.2s',
        }}>
          🎁 Promos
        </Link>
        <Link href="/reports" style={{
          padding: '1.5rem',
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
          backgroundColor: '#fff',
          textDecoration: 'none',
          color: '#111827',
          fontWeight: 500,
          transition: 'border-color 0.2s',
        }}>
          📈 Reports
        </Link>
      </div>
    </main>
  );
}
