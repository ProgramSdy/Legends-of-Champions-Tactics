"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { audioManager, type AudioManager } from "@/lib/audio/AudioManager";

const SOUND_PREFERENCE_KEY = "legends-of-champions-tactics.sound-enabled";

type SoundPreferenceManager = Pick<AudioManager, "setEnabled" | "isEnabled">;

type SoundPreferenceValue = {
  enabled: boolean;
  setEnabled: (enabled: boolean) => void;
  toggle: () => void;
};

const SoundPreferenceContext = createContext<SoundPreferenceValue | null>(null);

function readStoredPreference(): boolean | null {
  try {
    const value = window.localStorage.getItem(SOUND_PREFERENCE_KEY);
    return value === null ? null : value === "true";
  } catch {
    return null;
  }
}

function writeStoredPreference(enabled: boolean): void {
  try {
    window.localStorage.setItem(SOUND_PREFERENCE_KEY, String(enabled));
  } catch {
    // Storage is a convenience only; unavailable storage must not block play.
  }
}

export function SoundPreferenceProvider({
  children,
  manager = audioManager,
}: {
  children: ReactNode;
  manager?: SoundPreferenceManager;
}) {
  // Start from one SSR-safe value. Restoring browser storage during render can
  // disagree with the server markup and briefly set a different audio state.
  const [enabled, setEnabledState] = useState(true);

  useEffect(() => {
    let active = true;
    Promise.resolve().then(() => {
      if (!active) return;
      const restored = readStoredPreference();
      const next = restored ?? true;
      setEnabledState(next);
      manager.setEnabled(next);
    });
    return () => { active = false; };
  }, [manager]);

  const setEnabled = useCallback((next: boolean) => {
    manager.setEnabled(next);
    setEnabledState(next);
    writeStoredPreference(next);
  }, [manager]);

  const value = useMemo<SoundPreferenceValue>(() => ({
    enabled,
    setEnabled,
    toggle: () => setEnabled(!enabled),
  }), [enabled, setEnabled]);

  return <SoundPreferenceContext.Provider value={value}>{children}</SoundPreferenceContext.Provider>;
}

export function useSoundPreference(): SoundPreferenceValue {
  const preference = useContext(SoundPreferenceContext);
  if (!preference) {
    throw new Error("useSoundPreference must be used inside SoundPreferenceProvider.");
  }
  return preference;
}
