import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { markReleaseArtifact } from "./release-artifact-policy.mjs";

const scriptDirectory = dirname(fileURLToPath(import.meta.url));
await markReleaseArtifact(resolve(scriptDirectory, "..", "dist"), "development");
