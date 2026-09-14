declare module "jsfxr" {
  export interface JsfxrApi {
    generate(
      preset: string,
      options?: { sound_vol?: number; sample_rate?: number; sample_size?: number },
    ): Record<string, unknown>;
    play(definition: Record<string, unknown> | string): void | Promise<void>;
  }

  export const sfxr: JsfxrApi;
}
