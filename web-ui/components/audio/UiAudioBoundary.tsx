"use client";

import type { ReactNode } from "react";
import { useUiAudioFeedback, type UiAudioManager } from "@/lib/audio/uiAudio";

export function UiAudioBoundary({ children, manager }: { children: ReactNode; manager?: UiAudioManager }) {
  const feedback = useUiAudioFeedback(manager);

  return (
    <div data-ui-audio-root="true" style={{ display: "contents" }} {...feedback}>
      {children}
    </div>
  );
}
