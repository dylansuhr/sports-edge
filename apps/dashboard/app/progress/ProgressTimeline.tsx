'use client';

import { Milestone } from '@/actions/milestones';
import styles from './Progress.module.css';
import { useEffect, useState } from 'react';

interface Props {
  milestones: Milestone[];
  currentMilestone: Milestone | null;
  sportMilestones: Milestone[];
}

export default function ProgressTimeline({ milestones, currentMilestone, sportMilestones }: Props) {
  const [timeRemaining, setTimeRemaining] = useState('');

  useEffect(() => {
    if (!currentMilestone?.target_date) return;

    const updateTime = () => {
      const now = new Date();
      const target = new Date(currentMilestone.target_date!);
      const diff = target.getTime() - now.getTime();

      if (diff <= 0) {
        setTimeRemaining('Overdue');
        return;
      }

      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      setTimeRemaining(`${days} days remaining`);
    };

    updateTime();
    const interval = setInterval(updateTime, 60000); // Update every minute

    return () => clearInterval(interval);
  }, [currentMilestone]);

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'No target date';
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getStatusIcon = (met: boolean) => met ? '✅' : '❌';
  const getStatusColor = (met: boolean) => met ? styles.met : styles.notMet;

  const calculateProgress = (milestone: Milestone) => {
    if (!milestone.criteria_met) return 0;
    const total = Object.keys(milestone.criteria).length;
    const met = Object.values(milestone.criteria_met).filter((c: any) => c.met).length;
    return Math.round((met / total) * 100);
  };

  const phaseMilestones = milestones.filter(m => m.phase !== 'Sport Expansion');
  const currentProgress = currentMilestone ? calculateProgress(currentMilestone) : 0;
  const criteriaMet = currentMilestone?.criteria_met ?
    Object.values(currentMilestone.criteria_met).filter((c: any) => c.met).length : 0;
  const criteriaTotal = currentMilestone?.criteria ? Object.keys(currentMilestone.criteria).length : 0;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1 className={styles.title}>🎯 PROGRESS TRACKER</h1>
        <p className={styles.subtitle}>Research-Aligned Roadmap · Milestone-Based Sport Addition</p>
      </div>

      {/* Current Milestone Card */}
      {currentMilestone && (
        <div className={styles.currentMilestone}>
          <div className={styles.milestoneHeader}>
            <div>
              <h2 className={styles.milestoneName}>{currentMilestone.name}</h2>
              <p className={styles.milestonePhase}>{currentMilestone.phase}</p>
            </div>
            <div className={styles.progressBadge}>
              <span className={styles.progressPercent}>{currentProgress}%</span>
            </div>
          </div>

          <div className={styles.progressBarContainer}>
            <div className={styles.progressBar}>
              <div
                className={styles.progressFill}
                style={{ width: `${currentProgress}%` }}
              />
            </div>
            <span className={styles.progressLabel}>
              {criteriaMet} of {criteriaTotal} criteria met
            </span>
          </div>

          {currentMilestone.target_date && (
            <div className={styles.timeInfo}>
              <span>Target: {formatDate(currentMilestone.target_date)}</span>
              <span className={styles.timeRemaining}>{timeRemaining}</span>
            </div>
          )}

          <div className={styles.criteriaList}>
            <h3 className={styles.criteriaTitle}>Milestone Criteria:</h3>
            {Object.entries(currentMilestone.criteria).map(([key, config]: [string, any]) => {
              const criterionMet = currentMilestone.criteria_met?.[key];
              const isMet = criterionMet?.met || false;

              return (
                <div key={key} className={`${styles.criterion} ${getStatusColor(isMet)}`}>
                  <span className={styles.criterionIcon}>{getStatusIcon(isMet)}</span>
                  <div className={styles.criterionContent}>
                    <span className={styles.criterionLabel}>{config.description}</span>
                    {criterionMet && criterionMet.current !== undefined && (
                      <span className={styles.criterionValue}>
                        {typeof criterionMet.current === 'boolean'
                          ? (criterionMet.current ? 'Implemented' : 'Not implemented')
                          : `${criterionMet.current} / ${criterionMet.target}`
                        }
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {currentMilestone.all_criteria_met ? (
            <div className={styles.readyBanner}>
              🎉 All criteria met! Ready to advance to next phase.
            </div>
          ) : (
            <div className={styles.blockerBanner}>
              ⚠️ {criteriaTotal - criteriaMet} blocker{criteriaTotal - criteriaMet !== 1 ? 's' : ''} preventing advancement
            </div>
          )}
        </div>
      )}

      {/* Timeline */}
      <div className={styles.timeline}>
        <h2 className={styles.sectionTitle}>Phase Timeline</h2>
        {phaseMilestones.map((milestone, index) => {
          const progress = calculateProgress(milestone);
          const isActive = milestone.status === 'in_progress';
          const isCompleted = milestone.status === 'completed';

          return (
            <div key={milestone.id} className={`${styles.timelineItem} ${isActive ? styles.active : ''} ${isCompleted ? styles.completed : ''}`}>
              <div className={styles.timelineMarker}>
                {isCompleted ? '✓' : isActive ? '●' : index + 1}
              </div>
              <div className={styles.timelineContent}>
                <div className={styles.timelineHeader}>
                  <h3 className={styles.timelineName}>{milestone.name}</h3>
                  <span className={styles.timelineStatus}>{milestone.status}</span>
                </div>
                <p className={styles.timelineDescription}>{milestone.description}</p>
                {milestone.target_date && (
                  <p className={styles.timelineDate}>Target: {formatDate(milestone.target_date)}</p>
                )}
                {milestone.criteria_met && (
                  <div className={styles.timelineProgress}>
                    <div className={styles.progressBar}>
                      <div
                        className={styles.progressFill}
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                    <span className={styles.progressLabel}>{progress}%</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Sport Expansion Milestones */}
      {sportMilestones.length > 0 && (
        <div className={styles.sportExpansion}>
          <h2 className={styles.sectionTitle}>Sport Expansion Readiness</h2>
          <p className={styles.sportSubtitle}>
            Automated detection: System will alert when ready to add NBA/NHL
          </p>
          <div className={styles.sportGrid}>
            {sportMilestones.map(milestone => {
              const isReady = milestone.all_criteria_met;

              return (
                <div key={milestone.id} className={`${styles.sportCard} ${isReady ? styles.sportReady : ''}`}>
                  <div className={styles.sportHeader}>
                    <h3 className={styles.sportName}>
                      {milestone.name.includes('NBA') && '🏀 '}
                      {milestone.name.includes('NHL') && '🏒 '}
                      {milestone.name.replace('Add ', '').replace(' League', '')}
                    </h3>
                    {isReady && <span className={styles.readyBadge}>READY</span>}
                  </div>
                  <p className={styles.sportDescription}>{milestone.description}</p>
                  {milestone.criteria_met && (
                    <div className={styles.sportCriteria}>
                      {Object.entries(milestone.criteria).map(([key, config]: [string, any]) => {
                        const met = milestone.criteria_met?.[key]?.met || false;
                        return (
                          <div key={key} className={styles.sportCriterion}>
                            <span className={styles.criterionIcon}>{getStatusIcon(met)}</span>
                            <span>{config.description}</span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Last Updated */}
      {currentMilestone?.last_checked && (
        <div className={styles.footer}>
          Last checked: {new Date(currentMilestone.last_checked).toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
          })}
        </div>
      )}
    </div>
  );
}
