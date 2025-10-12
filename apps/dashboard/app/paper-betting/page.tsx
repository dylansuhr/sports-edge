import {
  getPaperBankroll,
  getRecentPaperBets,
  getRecentDecisions,
  getDailyPerformance,
  getMarketPerformance,
  getPaperBettingStats
} from '@/actions/paper-betting';
import PaperBettingClient from './PaperBettingClient';

export const dynamic = 'force-dynamic';

export default async function PaperBettingPage() {
  const [
    bankroll,
    recentBets,
    recentDecisions,
    dailyPerformance,
    marketPerformance,
    stats
  ] = await Promise.all([
    getPaperBankroll(),
    getRecentPaperBets(50),
    getRecentDecisions(20),
    getDailyPerformance(30),
    getMarketPerformance(),
    getPaperBettingStats()
  ]);

  return (
    <PaperBettingClient
      bankroll={bankroll}
      recentBets={recentBets}
      recentDecisions={recentDecisions}
      dailyPerformance={dailyPerformance}
      marketPerformance={marketPerformance}
      stats={stats}
    />
  );
}
