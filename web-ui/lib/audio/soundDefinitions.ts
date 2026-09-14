export type SoundCategory = "ui" | "game-event" | "battle" | "music";

export type JsfxrPreset =
  | "pickupCoin"
  | "laserShoot"
  | "explosion"
  | "powerUp"
  | "hitHurt"
  | "jump"
  | "blipSelect"
  | "synth"
  | "tone"
  | "click"
  | "random";

export interface JsfxrProviderDefinition {
  type: "jsfxr";
  preset: JsfxrPreset;
  volume: number;
  overrides?: Readonly<Record<string, number | boolean>>;
}

export interface FileProviderDefinition {
  type: "file";
  src: string;
  volume: number;
}

export interface LayeredProviderDefinition {
  type: "layers";
  layers: ReadonlyArray<{
    delayMs: number;
    provider: JsfxrProviderDefinition | FileProviderDefinition;
  }>;
}

export type SoundProviderDefinition =
  | JsfxrProviderDefinition
  | FileProviderDefinition
  | LayeredProviderDefinition;

export interface SoundDefinition {
  category: SoundCategory;
  cooldownMs: number;
  provider: SoundProviderDefinition;
}

/**
 * Pre-alpha catalogue. Callers use only the stable key; the provider can later
 * change to file-backed or layered playback without changing UI code.
 */
export const soundDefinitions = {
  "ui.click": {
    category: "ui",
    cooldownMs: 35,
    provider: {
      type: "jsfxr",
      preset: "click",
      volume: 0.055,
      overrides: { p_base_freq: 0.52, p_env_sustain: 0.01, p_env_decay: 0.035, p_hpf_freq: 0.2 },
    },
  },
  "ui.hover": {
    category: "ui",
    cooldownMs: 90,
    provider: {
      type: "jsfxr",
      preset: "blipSelect",
      volume: 0.025,
      overrides: { p_base_freq: 0.78, p_env_sustain: 0.008, p_env_decay: 0.025, p_hpf_freq: 0.35 },
    },
  },
  "battle.event": {
    category: "game-event",
    cooldownMs: 0,
    provider: {
      type: "jsfxr",
      preset: "pickupCoin",
      volume: 0.075,
      overrides: { p_base_freq: 0.42, p_env_sustain: 0.08, p_env_decay: 0.16, p_arp_speed: 0.55, p_arp_mod: 0.18 },
    },
  },
  "battle.skill": {
    category: "battle",
    cooldownMs: 0,
    provider: {
      type: "jsfxr",
      preset: "laserShoot",
      volume: 0.12,
      overrides: { p_base_freq: 0.48, p_freq_ramp: -0.22, p_env_sustain: 0.12, p_env_decay: 0.12 },
    },
  },
  "battle.damage": {
    category: "battle",
    cooldownMs: 0,
    provider: {
      type: "jsfxr",
      preset: "hitHurt",
      volume: 0.115,
      overrides: { p_base_freq: 0.24, p_freq_ramp: -0.42, p_env_sustain: 0.055, p_env_decay: 0.1 },
    },
  },
  "battle.evade": {
    category: "battle",
    cooldownMs: 0,
    provider: {
      type: "jsfxr",
      preset: "jump",
      volume: 0.065,
      overrides: { p_base_freq: 0.58, p_freq_ramp: 0.3, p_env_sustain: 0.07, p_env_decay: 0.11, p_hpf_freq: 0.28 },
    },
  },
  "battle.buff": {
    category: "battle",
    cooldownMs: 0,
    provider: {
      type: "jsfxr",
      preset: "powerUp",
      volume: 0.08,
      overrides: { p_base_freq: 0.3, p_freq_ramp: 0.24, p_env_sustain: 0.18, p_env_decay: 0.2 },
    },
  },
  "battle.debuff": {
    category: "battle",
    cooldownMs: 0,
    provider: {
      type: "jsfxr",
      preset: "hitHurt",
      volume: 0.08,
      overrides: { p_base_freq: 0.34, p_freq_ramp: -0.32, p_env_sustain: 0.15, p_env_decay: 0.22, p_lpf_freq: 0.45 },
    },
  },
  "battle.defeated": {
    category: "battle",
    cooldownMs: 0,
    provider: {
      type: "jsfxr",
      preset: "explosion",
      volume: 0.14,
      overrides: { p_base_freq: 0.16, p_freq_ramp: -0.28, p_env_sustain: 0.24, p_env_decay: 0.42, p_lpf_freq: 0.55 },
    },
  },
} as const satisfies Record<string, SoundDefinition>;

export type SoundId = keyof typeof soundDefinitions;
