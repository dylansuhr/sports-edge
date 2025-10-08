import fs from 'fs';
import path from 'path';

type Promo = { book: string; name: string; terms: string; est_ev: number; status: string; };
export default function Promos() {
  const file = path.join(process.cwd(), 'public', 'mock_promos.json');
  const data = JSON.parse(fs.readFileSync(file, 'utf8')) as Promo[];
  return (
    <main>
      <h1>Promos (Mock)</h1>
      <ul>
        {data.map((p, i) => (
          <li key={i}>{p.book}: <b>{p.name}</b> — {p.terms} | EV: ${(p.est_ev).toFixed(2)} | {p.status}</li>
        ))}
      </ul>
    </main>
  );
}
