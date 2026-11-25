"use client";

import {
  useId,
  useLayoutEffect,
  useRef,
  useState,
  type ReactNode,
  type RefObject,
} from "react";
import { createPortal } from "react-dom";

const VIEWPORT_MARGIN = 8;
const ANCHOR_GAP = 8;

export function ViewportBoundOverlay({
  anchorRef,
  children,
  className,
  id,
  role,
}: {
  anchorRef: RefObject<HTMLElement | null>;
  children: ReactNode;
  className?: string;
  id?: string;
  role?: "tooltip" | "status";
}) {
  const generatedId = useId();
  const overlayRef = useRef<HTMLDivElement>(null);
  const [position, setPosition] = useState<{ left: number; top: number } | null>(null);

  useLayoutEffect(() => {
    const anchor = anchorRef.current;
    const overlay = overlayRef.current;
    if (!anchor || !overlay) return;

    const place = () => {
      const anchorRect = anchor.getBoundingClientRect();
      const overlayRect = overlay.getBoundingClientRect();
      const maxLeft = Math.max(VIEWPORT_MARGIN, window.innerWidth - overlayRect.width - VIEWPORT_MARGIN);
      const left = Math.max(
        VIEWPORT_MARGIN,
        Math.min(anchorRect.left + anchorRect.width / 2 - overlayRect.width / 2, maxLeft),
      );
      const above = anchorRect.top - overlayRect.height - ANCHOR_GAP;
      const below = anchorRect.bottom + ANCHOR_GAP;
      const maxTop = Math.max(VIEWPORT_MARGIN, window.innerHeight - overlayRect.height - VIEWPORT_MARGIN);
      const top = above >= VIEWPORT_MARGIN
        ? above
        : below + overlayRect.height <= window.innerHeight - VIEWPORT_MARGIN
          ? below
          : Math.max(VIEWPORT_MARGIN, Math.min(above, maxTop));
      setPosition((current) => current
        && Math.abs(current.left - left) < 0.5
        && Math.abs(current.top - top) < 0.5
        ? current
        : { left, top });
    };

    place();
    let animationFrame = 0;
    const trackAnchor = () => {
      place();
      animationFrame = window.requestAnimationFrame(trackAnchor);
    };
    animationFrame = window.requestAnimationFrame(trackAnchor);
    const resizeObserver = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(place);
    resizeObserver?.observe(anchor);
    resizeObserver?.observe(overlay);
    window.addEventListener("resize", place);
    window.addEventListener("scroll", place, true);
    return () => {
      window.cancelAnimationFrame(animationFrame);
      resizeObserver?.disconnect();
      window.removeEventListener("resize", place);
      window.removeEventListener("scroll", place, true);
    };
  }, [anchorRef]);

  if (typeof document === "undefined") return null;
  return createPortal(
    <div
      ref={overlayRef}
      id={id ?? generatedId}
      role={role}
      className={`viewport-bound-overlay${className ? ` ${className}` : ""}`}
      style={position ? { left: position.left, top: position.top } : undefined}
      data-positioned={position ? "true" : "false"}
    >
      {children}
    </div>,
    document.body,
  );
}
