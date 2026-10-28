"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { BattleScreen } from "./BattleScreen";
import { ArenaRunExperience } from "./ArenaRunExperience";
import {
  createBattleAttemptId,
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
  StructuredBattleMode,
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
  attemptId?: string | null;
};

export function BattleExperience(props: BattleExperienceProps) {
  const structuredStage = resolveStructuredStage(props.selectedStageId);
  if (props.selectedStageId === "arena") {
    return <ArenaRunExperience countdownStepMs={props.countdownStepMs} />;
  }
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
  const [structuredBattleMode, setStructuredBattleMode] = useState<StructuredBattleMode>("learner");
  const [activeLaunch, setActiveLaunch] = useState<ActiveLaunch | null>(null);
  const [sessionKey, setSessionKey] = useState(0);
  const [resources, setResources] = useState<ResourceState | null>(null);
  const [resourceError, setResourceError] = useState<string | null>(null);
  const [resourceAttempt, setResourceAttempt] = useState(0);
  const [battleBackground, setBattleBackground] = useState<string | null>(null);
  const [rewardNotification, setRewardNotification] = useState<StageReward[] | null>(null);
  const pendingContinueRef = useRef<(() => void) | null>(null);
  const pendingCommitRef = useRef<VictoryCommitResponse | null>(null);
  const modeContextRef = useRef<string | null>(null);

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
            const modeContext = `${progression.profileId}.${structuredStage.stageId}`;
            if (modeContextRef.current !== modeContext) {
              modeContextRef.current = modeContext;
              setStructuredBattleMode("learner");
              setCurrentBattleIndex(serverStage.progress.unlockedBattle - 1);
            } else {
              setCurrentBattleIndex((index) => index ?? serverStage.progress.unlockedBattle - 1);
            }
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
    ? new LiveBattleProvider(
        undefined,
        activeLaunch.configuration,
        activeLaunch.createPath,
        activeLaunch.attemptId,
      )
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
    completedMode: StructuredBattleMode,
  ) => {
    if (completedMode === "tactics") {
      setCurrentBattleIndex(completedBattleIndex);
      return;
    }
    if (completedBattleIndex === refreshedStage.battles.length - 1
      && refreshedStage.modes.learner.completed) {
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
    if (!structuredStage || !currentStructuredBattle || !provider || !activeLaunch
      || currentBattleIndex === null) {
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
    const completedMode = "mode" in activeLaunch.configuration
      ? activeLaunch.configuration.mode ?? "learner"
      : "learner";
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

    const continueTraining = () => continueAfterCommit(
      refreshedStage,
      completedBattleIndex,
      completedMode,
    );
    if (completedMode === "learner" && commit.newlyGrantedRewards.length > 0) {
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
    return activeLaunch && "mode" in activeLaunch.configuration
      && activeLaunch.configuration.mode === "tactics"
      ? "RETURN TO TEAM BUILDER"
      : "CONTINUE TRAINING";
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
    const requestedMode = configuration.mode ?? "learner";
    const canLaunch = requestedMode === "tactics"
      ? authoritativeStage.modes.tactics.available
      : serverBattle?.unlocked;
    if (!serverBattle || !canLaunch) return;
    setSessionKey((key) => key + 1);
    setBattleBackground(BATTLE_BACKGROUND);
    setActiveLaunch({
      configuration,
      createPath: `/api/v1/stages/${encodeURIComponent(structuredStage.stageId)}/battles/${serverBattle.displayOrder}`,
      attemptId: createBattleAttemptId(),
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
            battleMode={structuredBattleMode}
            modeProgress={authoritativeStage.modes}
            onBattleModeChange={(mode) => {
              if (mode === "tactics" && !authoritativeStage.modes.tactics.available) return;
              setStructuredBattleMode(mode);
              if (mode === "learner") {
                setCurrentBattleIndex((index) => index !== null
                  && authoritativeStage.battles[index]?.unlocked
                    ? index
                    : authoritativeStage.progress.unlockedBattle - 1);
              }
            }}
            onSelectBattle={(index) => {
              const selectable = structuredBattleMode === "tactics"
                ? authoritativeStage.modes.tactics.available
                : authoritativeStage.battles[index]?.unlocked;
              if (selectable) setCurrentBattleIndex(index);
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
      onResign={closeLiveBattle}
    />
  );
}
