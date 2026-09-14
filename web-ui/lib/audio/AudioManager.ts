import {
  soundDefinitions,
  type JsfxrProviderDefinition,
  type SoundDefinition,
  type SoundId,
  type SoundProviderDefinition,
} from "./soundDefinitions";

interface JsfxrApi {
  generate(
    preset: string,
    options?: { sound_vol?: number; sample_rate?: number; sample_size?: number },
  ): Record<string, unknown>;
  play(definition: Record<string, unknown> | string): void | Promise<void>;
}

interface FileAudio {
  volume: number;
  play(): void | Promise<void>;
}

export interface AudioManagerDependencies {
  isBrowser?: () => boolean;
  now?: () => number;
  loadJsfxr?: () => Promise<JsfxrApi>;
  createFileAudio?: (src: string) => FileAudio | null;
  schedule?: (callback: () => void, delayMs: number) => void;
  definitions?: Readonly<Record<SoundId, SoundDefinition>>;
}

export interface PlaySoundOptions {
  /** A semantic occurrence key. Reusing it is always silent. */
  dedupeKey?: string;
}

const DEDUPE_HISTORY_LIMIT = 512;

function defaultIsBrowser(): boolean {
  return typeof window !== "undefined"
    && typeof document !== "undefined"
    && !(typeof navigator !== "undefined" && /jsdom/i.test(navigator.userAgent));
}

function defaultNow(): number {
  return typeof performance !== "undefined" ? performance.now() : Date.now();
}

async function defaultLoadJsfxr(): Promise<JsfxrApi> {
  const jsfxrModule = await import("jsfxr");
  return jsfxrModule.sfxr;
}

function defaultCreateFileAudio(src: string): FileAudio | null {
  if (typeof Audio === "undefined") return null;
  return new Audio(src);
}

function defaultSchedule(callback: () => void, delayMs: number): void {
  window.setTimeout(callback, delayMs);
}

/**
 * Sole provider boundary for browser sound. Construction and imports are SSR
 * safe; provider loading starts only after unlock() receives a trusted UI cue.
 */
export class AudioManager {
  private readonly isBrowser: () => boolean;
  private readonly now: () => number;
  private readonly loadJsfxr: () => Promise<JsfxrApi>;
  private readonly createFileAudio: (src: string) => FileAudio | null;
  private readonly schedule: (callback: () => void, delayMs: number) => void;
  private readonly definitions: Readonly<Record<SoundId, SoundDefinition>>;
  private unlocked = false;
  private jsfxrPromise: Promise<JsfxrApi> | null = null;
  private readonly generatedJsfxr = new Map<SoundId, Record<string, unknown>>();
  private readonly lastPlayedAt = new Map<SoundId, number>();
  private readonly dedupeHistory = new Set<string>();

  constructor(dependencies: AudioManagerDependencies = {}) {
    this.isBrowser = dependencies.isBrowser ?? defaultIsBrowser;
    this.now = dependencies.now ?? defaultNow;
    this.loadJsfxr = dependencies.loadJsfxr ?? defaultLoadJsfxr;
    this.createFileAudio = dependencies.createFileAudio ?? defaultCreateFileAudio;
    this.schedule = dependencies.schedule ?? defaultSchedule;
    this.definitions = dependencies.definitions ?? soundDefinitions;
  }

  unlock(): void {
    if (!this.isBrowser() || this.unlocked) return;
    this.unlocked = true;
  }

  play(id: SoundId, options: PlaySoundOptions = {}): void {
    if (!this.unlocked || !this.isBrowser()) return;
    const definition = this.definitions[id];
    if (!definition) return;

    if (options.dedupeKey) {
      if (this.dedupeHistory.has(options.dedupeKey)) return;
      this.dedupeHistory.add(options.dedupeKey);
      if (this.dedupeHistory.size > DEDUPE_HISTORY_LIMIT) {
        const oldest = this.dedupeHistory.values().next().value as string | undefined;
        if (oldest) this.dedupeHistory.delete(oldest);
      }
    }

    const timestamp = this.now();
    const lastPlayed = this.lastPlayedAt.get(id);
    if (lastPlayed !== undefined && timestamp - lastPlayed < definition.cooldownMs) return;
    this.lastPlayedAt.set(id, timestamp);
    void this.playProvider(id, definition.provider).catch(() => undefined);
  }

  private getJsfxr(): Promise<JsfxrApi> {
    this.jsfxrPromise ??= this.loadJsfxr();
    return this.jsfxrPromise;
  }

  private async playJsfxr(id: SoundId, provider: JsfxrProviderDefinition): Promise<void> {
    const jsfxr = await this.getJsfxr();
    let generated = this.generatedJsfxr.get(id);
    if (!generated) {
      generated = jsfxr.generate(provider.preset, { sound_vol: provider.volume });
      if (provider.overrides) Object.assign(generated, provider.overrides);
      this.generatedJsfxr.set(id, generated);
    }
    await jsfxr.play(generated);
  }

  private async playProvider(id: SoundId, provider: SoundProviderDefinition): Promise<void> {
    if (provider.type === "jsfxr") {
      await this.playJsfxr(id, provider);
      return;
    }
    if (provider.type === "file") {
      const audio = this.createFileAudio(provider.src);
      if (!audio) return;
      audio.volume = provider.volume;
      await audio.play();
      return;
    }
    for (const layer of provider.layers) {
      const playLayer = () => {
        void this.playProvider(id, layer.provider).catch(() => undefined);
      };
      if (layer.delayMs > 0) this.schedule(playLayer, layer.delayMs);
      else playLayer();
    }
  }
}

export const audioManager = new AudioManager();
