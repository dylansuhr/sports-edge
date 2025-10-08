import { getActiveSignals } from '@/actions/signals';
import SignalsClient from './SignalsClient';

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

  return <SignalsClient signals={signals} filters={filters} />;
}
