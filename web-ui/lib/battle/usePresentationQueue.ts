"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { BattleProviderError, type BattleEvent, type BattleProvider, type BattleSnapshot, type PresentationScript, type ProviderErrorKind } from "./types";

const BASE_DELAY = 620;

export function usePresentationQueue(provider: BattleProvider) {
  const [visibleSnapshot, setVisibleSnapshot] = useState<BattleSnapshot | null>(null);
  const [revision, setRevision] = useState(0);
  const [activeEvent, setActiveEvent] = useState<BattleEvent | null>(null);
  const [log, setLog] = useState<BattleEvent[]>([]);
  const [speed, setSpeed] = useState(1);
  const [isPlaying, setIsPlaying] = useState(false);
  const [canSkip, setCanSkip] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errorKind, setErrorKind] = useState<ProviderErrorKind | null>(null);
  const generation = useRef(0);
  const busy = useRef(false);
  const pending = useRef<PresentationScript | null>(null);
  const pendingLogEvents = useRef<BattleEvent[]>([]);

  const [loadAttempt, setLoadAttempt] = useState(0);
  useEffect(() => {
    const token = ++generation.current;
    provider.getState().then((state) => {
      if (generation.current !== token) return;
      setVisibleSnapshot(structuredClone(state.snapshot));
      setRevision(state.revision);
      setLog([...(state.events ?? [])].sort((a, b) => a.sequence - b.sequence));
      setError(null);
      setErrorKind(null);
    }).catch((reason: unknown) => {
      setError(reason instanceof Error ? reason.message : "Unable to load battle.");
      setErrorKind(reason instanceof BattleProviderError ? reason.kind : "adapter");
    });
    return () => { generation.current += 1; };
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
        if (existing) existing.roundsRemaining = event.roundsRemaining ?? null;
        else statuses.push({ id: event.statusId, instanceId: `${event.id}.status`, kind: "debuff", roundsRemaining: event.roundsRemaining ?? null, stacks: null, sourceCombatantId: event.sourceId ?? null });
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
      return next;
    });
  }, []);

  const present = useCallback(async (request: () => Promise<PresentationScript>) => {
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
      pendingLogEvents.current = orderedEvents;
      for (const event of orderedEvents) {
        if (generation.current !== token) return;
        pendingLogEvents.current = pendingLogEvents.current.slice(1);
        setActiveEvent(event);
        applyEvent(event);
        setLog((items) => [...items, event]);
        await new Promise((resolve) => window.setTimeout(resolve, BASE_DELAY / speed));
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
        setCanSkip(false);
      }
    }
  }, [applyEvent, speed]);

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
    setCanSkip(false);
  }, []);

  const retry = useCallback(() => {
    setError(null);
    setErrorKind(null);
    setLoadAttempt((attempt) => attempt + 1);
  }, []);

  return { snapshot: visibleSnapshot, revision, activeEvent, log, setLog, speed, setSpeed, isPlaying, canSkip, error, errorKind, present, skip, retry };
}
