import vinext from "vinext";
import { defineConfig } from "vite";
import { readFileSync } from "node:fs";
import hostingConfig from "./.openai/hosting.json";
import { sites } from "./build/sites-vite-plugin";

const SITE_CREATOR_PLACEHOLDER_DATABASE_ID =
  "00000000-0000-4000-8000-000000000000";

const { d1, r2 } = hostingConfig;

// macOS Seatbelt blocks FSEvents, so Codex previews need polling for HMR.
const isCodexSeatbeltSandbox = process.env.CODEX_SANDBOX === "seatbelt";

const localBindingConfig = {
  main: "./worker/index.ts",
  compatibility_flags: ["nodejs_compat"],
  d1_databases: d1
    ? [
        {
          binding: d1,
          database_name: "site-creator-d1",
          database_id: SITE_CREATOR_PLACEHOLDER_DATABASE_ID,
        },
      ]
    : [],
  r2_buckets: r2
    ? [
        {
          binding: r2,
          bucket_name: "site-creator-r2",
        },
      ]
    : [],
};

export default defineConfig(async () => {
  const releaseMode = process.env.LOCT_RELEASE_MODE === "development"
    ? "development"
    : "public";
  const telemetryEnabled = process.env.NEXT_PUBLIC_TELEMETRY_ENABLED === "true"
    ? "true"
    : "false";
  const feedbackUrl = process.env.NEXT_PUBLIC_FEEDBACK_URL ?? "";
  const localApiProxyTarget = process.env.LOCT_LOCAL_API_PROXY_TARGET;
  const localHttpsCert = process.env.LOCT_LOCAL_HTTPS_CERT;
  const localHttpsKey = process.env.LOCT_LOCAL_HTTPS_KEY;
  if ((localHttpsCert && !localHttpsKey) || (!localHttpsCert && localHttpsKey)) {
    throw new Error("LOCT_LOCAL_HTTPS_CERT and LOCT_LOCAL_HTTPS_KEY must be provided together.");
  }
  // Keep Wrangler and Miniflare state project-local. These are non-secret tool
  // settings; application environment belongs in ignored `.env*` files.
  process.env.WRANGLER_WRITE_LOGS ??= "false";
  process.env.WRANGLER_LOG_PATH ??= ".wrangler/logs";
  process.env.MINIFLARE_REGISTRY_PATH ??= ".wrangler/registry";

  // Wrangler snapshots its log path while the Cloudflare plugin is imported.
  const { cloudflare } = await import("@cloudflare/vite-plugin");

  return {
    define: {
      "process.env.LOCT_RELEASE_MODE": JSON.stringify(releaseMode),
      "process.env.NEXT_PUBLIC_TELEMETRY_ENABLED": JSON.stringify(telemetryEnabled),
      "process.env.NEXT_PUBLIC_FEEDBACK_URL": JSON.stringify(feedbackUrl),
    },
    server: {
      ...(localHttpsCert && localHttpsKey
        ? { https: { cert: readFileSync(localHttpsCert), key: readFileSync(localHttpsKey) } }
        : {}),
      ...(isCodexSeatbeltSandbox
        ? { watch: { useFsEvents: false, usePolling: true } }
        : {}),
      ...(localApiProxyTarget
        ? { proxy: { "/api": { target: localApiProxyTarget, changeOrigin: false } } }
        : {}),
    },
    plugins: [
      vinext(),
      sites(),
      cloudflare({
        viteEnvironment: { name: "rsc", childEnvironments: ["ssr"] },
        config: localBindingConfig,
      }),
    ],
  };
});
