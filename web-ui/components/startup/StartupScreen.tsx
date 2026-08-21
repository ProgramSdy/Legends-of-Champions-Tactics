"use client";

import Image from "next/image";
import { useRouter } from "next/navigation";
import {
  createSaveSlot,
  fetchSaveSlots,
  loadSaveSlot,
  overwriteSaveSlot,
} from "@/lib/battle/liveProvider";
import type { SaveSlotId, SaveSlotSummary } from "@/lib/battle/types";
import {
  useEffect,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";

const STARTUP_BACKGROUND = "/game-images/Game_Startup/Game_Startup_01.png";
const GAME_LOGO = "/game-images/Game_Logo/Game_Logo_01.png";

type StartupView = "closed" | "choices" | "new" | "load" | "overwrite";

function timestampLabel(value: string | null): string {
  if (!value) return "Not played";
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime())
    ? value
    : new Intl.DateTimeFormat(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
      }).format(parsed);
}

function SaveSlotButton({
  slot,
  mode,
  disabled,
  onSelect,
}: {
  slot: SaveSlotSummary;
  mode: "new" | "load";
  disabled: boolean;
  onSelect: () => void;
}) {
  const stateLabel = slot.occupied ? "Occupied" : "Empty";
  const actionLabel = mode === "load"
    ? slot.occupied ? "Load saved game" : "No saved game"
    : slot.occupied ? "Overwrite confirmation required" : "Start a new game";
  return (
    <button
      type="button"
      className={`save-slot-card ${slot.occupied ? "occupied" : "empty"}${slot.active ? " active" : ""}`}
      disabled={disabled}
      aria-label={`Save Slot ${slot.slotId}, ${stateLabel}. ${actionLabel}`}
      onClick={onSelect}
    >
      <span className="save-slot-number">SLOT {slot.slotId}</span>
      <strong>{stateLabel}</strong>
      <span>{actionLabel}</span>
      {slot.occupied ? (
        <small>
          {slot.active ? <b>ACTIVE · </b> : null}
          Last played <time dateTime={slot.lastPlayedAt ?? undefined}>{timestampLabel(slot.lastPlayedAt)}</time>
        </small>
      ) : <small>Four starting heroes · Training progress 0</small>}
    </button>
  );
}

export function StartupScreen() {
  const router = useRouter();
  const startRef = useRef<HTMLButtonElement>(null);
  const dialogRef = useRef<HTMLElement>(null);
  const newGameRef = useRef<HTMLButtonElement>(null);
  const overwriteConfirmRef = useRef<HTMLButtonElement>(null);
  const [view, setView] = useState<StartupView>("closed");
  const [slots, setSlots] = useState<SaveSlotSummary[] | null>(null);
  const [selectedSlot, setSelectedSlot] = useState<SaveSlotSummary | null>(null);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const occupiedSlots = slots?.filter((slot) => slot.occupied) ?? [];
  const loadUnavailable = !loadingSlots && slots !== null && occupiedSlots.length === 0;

  const refreshSlots = async () => {
    setLoadingSlots(true);
    setError(null);
    try {
      const response = await fetchSaveSlots();
      setSlots(response.slots);
    } catch (reason: unknown) {
      setSlots(null);
      setError(reason instanceof Error ? reason.message : "Unable to load save slots.");
    } finally {
      setLoadingSlots(false);
    }
  };

  const openStartupMenu = () => {
    setView("choices");
    setSelectedSlot(null);
    void refreshSlots();
  };

  const closeStartupMenu = () => {
    if (actionLoading) return;
    setView("closed");
    setSelectedSlot(null);
    setError(null);
    window.requestAnimationFrame(() => startRef.current?.focus());
  };

  useEffect(() => {
    if (view === "closed" || loadingSlots || actionLoading) return;
    window.requestAnimationFrame(() => {
      if (view === "choices") {
        if (newGameRef.current && !newGameRef.current.disabled) {
          newGameRef.current.focus();
        } else {
          dialogRef.current?.querySelector<HTMLButtonElement>("button:not(:disabled)")?.focus();
        }
      } else if (view === "overwrite") {
        overwriteConfirmRef.current?.focus();
      } else {
        dialogRef.current?.querySelector<HTMLButtonElement>(".save-slot-card:not(:disabled)")?.focus();
      }
    });
  }, [actionLoading, loadingSlots, view]);

  const handleDialogKeyDown = (event: KeyboardEvent<HTMLElement>) => {
    if (event.key === "Escape") {
      event.preventDefault();
      if (actionLoading) return;
      if (view === "overwrite") {
        setView("new");
        setSelectedSlot(null);
      } else if (view === "new" || view === "load") {
        setView("choices");
      } else {
        closeStartupMenu();
      }
      return;
    }
    if (event.key !== "Tab") return;
    const focusable = Array.from(
      dialogRef.current?.querySelectorAll<HTMLElement>(
        "button:not(:disabled), [href], [tabindex]:not([tabindex='-1'])",
      ) ?? [],
    ).filter((element) => !element.hasAttribute("disabled"));
    if (focusable.length === 0) return;
    const first = focusable[0];
    const last = focusable.at(-1)!;
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  };

  const finishSlotAction = async (
    slotId: SaveSlotId,
    action: "create" | "load" | "overwrite",
  ) => {
    setActionLoading(true);
    setError(null);
    try {
      if (action === "create") await createSaveSlot(slotId);
      else if (action === "load") await loadSaveSlot(slotId);
      else await overwriteSaveSlot(slotId);
      router.push("/stages");
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "The save-slot action failed.");
      setActionLoading(false);
    }
  };

  const selectNewSlot = (slot: SaveSlotSummary) => {
    if (slot.occupied) {
      setSelectedSlot(slot);
      setError(null);
      setView("overwrite");
      return;
    }
    void finishSlotAction(slot.slotId, "create");
  };

  return (
    <main className="startup-screen">
      <Image
        className="startup-background"
        src={STARTUP_BACKGROUND}
        alt=""
        aria-hidden="true"
        fill
        priority
        sizes="100vw"
        unoptimized
      />
      <div className="startup-content">
        <h1 className="startup-title">
          <Image
            className="startup-logo"
            src={GAME_LOGO}
            alt="Legends of Champions Tactics"
            width={1536}
            height={1024}
            priority
            unoptimized
          />
        </h1>
        <button ref={startRef} className="startup-action" type="button" onClick={openStartupMenu}>
          <span>START GAME</span>
        </button>
      </div>

      {view !== "closed" ? (
        <div className="startup-dialog-backdrop">
          <section
            ref={dialogRef}
            className="startup-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="startup-dialog-title"
            aria-describedby="startup-dialog-description"
            onKeyDown={handleDialogKeyDown}
          >
            {view === "choices" ? (
              <>
                <small>LOCAL ADVENTURE</small>
                <h2 id="startup-dialog-title">Choose your journey</h2>
                <p id="startup-dialog-description">Begin in an empty save slot or continue an occupied one.</p>
                {loadingSlots ? <p className="startup-dialog-status" aria-live="polite">Loading save slots…</p> : null}
                {error ? (
                  <div className="startup-dialog-error" role="alert">
                    <strong>SAVE SLOTS UNAVAILABLE</strong>
                    <span>{error}</span>
                    <button type="button" onClick={() => void refreshSlots()}>RETRY</button>
                  </div>
                ) : null}
                <div className="startup-choice-actions">
                  <button
                    ref={newGameRef}
                    type="button"
                    disabled={loadingSlots || !slots}
                    onClick={() => { setError(null); setView("new"); }}
                  >
                    <strong>NEW GAME</strong>
                    <span>Choose any of five slots</span>
                  </button>
                  <button
                    type="button"
                    disabled={loadingSlots || !slots || loadUnavailable}
                    aria-describedby={loadUnavailable ? "load-game-unavailable" : undefined}
                    onClick={() => { setError(null); setView("load"); }}
                  >
                    <strong>LOAD GAME</strong>
                    <span>Continue saved progression</span>
                  </button>
                </div>
                {loadUnavailable ? <p id="load-game-unavailable" className="load-game-unavailable">No saved games. Create a New Game first.</p> : null}
                <button className="startup-dialog-cancel" type="button" disabled={actionLoading} onClick={closeStartupMenu}>CANCEL</button>
              </>
            ) : view === "overwrite" && selectedSlot ? (
              <>
                <small>DESTRUCTIVE ACTION</small>
                <h2 id="startup-dialog-title">Overwrite Save Slot {selectedSlot.slotId}?</h2>
                <p id="startup-dialog-description">
                  Save Slot {selectedSlot.slotId}&apos;s saved progression will be permanently replaced. This cannot be undone.
                </p>
                {error ? <p className="startup-dialog-error compact" role="alert">{error}</p> : null}
                <div className="overwrite-actions">
                  <button
                    type="button"
                    disabled={actionLoading}
                    onClick={() => { setError(null); setSelectedSlot(null); setView("new"); }}
                  >KEEP SAVE SLOT {selectedSlot.slotId}</button>
                  <button
                    ref={overwriteConfirmRef}
                    className="destructive"
                    type="button"
                    disabled={actionLoading}
                    onClick={() => void finishSlotAction(selectedSlot.slotId, "overwrite")}
                  >{actionLoading ? "OVERWRITING…" : `OVERWRITE SLOT ${selectedSlot.slotId}`}</button>
                </div>
              </>
            ) : (
              <>
                <small>{view === "load" ? "LOAD GAME" : "NEW GAME"}</small>
                <h2 id="startup-dialog-title">Choose a save slot</h2>
                <p id="startup-dialog-description">
                  {view === "load"
                    ? "Only occupied slots can be loaded. Empty slots are unavailable."
                    : "Empty slots start fresh. Occupied slots require overwrite confirmation."}
                </p>
                {error ? <p className="startup-dialog-error compact" role="alert">{error}</p> : null}
                <div className="save-slot-grid" aria-label="Five local save slots">
                  {slots?.map((slot) => (
                    <SaveSlotButton
                      key={slot.slotId}
                      slot={slot}
                      mode={view === "load" ? "load" : "new"}
                      disabled={actionLoading || (view === "load" && !slot.occupied)}
                      onSelect={() => view === "load"
                        ? void finishSlotAction(slot.slotId, "load")
                        : selectNewSlot(slot)}
                    />
                  ))}
                </div>
                <p className="startup-dialog-status" aria-live="polite">
                  {actionLoading ? `${view === "load" ? "Loading" : "Creating"} save slot…` : ""}
                </p>
                <button
                  className="startup-dialog-cancel"
                  type="button"
                  disabled={actionLoading}
                  onClick={() => { setError(null); setView("choices"); }}
                >BACK</button>
              </>
            )}
          </section>
        </div>
      ) : null}
    </main>
  );
}
