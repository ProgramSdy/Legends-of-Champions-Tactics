import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { verifyPublicArtifact } from "./release-artifact-policy.mjs";

const scriptDirectory = dirname(fileURLToPath(import.meta.url));
const publicArtifact = resolve(scriptDirectory, "..", "dist");

await verifyPublicArtifact(publicArtifact);
console.log("Verified public frontend artifact: Engineering routes and page bundle are absent.");
