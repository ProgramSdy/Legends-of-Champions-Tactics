import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import {
  markReleaseArtifact,
  verifyPublicArtifact,
} from "@/scripts/release-artifact-policy.mjs";

const temporaryDirectories: string[] = [];

async function artifactDirectory() {
  const directory = await mkdtemp(join(tmpdir(), "loct-release-001-"));
  temporaryDirectories.push(directory);
  return directory;
}

afterEach(async () => {
  await Promise.all(temporaryDirectories.splice(0).map((directory) => rm(directory, { recursive: true, force: true })));
});

describe("public release artifact policy", () => {
  it("accepts a marked public artifact without Engineering routes", async () => {
    const directory = await artifactDirectory();
    await markReleaseArtifact(directory, "public");
    await writeFile(join(directory, "index.js"), "normal gameplay bundle", "utf8");

    await expect(verifyPublicArtifact(directory)).resolves.toBeUndefined();
  });

  it("rejects missing or Development artifact markers", async () => {
    const missing = await artifactDirectory();
    await expect(verifyPublicArtifact(missing)).rejects.toThrow();

    const development = await artifactDirectory();
    await markReleaseArtifact(development, "development");
    await expect(verifyPublicArtifact(development)).rejects.toThrow(/not marked/);
  });

  it("rejects a forbidden route or page-specific client bundle", async () => {
    const route = await artifactDirectory();
    await markReleaseArtifact(route, "public");
    await writeFile(join(route, "server.js"), "route:/debug", "utf8");
    await expect(verifyPublicArtifact(route)).rejects.toThrow(/debug route/);

    const chunk = await artifactDirectory();
    await markReleaseArtifact(chunk, "public");
    await writeFile(join(chunk, "DebugBattleExperience.js"), "client module", "utf8");
    await expect(verifyPublicArtifact(chunk)).rejects.toThrow(/Engineering page file/);
  });

  it("rejects a Development adapter origin from a Public artifact", async () => {
    const directory = await artifactDirectory();
    await markReleaseArtifact(directory, "public");
    await writeFile(join(directory, "index.js"), "fetch('http://localhost:8001/api/v1/battles')", "utf8");

    await expect(verifyPublicArtifact(directory)).rejects.toThrow(/Development adapter origin/);
  });
});
