import { readdir, readFile, writeFile } from "node:fs/promises";
import { join, relative } from "node:path";

export const RELEASE_ARTIFACT_MARKER = ".loct-release-mode";

async function listFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) files.push(...await listFiles(path));
    else if (entry.isFile()) files.push(path);
  }
  return files;
}

export async function markReleaseArtifact(directory, mode) {
  await writeFile(join(directory, RELEASE_ARTIFACT_MARKER), `${mode}\n`, "utf8");
}

export async function verifyPublicArtifact(directory, { requireMarker = true } = {}) {
  if (requireMarker) {
    const marker = await readFile(join(directory, RELEASE_ARTIFACT_MARKER), "utf8");
    if (marker.trim() !== "public") {
      throw new Error("Frontend artifact is not marked as a verified public release.");
    }
  }

  const files = await listFiles(directory);
  const forbiddenFile = files.find((path) => /DebugBattleExperience|app[\\/]debug|app[\\/]assets/i.test(relative(directory, path)));
  if (forbiddenFile) {
    throw new Error(`Public artifact contains an Engineering page file: ${relative(directory, forbiddenFile)}`);
  }

  const textExtensions = new Set([".html", ".js", ".json", ".map", ".txt"]);
  const forbiddenText = [
    { label: "debug route", pattern: /route:\/debug\b|app[\\/]debug[\\/]page/ },
    { label: "asset diagnostics route", pattern: /route:\/assets\b|app[\\/]assets[\\/]page/ },
    { label: "debug page client module", pattern: /DebugBattleExperience/ },
    { label: "Development adapter origin", pattern: /https?:\/\/(?:localhost|127\.0\.0\.1):8001\b/ },
  ];
  const configuredDevelopmentOrigin = process.env.NEXT_PUBLIC_BATTLE_API_URL?.trim();

  for (const path of files) {
    const extension = path.slice(path.lastIndexOf("."));
    if (!textExtensions.has(extension)) continue;
    const contents = await readFile(path, "utf8");
    if (configuredDevelopmentOrigin && contents.includes(configuredDevelopmentOrigin)) {
      throw new Error(`Public artifact contains configured Development adapter origin in ${relative(directory, path)}.`);
    }
    const finding = forbiddenText.find(({ pattern }) => pattern.test(contents));
    if (finding) {
      throw new Error(`Public artifact contains ${finding.label} in ${relative(directory, path)}.`);
    }
  }
}
