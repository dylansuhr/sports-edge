import {
  getAdvancedPerformanceMetrics,
  getParameterTuningHistory,
  getCorrelationAnalysis,
  getBettingPatterns
} from '@/actions/analytics';
import AnalyticsDashboard from './AnalyticsDashboard';

export const dynamic = 'force-dynamic';

export default async function AnalyticsPage() {
  const [performanceMetrics, parameterHistory, correlationData, bettingPatterns] = await Promise.all([
    getAdvancedPerformanceMetrics(),
    getParameterTuningHistory(30),
    getCorrelationAnalysis(),
    getBettingPatterns()
  ]);

  return (
    <AnalyticsDashboard
      performanceMetrics={performanceMetrics}
      parameterHistory={parameterHistory}
      correlationData={correlationData}
      bettingPatterns={bettingPatterns}
    />
  );
}
