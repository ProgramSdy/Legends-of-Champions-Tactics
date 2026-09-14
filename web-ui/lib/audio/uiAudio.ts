import {
  useCallback,
  useRef,
  type FocusEvent,
  type KeyboardEvent,
  type MouseEvent,
  type PointerEvent,
} from "react";
import { audioManager, type AudioManager } from "./AudioManager";

export const UI_AUDIO_FEEDBACK_ATTRIBUTE = "data-audio-feedback";
export const UI_AUDIO_INTERACTIVE_VALUE = "interactive";

const OPT_IN_SELECTOR = `[${UI_AUDIO_FEEDBACK_ATTRIBUTE}="${UI_AUDIO_INTERACTIVE_VALUE}"]`;
const NATIVE_INTERACTIVE_SELECTOR = "button, a[href], input:not([type='hidden']), select, textarea";
const CUSTOM_INTERACTIVE_SELECTOR = "[role='button'], [role='link']";
const SEMANTIC_SELECTOR = `${NATIVE_INTERACTIVE_SELECTOR}, label`;
const ACTIVATION_DEDUPE_MS = 50;

export type UiAudioManager = Pick<AudioManager, "unlock" | "play">;

function associatedLabelControl(label: HTMLLabelElement): HTMLElement | null {
  if (label.htmlFor) return document.getElementById(label.htmlFor);
  return label.querySelector<HTMLElement>("button, input:not([type='hidden']), select, textarea");
}

function normalizeInteractiveElement(target: EventTarget | null): HTMLElement | null {
  if (!(target instanceof Element)) return null;

  const optedIn = target.closest<HTMLElement>(OPT_IN_SELECTOR);
  if (optedIn) return optedIn;

  const containingLabel = target.closest<HTMLLabelElement>("label");
  if (containingLabel && associatedLabelControl(containingLabel)) return containingLabel;

  const semantic = target.closest<HTMLElement>(SEMANTIC_SELECTOR);
  if (!semantic) return null;
  if (semantic instanceof HTMLInputElement && semantic.labels?.length) {
    return semantic.labels[0];
  }
  return semantic;
}

function hasInactiveAncestor(element: HTMLElement): boolean {
  let current: HTMLElement | null = element;
  while (current) {
    if (
      current.hidden
      || current.hasAttribute("inert")
      || current.getAttribute("aria-hidden") === "true"
      || current.style.display === "none"
      || current.style.visibility === "hidden"
    ) return true;
    current = current.parentElement;
  }
  return false;
}

function isEnabledInteractive(element: HTMLElement | null): element is HTMLElement {
  if (!element || hasInactiveAncestor(element)) return false;
  if (element.closest("[aria-disabled='true']")) return false;
  if (element.matches(":disabled")) return false;
  if (element instanceof HTMLLabelElement) {
    const control = associatedLabelControl(element);
    return Boolean(control && !control.matches(":disabled, [aria-disabled='true']"));
  }
  if (element.matches(CUSTOM_INTERACTIVE_SELECTOR) && !element.matches(NATIVE_INTERACTIVE_SELECTOR)) {
    return element.tabIndex >= 0;
  }
  if (element.matches(OPT_IN_SELECTOR) && !element.matches(`${NATIVE_INTERACTIVE_SELECTOR}, ${CUSTOM_INTERACTIVE_SELECTOR}`)) {
    return false;
  }
  return true;
}

/**
 * Shared delegated UI feedback for one explicit application or scene root.
 * Battle-event sounds do not enter this hook; they remain queue-owned.
 */
export function useUiAudioFeedback(manager: UiAudioManager = audioManager) {
  const pointerInside = useRef(new Set<HTMLElement>());
  const lastActivation = useRef<{ element: HTMLElement; timestamp: number } | null>(null);

  const onPointerDownCapture = useCallback((event: PointerEvent<HTMLElement>) => {
    if (isEnabledInteractive(normalizeInteractiveElement(event.target))) manager.unlock();
  }, [manager]);

  const onPointerOverCapture = useCallback((event: PointerEvent<HTMLElement>) => {
    if (event.pointerType === "touch") return;
    const current = normalizeInteractiveElement(event.target);
    if (!isEnabledInteractive(current)) return;
    if (current === normalizeInteractiveElement(event.relatedTarget)) return;
    pointerInside.current.add(current);
    manager.play("ui.hover");
  }, [manager]);

  const onPointerOutCapture = useCallback((event: PointerEvent<HTMLElement>) => {
    if (event.pointerType === "touch") return;
    const current = normalizeInteractiveElement(event.target);
    if (!current || current === normalizeInteractiveElement(event.relatedTarget)) return;
    pointerInside.current.delete(current);
  }, []);

  const onFocusCapture = useCallback((event: FocusEvent<HTMLElement>) => {
    const current = normalizeInteractiveElement(event.target);
    if (!isEnabledInteractive(current) || pointerInside.current.has(current)) return;
    manager.play("ui.hover");
  }, [manager]);

  const onKeyDownCapture = useCallback((event: KeyboardEvent<HTMLElement>) => {
    if (event.repeat || (event.key !== "Enter" && event.key !== " ")) return;
    if (isEnabledInteractive(normalizeInteractiveElement(event.target))) manager.unlock();
  }, [manager]);

  const onClickCapture = useCallback((event: MouseEvent<HTMLElement>) => {
    const current = normalizeInteractiveElement(event.target);
    if (!isEnabledInteractive(current)) return;
    manager.unlock();

    const previous = lastActivation.current;
    if (previous?.element === current && event.timeStamp - previous.timestamp < ACTIVATION_DEDUPE_MS) return;
    lastActivation.current = { element: current, timestamp: event.timeStamp };
    manager.play("ui.click");
  }, [manager]);

  return {
    onPointerDownCapture,
    onPointerOverCapture,
    onPointerOutCapture,
    onFocusCapture,
    onKeyDownCapture,
    onClickCapture,
  };
}
