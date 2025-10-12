export default function Loading() {
  return (
    <div className="container" style={{ padding: '2rem', maxWidth: '1600px', margin: '0 auto' }}>
      <header style={{ marginBottom: '2rem' }}>
        <div style={{ height: '40px', background: '#1a1a1a', borderRadius: '4px', marginBottom: '1rem', width: '300px' }}></div>
        <div style={{ height: '20px', background: '#1a1a1a', borderRadius: '4px', width: '200px' }}></div>
      </header>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '2rem', borderBottom: '2px solid #333', paddingBottom: '0.5rem' }}>
        {[1, 2, 3, 4].map((i) => (
          <div key={i} style={{ height: '36px', background: '#1a1a1a', borderRadius: '4px', width: '100px' }}></div>
        ))}
      </div>

      <div style={{ background: '#0f0f0f', border: '1px solid #333', borderRadius: '8px', padding: '1.5rem' }}>
        <div style={{ marginBottom: '1rem' }}>
          <div style={{ height: '24px', background: '#1a1a1a', borderRadius: '4px', marginBottom: '0.5rem' }}></div>
        </div>

        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} style={{ height: '60px', background: '#1a1a1a', borderRadius: '4px', marginBottom: '0.75rem' }}></div>
        ))}
      </div>

      <div style={{ textAlign: 'center', marginTop: '2rem', color: '#888', fontSize: '0.9rem' }}>
        Loading signals...
      </div>
    </div>
  );
}
