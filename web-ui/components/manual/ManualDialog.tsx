"use client";

import { useEffect, useRef, type KeyboardEvent, type RefObject } from "react";
import { useRouter } from "next/navigation";
import { useSoundPreference } from "@/components/audio/SoundPreferenceProvider";

type ManualDialogProps = {
  open: boolean;
  onClose: () => void;
  triggerRef: RefObject<HTMLButtonElement | null>;
};

const FOCUSABLE_SELECTOR = "button:not(:disabled), a[href], [tabindex]:not([tabindex='-1'])";

function focusableInManual(dialog: HTMLElement | null): HTMLElement[] {
  const focusable = Array.from(dialog?.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR) ?? []);
  const close = focusable.find((element) => element.classList.contains("manual-close"));
  return close ? [...focusable.filter((element) => element !== close), close] : focusable;
}

export function ManualDialog({ open, onClose, triggerRef }: ManualDialogProps) {
  const router = useRouter();
  const dialogRef = useRef<HTMLElement>(null);
  const firstOptionRef = useRef<HTMLButtonElement>(null);
  const { enabled, toggle } = useSoundPreference();

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: globalThis.KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        closeAndRestoreFocus();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    window.requestAnimationFrame(() => {
      firstOptionRef.current?.focus();
    });
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose, open]);

  function closeAndRestoreFocus() {
    onClose();
    window.requestAnimationFrame(() => triggerRef.current?.focus());
  }

  function trapFocus(event: KeyboardEvent<HTMLElement>) {
    if (event.key !== "Tab") return;
    const focusable = focusableInManual(dialogRef.current);
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
  }

  if (!open) return null;

  return (
    <div className="manual-dialog-backdrop" onMouseDown={(event) => {
      if (event.target === event.currentTarget) closeAndRestoreFocus();
    }}>
      <section
        className="manual-dialog"
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="manual-heading"
        onKeyDown={trapFocus}
      >
        <header>
          <div>
            <small>LEGENDS OF CHAMPIONS TACTICS</small>
            <h2 id="manual-heading">Game Manual</h2>
          </div>
          <button type="button" className="manual-close" onClick={closeAndRestoreFocus} aria-label="Close Game Manual">×</button>
        </header>
        <div className="manual-options" aria-label="Game Manual options">
          <button ref={firstOptionRef} type="button" onClick={() => router.push("/manual/heroes")}>
            <span aria-hidden="true">♜</span><strong>Hero Gallery</strong><small>Browse every approved specialization</small>
          </button>
          <button type="button" onClick={() => router.push("/manual/battle-instruction")}>
            <span aria-hidden="true">⚔</span><strong>Battle Instruction</strong><small>Learn the battlefield fundamentals</small>
          </button>
          <button type="button" onClick={toggle} aria-pressed={enabled}>
            <span aria-hidden="true">♫</span><strong>Sound {enabled ? "On" : "Off"}</strong><small>{enabled ? "UI and battle effects enabled" : "UI and battle effects muted"}</small>
          </button>
        </div>
      </section>
    </div>
  );
}
