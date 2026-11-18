export const RELEASE_MODE_ENV = "LOCT_RELEASE_MODE";

export type ReleaseMode = "development" | "public";

/**
 * Engineering surfaces are enabled only by the exact server-controlled
 * Development value. Missing, blank, or unknown values fail closed.
 */
export function resolveReleaseMode(value = process.env.LOCT_RELEASE_MODE): ReleaseMode {
  return value === "development" ? "development" : "public";
}

export function isEngineeringMode(value = process.env.LOCT_RELEASE_MODE): boolean {
  return resolveReleaseMode(value) === "development";
}
