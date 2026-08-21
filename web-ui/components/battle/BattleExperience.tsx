"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { BattleScreen } from "./BattleScreen";
import {
  fetchHeroRoster,
  fetchPlayerProgression,
  fetchStructuredStages,
  LiveBattleProvider,
} from "@/lib/battle/liveProvider";
import type {
  AuthoritativeStructuredStageDefinition,
  BattleCreateConfiguration,
  BattleOutcome,
  HeroDefinitionSummary,
  PlayerProgressionResponse,
  StageReward,
  StructuredBattleCreateConfiguration,
  VictoryCommitResponse,
} from "@/lib/battle/types";
import { BATTLE_BACKGROUND } from "@/lib/battle/battleBackgrounds";
import { TeamBuilder } from "./TeamBuilder";
import {
  missingStructuredStageRosterIds,
  resolveStructuredStage,
  structuredStageMatchesAuthority,
  type StructuredStageDefinition,
} from "@/components/stages/structured-stage-config";

type BattleExperienceProps = {
  countdownStepMs?: number;
  selectedStageId?: string;
};

type ResourceState = {
  roster: HeroDefinitionSummary[];
  progression: PlayerProgressionResponse;
  stages: AuthoritativeStructuredStageDefinition[];
};

type ActiveLaunch = {
  configuration: BattleCreateConfiguration | StructuredBattleCreateConfiguration;
  createPath: string;
};

export function BattleExperience(props: BattleExperienceProps) {
  const structuredStage = resolveStructuredStage(props.selectedStageId);
  return structuredStage
    ? <StructuredBattleExperience {...props} structuredStage={structuredStage} />
    : <BattleSession {...props} structuredStage={null} />;
}

function StructuredBattleExperience({
  structuredStage,
  ...props
}: BattleExperienceProps & { structuredStage: StructuredStageDefinition }) {
  const router = useRouter();
  return (
    <BattleSession
      {...props}
      structuredStage={structuredStage}
      onStructuredStageComplete={() => router.replace("/stages")}
    />
  );
}

function RewardNotification({
  rewards,
  onContinue,
}: {
  rewards: readonly StageReward[];
  onContinue: () => void;
}) {
  const continueRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    continueRef.current?.focus();
  }, []);
  return (
    <div className="completion-backdrop reward-notification-backdrop">
      <section
        className="completion-dialog reward-notification"
        role="dialog"
        aria-modal="true"
        aria-labelledby="reward-notification-title"
        aria-describedby="reward-notification-message"
        onKeyDown={(event) => {
          if (event.key === "Tab") {
            event.preventDefault();
            continueRef.current?.focus();
          }
        }}
      >
        <span className="completion-crest" aria-hidden="true">✦</span>
        <small>TRAINING REWARD</small>
        <h2 id="reward-notification-title">Reward granted</h2>
        <div id="reward-notification-message" aria-live="assertive">
          {rewards.map((reward) => <p key={reward.rewardId}>{reward.notification}</p>)}
        </div>
        <button ref={continueRef} type="button" onClick={onContinue}>CONTINUE</button>
      </section>
    </div>
  );
}

function BattleSession({
  countdownStepMs = 1000,
  selectedStageId,
  structuredStage,
  onStructuredStageComplete,
}: BattleExperienceProps & {
  structuredStage: StructuredStageDefinition | null;
  onStructuredStageComplete?: () => void;
}) {
  const [currentBattleIndex, setCurrentBattleIndex] = useState<number | null>(null);
  const [activeLaunch, setActiveLaunch] = useState<ActiveLaunch | null>(null);
  const [sessionKey, setSessionKey] = useState(0);
  const [resources, setResources] = useState<ResourceState | null>(null);
  const [resourceError, setResourceError] = useState<string | null>(null);
  const [resourceAttempt, setResourceAttempt] = useState(0);
  const [battleBackground, setBattleBackground] = useState<string | null>(null);
  const [rewardNotification, setRewardNotification] = useState<StageReward[] | null>(null);
  const pendingContinueRef = useRef<(() => void) | null>(null);
  const pendingCommitRef = useRef<VictoryCommitResponse | null>(null);

  useEffect(() => {
    let current = true;
    const load = async () => {
      try {
        const [roster, progression, stagesResponse] = await Promise.all([
          fetchHeroRoster(),
          fetchPlayerProgression(),
          structuredStage ? fetchStructuredStages() : Promise.resolve(null),
        ]);
        if (!current) return;
        setResources({ roster, progression, stages: stagesResponse?.stages ?? [] });
        if (structuredStage && stagesResponse) {
          const serverStage = stagesResponse.stages.find(
            (stage) => stage.stageId === structuredStage.stageId,
          );
          if (serverStage) {
            setCurrentBattleIndex((index) => index ?? serverStage.progress.unlockedBattle - 1);
          }
        }
        setResourceError(null);
      } catch (reason: unknown) {
        if (!current) return;
        setResourceError(
          reason instanceof Error ? reason.message : "Unable to load player progression.",
        );
      }
    };
    void load();
    return () => { current = false; };
  }, [resourceAttempt, structuredStage]);

  const authoritativeStage = structuredStage && resources
    ? resources.stages.find((stage) => stage.stageId === structuredStage.stageId) ?? null
    : null;

  const currentStructuredBattle = structuredStage && currentBattleIndex !== null
    ? structuredStage.battles[currentBattleIndex] ?? null
    : null;

  const provider = useMemo(() => activeLaunch
    ? new LiveBattleProvider(undefined, activeLaunch.configuration, activeLaunch.createPath)
    : null, [activeLaunch]);

  const missingStructuredRosterIds = useMemo(
    () => structuredStage && resources
      ? missingStructuredStageRosterIds(structuredStage, resources.roster)
      : [],
    [resources, structuredStage],
  );

  const retryResources = () => {
    setResources(null);
    setResourceError(null);
    setCurrentBattleIndex(null);
    setResourceAttempt((attempt) => attempt + 1);
  };

  const closeLiveBattle = () => {
    setActiveLaunch(null);
    setBattleBackground(null);
  };

  const continueAfterCommit = (
    refreshedStage: AuthoritativeStructuredStageDefinition,
    completedBattleIndex: number,
  ) => {
    if (completedBattleIndex === 8 && refreshedStage.progress.completed) {
      setCurrentBattleIndex(null);
      onStructuredStageComplete?.();
      return;
    }
    const nextDisplayOrder = Math.min(
      completedBattleIndex + 2,
      refreshedStage.progress.unlockedBattle,
    );
    setCurrentBattleIndex(nextDisplayOrder - 1);
  };

  const completeBattle = async (outcome: BattleOutcome) => {
    if (!structuredStage || !currentStructuredBattle || !provider || currentBattleIndex === null) {
      closeLiveBattle();
      return;
    }
    const friendlyVictory = outcome.kind === "victory" && outcome.winningSideId === "friendly";
    if (!friendlyVictory) {
      pendingCommitRef.current = null;
      closeLiveBattle();
      return;
    }

    const completedBattleIndex = currentBattleIndex;
    const commit = pendingCommitRef.current ?? await provider.commitStageVictory();
    pendingCommitRef.current = commit;
    const [progression, stagesResponse] = await Promise.all([
      fetchPlayerProgression(),
      fetchStructuredStages(),
    ]);
    const refreshedStage = stagesResponse.stages.find(
      (stage) => stage.stageId === structuredStage.stageId,
    );
    if (!refreshedStage || !structuredStageMatchesAuthority(structuredStage, refreshedStage)) {
      throw new Error("The refreshed training stage does not match the approved curriculum.");
    }
    setResources((current) => current
      ? { ...current, progression, stages: stagesResponse.stages }
      : current);
    pendingCommitRef.current = null;
    closeLiveBattle();

    const continueTraining = () => continueAfterCommit(refreshedStage, completedBattleIndex);
    if (commit.newlyGrantedRewards.length > 0) {
      pendingContinueRef.current = continueTraining;
      setRewardNotification(commit.newlyGrantedRewards);
      return;
    }
    continueTraining();
  };

  const dismissReward = () => {
    const continueTraining = pendingContinueRef.current;
    pendingContinueRef.current = null;
    setRewardNotification(null);
    continueTraining?.();
  };

  const completionLabel = (outcome: BattleOutcome) => {
    if (!structuredStage || !currentStructuredBattle) return "RETURN TO TEAM BUILDER";
    if (outcome.kind !== "victory" || outcome.winningSideId !== "friendly") {
      return "RETRY BATTLE";
    }
    return "CONTINUE TRAINING";
  };

  if (!provider && resourceError) return (
    <main className="loading-screen">
      <section className="connection-state" role="alert">
        <strong>PLAYER PROGRESSION UNAVAILABLE</strong>
        <p>{resourceError}</p>
        <button onClick={retryResources}>Retry progression</button>
      </section>
    </main>
  );
  if (!provider && !resources) return (
    <main className="loading-screen" aria-live="polite">
      <span className="loading-rune">◇</span>Loading player progression…
    </main>
  );
  if (!provider && structuredStage && (
    !authoritativeStage || !structuredStageMatchesAuthority(structuredStage, authoritativeStage)
  )) return (
    <main className="loading-screen">
      <section className="connection-state" role="alert">
        <strong>STAGE CONFIGURATION UNAVAILABLE</strong>
        <p>{structuredStage.displayName} does not match the approved server curriculum.</p>
        <button onClick={retryResources}>Retry training data</button>
      </section>
    </main>
  );
  if (!provider && structuredStage && missingStructuredRosterIds.length > 0) return (
    <main className="loading-screen">
      <section className="connection-state" role="alert">
        <strong>STAGE CONFIGURATION UNAVAILABLE</strong>
        <p>{structuredStage.displayName} cannot start because the approved roster is missing: {missingStructuredRosterIds.join(", ")}.</p>
        <button onClick={retryResources}>Retry training data</button>
      </section>
    </main>
  );

  const startArenaBattle = (configuration: BattleCreateConfiguration) => {
    setSessionKey((key) => key + 1);
    setBattleBackground(BATTLE_BACKGROUND);
    setActiveLaunch({ configuration, createPath: "/api/v1/battles" });
  };
  const startStructuredBattle = (configuration: StructuredBattleCreateConfiguration) => {
    if (!structuredStage || !authoritativeStage || currentBattleIndex === null) return;
    const serverBattle = authoritativeStage.battles[currentBattleIndex];
    if (!serverBattle?.unlocked) return;
    setSessionKey((key) => key + 1);
    setBattleBackground(BATTLE_BACKGROUND);
    setActiveLaunch({
      configuration,
      createPath: `/api/v1/stages/${encodeURIComponent(structuredStage.stageId)}/battles/${serverBattle.displayOrder}`,
    });
  };

  if (!provider) {
    const builder = structuredStage && currentStructuredBattle && authoritativeStage
      ? (
          <TeamBuilder
            key={`${resources!.progression.profileId}.${currentStructuredBattle.id}`}
            mode="structured"
            roster={resources!.roster}
            availableDefinitionIds={resources!.progression.unlockedHeroDefinitionIds}
            stage={structuredStage}
            battle={currentStructuredBattle}
            highestCompletedBattle={authoritativeStage.progress.highestCompletedBattle}
            highestUnlockedBattle={authoritativeStage.progress.unlockedBattle}
            onSelectBattle={(index) => {
              if (authoritativeStage.battles[index]?.unlocked) setCurrentBattleIndex(index);
            }}
            onStart={startStructuredBattle}
          />
        )
      : (
          <TeamBuilder
            key={`arena.${resources!.progression.profileId}`}
            roster={resources!.roster}
            availableDefinitionIds={resources!.progression.unlockedHeroDefinitionIds}
            selectedStageId={selectedStageId}
            onStart={startArenaBattle}
          />
        );
    return (
      <>
        {builder}
        {rewardNotification
          ? <RewardNotification rewards={rewardNotification} onContinue={dismissReward} />
          : null}
      </>
    );
  }
  return (
    <BattleScreen
      key={sessionKey}
      provider={provider}
      mode="live"
      backgroundImage={battleBackground ?? undefined}
      entryCountdownStepMs={countdownStepMs}
      completionActionLabel={completionLabel}
      onBattleComplete={completeBattle}
    />
  );
}
