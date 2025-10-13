import { getMilestones, getCurrentMilestone, getSportExpansionMilestones, getTimelineData } from '@/actions/milestones';
import ProgressTimeline from './ProgressTimeline';
import WaitingPeriodCard from '@/components/WaitingPeriodCard';
import ActionTimelineCalendar from '@/components/ActionTimelineCalendar';
import NextActionAlert from '@/components/NextActionAlert';

export const dynamic = 'force-dynamic';

export default async function ProgressPage() {
  const [allMilestones, currentMilestone, sportMilestones, timelineData] = await Promise.all([
    getMilestones(),
    getCurrentMilestone(),
    getSportExpansionMilestones(),
    getTimelineData()
  ]);

  return (
    <div>
      {/* Next Action Alert - Most Important */}
      <NextActionAlert
        paperBetsSettled={timelineData.paperBetsSettled}
        roiPct={timelineData.roiPct}
        clvPct={timelineData.clvPct}
        targetBets={timelineData.targetBets}
        targetRoi={timelineData.targetRoi}
        targetClv={timelineData.targetClv}
        betsPerDay={timelineData.betsPerDay}
        lineShoppingImplemented={timelineData.lineShoppingImplemented}
        backtestingCompleted={timelineData.backtestingCompleted}
      />

      {/* Waiting Period Progress */}
      <WaitingPeriodCard
        paperBetsSettled={timelineData.paperBetsSettled}
        targetBets={timelineData.targetBets}
        roiPct={timelineData.roiPct}
        targetRoi={timelineData.targetRoi}
        clvPct={timelineData.clvPct}
        targetClv={timelineData.targetClv}
        daysElapsed={timelineData.daysElapsed}
        estimatedDaysRemaining={timelineData.estimatedDaysRemaining}
      />

      {/* Week-by-Week Timeline */}
      <ActionTimelineCalendar
        startDate={new Date(timelineData.startDate)}
        paperBetsSettled={timelineData.paperBetsSettled}
        betsPerDay={timelineData.betsPerDay}
      />

      {/* Original Milestone Timeline */}
      <ProgressTimeline
        milestones={allMilestones}
        currentMilestone={currentMilestone}
        sportMilestones={sportMilestones}
      />
    </div>
  );
}
