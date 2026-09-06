"use client";

import { useEffect, useState } from "react";

export type BattleDisplayMode = "monitor" | "laptop-large" | "laptop-medium" | "pad" | "pad-mini" | "phone" | "portrait";

export type BattlePresentationConfig = {
  mode: BattleDisplayMode;
  browserSizeRate: number;
  orientation: "landscape" | "portrait";
  viewport: BattleViewport;
};

export type BattleViewport = { width: number; height: number };

const DISPLAY_CONFIGS: Record<BattleDisplayMode, Omit<BattlePresentationConfig, "orientation" | "viewport">> = {
  monitor: { mode: "monitor", browserSizeRate: 1 },
  "laptop-large": { mode: "laptop-large", browserSizeRate: 0.7 },
  "laptop-medium": { mode: "laptop-medium", browserSizeRate: 0.6 },
  pad: { mode: "pad", browserSizeRate: 0.5 },
  "pad-mini": { mode: "pad-mini", browserSizeRate: 0.84 },
  phone: { mode: "phone", browserSizeRate: 0.4 },
  // Portrait is intentionally a rotate-device state, not a battle layout.
  portrait: { mode: "portrait", browserSizeRate: 1 },
};

/**
 * Owns browser-size presentation only. It never changes engine positions,
 * target legality, hero metadata, or formation metadata.
 */
export function battlePresentationConfigFor(viewport: BattleViewport): BattlePresentationConfig {
  const { width, height } = viewport;
  const orientation = width >= height ? "landscape" : "portrait";
  if (orientation === "portrait") return { ...DISPLAY_CONFIGS.portrait, orientation, viewport };
  if (height <= 550) return { ...DISPLAY_CONFIGS.phone, orientation, viewport };
  if (width >= 1600 && height >= 900) return { ...DISPLAY_CONFIGS.monitor, orientation, viewport };
  if (width >= 1440 && height >= 750) return { ...DISPLAY_CONFIGS["laptop-large"], orientation, viewport };
  if (width >= 1180 && height >= 700) return { ...DISPLAY_CONFIGS["laptop-medium"], orientation, viewport };
  if (width >= 900) return { ...DISPLAY_CONFIGS.pad, orientation, viewport };
  if (width >= 700) return { ...DISPLAY_CONFIGS["pad-mini"], orientation, viewport };
  return { ...DISPLAY_CONFIGS.phone, orientation, viewport };
}

function currentViewport(): BattleViewport {
  if (typeof window === "undefined") return { width: 1920, height: 1080 };
  return { width: window.innerWidth, height: window.innerHeight };
}

/** The single React boundary that observes browser dimensions for Battle Scene presentation. */
export function useBattlePresentationConfig(): BattlePresentationConfig {
  const [config, setConfig] = useState(() => battlePresentationConfigFor(currentViewport()));

  useEffect(() => {
    const update = () => setConfig(battlePresentationConfigFor(currentViewport()));
    window.addEventListener("resize", update);
    window.addEventListener("orientationchange", update);
    return () => {
      window.removeEventListener("resize", update);
      window.removeEventListener("orientationchange", update);
    };
  }, []);

  return config;
}
