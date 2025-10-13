import { getActiveSignals } from '@/actions/signals';
import SignalsClient from './SignalsClient';

export const dynamic = 'force-dynamic';

export default async function SignalsPage({
  searchParams,
}: {
  searchParams: { league?: string; market?: string; minEdge?: string; page?: string };
}) {
  const filters = {
    league: 'nfl', // NFL-only focus per research recommendations
    market: searchParams.market,
    minEdge: searchParams.minEdge ? parseFloat(searchParams.minEdge) : undefined,
    page: searchParams.page ? parseInt(searchParams.page) : 1,
    limit: 25, // Reduced from 50 for faster initial load
  };

  const { signals, total, pages, sportCounts } = await getActiveSignals(filters);

  return <SignalsClient signals={signals} filters={filters} total={total} pages={pages} sportCounts={sportCounts} />;
}
