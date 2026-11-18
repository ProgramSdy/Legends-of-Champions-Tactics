import { spawn } from "node:child_process";
import { cp, mkdir, readdir, rm, stat } from "node:fs/promises";
import { dirname, join, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { markReleaseArtifact, RELEASE_ARTIFACT_MARKER, verifyPublicArtifact } from "./release-artifact-policy.mjs";

const scriptDirectory = dirname(fileURLToPath(import.meta.url));
const sourceRoot = resolve(scriptDirectory, "..");
const stagingRoot = join(sourceRoot, ".public-release-source");
const stagedDist = join(stagingRoot, "dist");
const publishedDist = join(sourceRoot, "dist");
const vinextCli = join(sourceRoot, "node_modules", "vinext", "dist", "cli.js");

const excludedTopLevel = new Set([
  ".git",
  ".next",
  ".public-release-source",
  ".vinext",
  ".wrangler",
  "coverage",
  "dist",
  "node_modules",
  "out",
  "outputs",
  "work",
]);

const excludedRoutes = new Set([
  join("app", "debug"),
  join("app", "assets"),
]);

function includeInPublicSource(sourcePath) {
  const pathFromRoot = relative(sourceRoot, sourcePath);
  if (!pathFromRoot) return true;
  const parts = pathFromRoot.split(sep);
  if (excludedTopLevel.has(parts[0])) return false;
  if (parts[0].startsWith(".env")) return false;
  return ![...excludedRoutes].some(
    (route) => pathFromRoot === route || pathFromRoot.startsWith(`${route}${sep}`),
  );
}

async function runVinextBuild() {
  await new Promise((resolveBuild, rejectBuild) => {
    const child = spawn(process.execPath, [vinextCli, "build"], {
      cwd: stagingRoot,
      env: {
        ...process.env,
        LOCT_RELEASE_MODE: "public",
        WRANGLER_LOG_PATH: ".wrangler/wrangler.log",
      },
      stdio: "inherit",
    });
    child.once("error", rejectBuild);
    child.once("exit", (code, signal) => {
      if (code === 0) resolveBuild();
      else rejectBuild(new Error(`Public vinext build failed (${signal ?? `exit ${code}`}).`));
    });
  });
}

async function buildPublicRelease() {
  await rm(join(publishedDist, RELEASE_ARTIFACT_MARKER), { force: true });
  await rm(stagingRoot, { recursive: true, force: true });
  await mkdir(stagingRoot, { recursive: true });
  const sourceEntries = await readdir(sourceRoot, { withFileTypes: true });
  for (const entry of sourceEntries) {
    const sourcePath = join(sourceRoot, entry.name);
    if (!includeInPublicSource(sourcePath)) continue;
    await cp(sourcePath, join(stagingRoot, entry.name), {
      recursive: entry.isDirectory(),
      force: false,
      filter: includeInPublicSource,
    });
  }

  for (const route of excludedRoutes) {
    try {
      await stat(join(stagingRoot, route));
      throw new Error(`Engineering route was copied into public staging: ${route}`);
    } catch (error) {
      if (error?.code !== "ENOENT") throw error;
    }
  }

  await runVinextBuild();
  await verifyPublicArtifact(stagedDist, { requireMarker: false });
  await markReleaseArtifact(stagedDist, "public");

  await rm(publishedDist, { recursive: true, force: true });
  await cp(stagedDist, publishedDist, { recursive: true });
  console.log("Public frontend artifact verified and published to web-ui/dist.");
}

try {
  await buildPublicRelease();
} finally {
  await rm(stagingRoot, { recursive: true, force: true });
}
