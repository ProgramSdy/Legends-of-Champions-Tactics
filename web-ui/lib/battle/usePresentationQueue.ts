"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { BattleProviderError, type BattleEvent, type BattleProvider, type BattleSnapshot, type PresentationScript, type ProviderErrorKind } from "./types";

const BASE_DELAY = 620;
const isVisibleLogEvent = (event: BattleEvent) => event.visibleInLog !== false;

export function usePresentationQueue(provider: BattleProvider) {
  const [visibleSnapshot, setVisibleSnapshot] = useState<BattleSnapshot | null>(null);
  const [revision, setRevision] = useState(0);
  const [activeEvent, setActiveEvent] = useState<BattleEvent | null>(null);
  const [log, setLog] = useState<BattleEvent[]>([]);
  const [speed, setSpeed] = useState(1);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isOpening, setIsOpening] = useState(false);
  const [hasPendingOpening, setHasPendingOpening] = useState(false);
  const [canSkip, setCanSkip] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errorKind, setErrorKind] = useState<ProviderErrorKind | null>(null);
  const generation = useRef(0);
  const busy = useRef(false);
  const pending = useRef<PresentationScript | null>(null);
  const pendingOpening = useRef<PresentationScript | null>(null);
  const pendingLogEvents = useRef<BattleEvent[]>([]);

  const [loadAttempt, setLoadAttempt] = useState(0);
  useEffect(() => {
    const token = ++generation.current;
    busy.current = false;
    pending.current = null;
    pendingOpening.current = null;
    pendingLogEvents.current = [];
    provider.getState().then((state) => {
      if (generation.current !== token) return;
      const shouldPlayOpening = state.playOpening === true && Boolean(state.openingSnapshot);
      setVisibleSnapshot(structuredClone(shouldPlayOpening ? state.openingSnapshot! : state.snapshot));
      setRevision(state.revision);
      if (shouldPlayOpening) {
        pendingOpening.current = {
          id: "session-opening",
          label: "Battle opening",
          eventType: state.events?.find((event) => event.effectHint)?.effectHint ?? "magic",
          events: [...(state.events ?? [])].sort((a, b) => a.sequence - b.sequence),
          snapshot: structuredClone(state.snapshot),
          revision: state.revision,
        };
        setIsOpening(true);
        setHasPendingOpening(true);
        setLog([]);
      } else {
        setIsOpening(false);
        setHasPendingOpening(false);
        setLog([...(state.events ?? [])].sort((a, b) => a.sequence - b.sequence).filter(isVisibleLogEvent));
      }
      setActiveEvent(null);
      setIsPlaying(false);
      setCanSkip(false);
      setError(null);
      setErrorKind(null);
    }).catch((reason: unknown) => {
      if (generation.current !== token) return;
      setError(reason instanceof Error ? reason.message : "Unable to load battle.");
      setErrorKind(reason instanceof BattleProviderError ? reason.kind : "adapter");
    });
    return () => {
      generation.current += 1;
      busy.current = false;
      pending.current = null;
      pendingOpening.current = null;
      pendingLogEvents.current = [];
    };
  }, [provider, loadAttempt]);

  const applyEvent = useCallback((event: BattleEvent) => {
    setVisibleSnapshot((current) => {
      if (!current) return current;
      const next = structuredClone(current);
      if (event.type === "turnStarted" && event.sourceId && next.combatants[event.sourceId]) {
        next.activeCombatantId = event.sourceId;
        next.turnControl = {
          disposition: "automaticAction",
          acceptsCommands: false,
          reasonId: "automaticResolution",
          actorCombatantId: event.sourceId,
          sourceCombatantId: null,
          forcedTargetIds: [],
        };
        next.legalActions = [];
        next.turnOrder = next.turnOrder.map((turn) => ({
          ...turn,
          isCurrent: turn.combatantId === event.sourceId,
        }));
      }
      if (event.type === "turnEnded" && event.sourceId) {
        next.turnOrder = next.turnOrder.map((turn) => turn.combatantId === event.sourceId
          ? { ...turn, hasActed: true }
          : turn);
      }
      if (
        event.type === "turnEnded"
        && event.sourceId
        && event.reasonId
        && ["glacier", "stunned", "paralyzed", "fear"].includes(event.reasonId)
        && next.combatants[event.sourceId]
      ) {
        next.activeCombatantId = event.sourceId;
        next.turnControl = {
          disposition: "skip",
          acceptsCommands: false,
          reasonId: event.reasonId,
          actorCombatantId: event.sourceId,
          sourceCombatantId: null,
          forcedTargetIds: [],
        };
        next.legalActions = [];
      }
      if (event.targetId && event.hpAfter && next.combatants[event.targetId]) next.combatants[event.targetId].hp = event.hpAfter;
      if (event.type === "statusApplied" && event.targetId && event.statusId && next.combatants[event.targetId]) {
        const statuses = next.combatants[event.targetId].statuses;
        const existing = statuses.find((status) => status.id === event.statusId);
        const kind = event.statusPresentation === "buff" ? "buff" : event.statusPresentation === "debuff" ? "debuff" : "other";
        if (existing) {
          existing.roundsRemaining = event.roundsRemaining ?? null;
          existing.kind = kind;
          if ("stacks" in event) existing.stacks = event.stacks ?? null;
          if (event.sourceId) existing.sourceCombatantId = event.sourceId;
        } else statuses.push({ id: event.statusId, instanceId: `${event.id}.status`, kind, roundsRemaining: event.roundsRemaining ?? null, stacks: event.stacks ?? null, sourceCombatantId: event.sourceId ?? null });
      }
      if (event.type === "statusRemoved" && event.targetId && event.statusId && next.combatants[event.targetId]) {
        next.combatants[event.targetId].statuses = next.combatants[event.targetId].statuses.filter(
          (status) => status.id !== event.statusId,
        );
      }
      if (event.type === "characterSummoned" && event.combatant) {
        next.combatants[event.combatant.id] = event.combatant;
        const side = next.sides.find((item) => item.id === event.combatant?.sideId);
        if (side && !side.combatantIds.includes(event.combatant.id)) side.combatantIds.push(event.combatant.id);
      }
      if (event.type === "characterDefeated" && event.targetId && next.combatants[event.targetId]) {
        next.combatants[event.targetId].alive = false;
      }
      return next;
    });
  }, []);

  const runPresentation = useCallback(async (request: () => Promise<PresentationScript>, opening: boolean) => {
    if (busy.current) return;
    busy.current = true;
    const token = ++generation.current;
    setIsPlaying(true);
    setError(null);
    setErrorKind(null);
    try {
      const script = await request();
      if (generation.current !== token) return;
      pending.current = script;
      setCanSkip(true);
      const orderedEvents = [...script.events].sort((a, b) => a.sequence - b.sequence);
      pendingLogEvents.current = orderedEvents.filter(isVisibleLogEvent);
      for (const event of orderedEvents) {
        if (generation.current !== token) return;
        if (isVisibleLogEvent(event)) {
          pendingLogEvents.current = pendingLogEvents.current.slice(1);
        }
        setActiveEvent(event);
        applyEvent(event);
        if (isVisibleLogEvent(event)) {
          setLog((items) => [...items, event]);
        }
        if (event.type !== "battleLog") {
          await new Promise((resolve) => window.setTimeout(resolve, BASE_DELAY / speed));
        }
      }
      if (generation.current !== token) return;
      setVisibleSnapshot(structuredClone(script.snapshot));
      setRevision(script.revision);
      pending.current = null;
      pendingLogEvents.current = [];
      setCanSkip(false);
    } catch (reason) {
      if (generation.current === token) {
        if (reason instanceof BattleProviderError && reason.snapshot && reason.revision !== undefined) {
          setVisibleSnapshot(structuredClone(reason.snapshot));
          setRevision(reason.revision);
        }
        setError(reason instanceof Error ? reason.message : "The command could not be submitted.");
        setErrorKind(reason instanceof BattleProviderError ? reason.kind : "adapter");
      }
    } finally {
      if (generation.current === token) {
        busy.current = false;
        setActiveEvent(null);
        setIsPlaying(false);
        if (opening) setIsOpening(false);
        setCanSkip(false);
      }
    }
  }, [applyEvent, speed]);

  const present = useCallback(
    (request: () => Promise<PresentationScript>) => runPresentation(request, false),
    [runPresentation],
  );

  const playOpening = useCallback(() => {
    const script = pendingOpening.current;
    if (!script || busy.current) return Promise.resolve();
    pendingOpening.current = null;
    setHasPendingOpening(false);
    return runPresentation(async () => script, true);
  }, [runPresentation]);

  const skip = useCallback(() => {
    const finalScript = pending.current;
    const remainingLogEvents = pendingLogEvents.current;
    generation.current += 1;
    pending.current = null;
    busy.current = false;
    if (finalScript) {
      setVisibleSnapshot(structuredClone(finalScript.snapshot));
      setRevision(finalScript.revision);
      setLog((items) => [...items, ...remainingLogEvents]);
    }
    pendingLogEvents.current = [];
    setActiveEvent(null);
    setIsPlaying(false);
    setIsOpening(false);
    setHasPendingOpening(false);
    setCanSkip(false);
  }, []);

  const retry = useCallback(() => {
    setError(null);
    setErrorKind(null);
    setLoadAttempt((attempt) => attempt + 1);
  }, []);

  return { snapshot: visibleSnapshot, revision, activeEvent, log, setLog, speed, setSpeed, isPlaying, isOpening, hasPendingOpening, canSkip, error, errorKind, present, playOpening, skip, retry };
}
