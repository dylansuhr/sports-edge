import fs from 'fs';
import path from 'path';

type Promo = { book: string; name: string; terms: string; est_ev: number; status: string; };
export default function Promos() {
  const file = path.join(process.cwd(), 'public', 'mock_promos.json');
  let data: Promo[] = [];

  try {
    if (fs.existsSync(file)) {
      data = JSON.parse(fs.readFileSync(file, 'utf8')) as Promo[];
    }
  } catch (_error) {
    data = [];
  }

  return (
    <main>
      <h1>Promos (Mock)</h1>
      {data.length === 0 ? (
        <p>No promo data available. Drop a <code>mock_promos.json</code> file into <code>/public</code> to populate this list.</p>
      ) : (
        <ul>
          {data.map((p, i) => (
            <li key={i}>{p.book}: <b>{p.name}</b> — {p.terms} | EV: ${(p.est_ev).toFixed(2)} | {p.status}</li>
          ))}
        </ul>
      )}
    </main>
  );
}
