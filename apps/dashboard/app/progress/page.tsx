import { getMilestones, getCurrentMilestone, getSportExpansionMilestones } from '@/actions/milestones';
import ProgressTimeline from './ProgressTimeline';

export const dynamic = 'force-dynamic';

export default async function ProgressPage() {
  const [allMilestones, currentMilestone, sportMilestones] = await Promise.all([
    getMilestones(),
    getCurrentMilestone(),
    getSportExpansionMilestones()
  ]);

  return (
    <ProgressTimeline
      milestones={allMilestones}
      currentMilestone={currentMilestone}
      sportMilestones={sportMilestones}
    />
  );
}
