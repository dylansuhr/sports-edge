'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { useState, useEffect } from 'react';

export default function SignalsFilter() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [league, setLeague] = useState(searchParams.get('league') || 'all');
  const [market, setMarket] = useState(searchParams.get('market') || 'all');
  const [minEdge, setMinEdge] = useState(searchParams.get('minEdge') || '0');

  const updateFilters = () => {
    const params = new URLSearchParams();

    if (league !== 'all') params.set('league', league);
    if (market !== 'all') params.set('market', market);
    if (minEdge !== '0') params.set('minEdge', minEdge);

    router.push(`/signals?${params.toString()}`);
  };

  return (
    <div style={{
      display: 'flex',
      gap: '1rem',
      padding: '1.5rem',
      backgroundColor: '#f9fafb',
      border: '1px solid #e5e7eb',
      borderRadius: '8px',
      marginBottom: '2rem',
      flexWrap: 'wrap',
      alignItems: 'flex-end'
    }}>
      {/* League Filter */}
      <div style={{ minWidth: '150px' }}>
        <label style={{
          display: 'block',
          fontSize: '0.875rem',
          fontWeight: 500,
          color: '#374151',
          marginBottom: '0.5rem'
        }}>
          League
        </label>
        <select
          value={league}
          onChange={(e) => setLeague(e.target.value)}
          style={{
            width: '100%',
            padding: '0.5rem',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            fontSize: '0.875rem',
            backgroundColor: '#fff'
          }}
        >
          <option value="all">All Leagues</option>
          <option value="nfl">NFL</option>
          <option value="nba">NBA</option>
          <option value="nhl">NHL</option>
          <option value="mlb">MLB</option>
        </select>
      </div>

      {/* Market Filter */}
      <div style={{ minWidth: '150px' }}>
        <label style={{
          display: 'block',
          fontSize: '0.875rem',
          fontWeight: 500,
          color: '#374151',
          marginBottom: '0.5rem'
        }}>
          Market Type
        </label>
        <select
          value={market}
          onChange={(e) => setMarket(e.target.value)}
          style={{
            width: '100%',
            padding: '0.5rem',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            fontSize: '0.875rem',
            backgroundColor: '#fff'
          }}
        >
          <option value="all">All Markets</option>
          <option value="moneyline">Moneyline</option>
          <option value="spread">Spread</option>
          <option value="total">Total</option>
          <option value="player_prop">Player Props</option>
        </select>
      </div>

      {/* Min Edge Filter */}
      <div style={{ minWidth: '150px' }}>
        <label style={{
          display: 'block',
          fontSize: '0.875rem',
          fontWeight: 500,
          color: '#374151',
          marginBottom: '0.5rem'
        }}>
          Min Edge %
        </label>
        <input
          type="number"
          min="0"
          max="20"
          step="0.5"
          value={minEdge}
          onChange={(e) => setMinEdge(e.target.value)}
          style={{
            width: '100%',
            padding: '0.5rem',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            fontSize: '0.875rem'
          }}
        />
      </div>

      {/* Apply Button */}
      <button
        onClick={updateFilters}
        style={{
          padding: '0.5rem 1.5rem',
          backgroundColor: '#3b82f6',
          color: '#fff',
          border: 'none',
          borderRadius: '6px',
          fontSize: '0.875rem',
          fontWeight: 500,
          cursor: 'pointer',
          height: '38px'
        }}
      >
        Apply Filters
      </button>

      {/* Reset Button */}
      {(league !== 'all' || market !== 'all' || minEdge !== '0') && (
        <button
          onClick={() => {
            setLeague('all');
            setMarket('all');
            setMinEdge('0');
            router.push('/signals');
          }}
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: '#fff',
            color: '#6b7280',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            fontSize: '0.875rem',
            fontWeight: 500,
            cursor: 'pointer',
            height: '38px'
          }}
        >
          Reset
        </button>
      )}
    </div>
  );
}
