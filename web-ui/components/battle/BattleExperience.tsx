"use client";

import { useEffect, useMemo, useState } from "react";
import { BattleScreen } from "./BattleScreen";
import { MockBattleProvider, createFormatFixture } from "@/lib/battle/fixture";
import { LiveBattleProvider } from "@/lib/battle/liveProvider";

type Mode = "live" | "mock";
type Format = 1 | 2 | 3;

function readConfiguration(): { mode: Mode; format: Format } {
  if (typeof window === "undefined") return { mode: "live", format: 1 };
  const query = new URLSearchParams(window.location.search);
  const mode = query.get("provider") === "mock" ? "mock" : "live";
  const requested = Number(query.get("format"));
  return { mode, format: requested === 2 || requested === 3 ? requested : 1 };
}

export function BattleExperience() {
  const [config, setConfig] = useState<{ mode: Mode; format: Format } | null>(null);
  useEffect(() => {
    const timer = window.setTimeout(() => setConfig(readConfiguration()), 0);
    return () => window.clearTimeout(timer);
  }, []);
  const provider = useMemo(
    () => !config ? null : config.mode === "live" ? new LiveBattleProvider() : new MockBattleProvider(createFormatFixture(config.format)),
    [config],
  );

  if (!config || !provider) return <main className="loading-screen"><span className="loading-rune">◇</span>Preparing battle interface…</main>;
  return (
    <>
      {process.env.NODE_ENV !== "production" && (
        <nav className="dev-toolbar" aria-label="Battle development preview">
          <span>DEV PREVIEW</span>
          <a href="?provider=live&format=1" aria-current={config.mode === "live" ? "page" : undefined}>Live 1v1</a>
          {[1, 2, 3].map((size) => <a key={size} href={`?provider=mock&format=${size}`} aria-current={config.mode === "mock" && config.format === size ? "page" : undefined}>{size}v{size}</a>)}
        </nav>
      )}
      <BattleScreen provider={provider} mode={config.mode} />
    </>
  );
}
