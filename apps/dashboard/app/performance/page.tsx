import {
  getModelReadiness,
  getDailyPerformance,
  getPerformanceBySport,
  getPerformanceByMarket,
  getOverallPerformance
} from '@/actions/performance';
import ModelReadinessCard from '@/components/ModelReadinessCard';
import PerformanceCharts from './PerformanceCharts';

export const revalidate = 60; // Revalidate every 60 seconds

export default async function PerformancePage() {
  const [readiness, dailyPerformance, sportPerformance, marketPerformance, overall] = await Promise.all([
    getModelReadiness(),
    getDailyPerformance(30),
    getPerformanceBySport(14),
    getPerformanceByMarket(14),
    getOverallPerformance(14)
  ]);

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      <h1 style={{
        fontFamily: 'var(--font-mono)',
        fontSize: '32px',
        marginBottom: '24px',
        letterSpacing: '0.05em'
      }}>
        MODEL PERFORMANCE
      </h1>

      <ModelReadinessCard readiness={readiness} />

      <PerformanceCharts
        dailyData={dailyPerformance}
        sportData={sportPerformance}
        marketData={marketPerformance}
        overall={overall}
      />
    </div>
  );
}
