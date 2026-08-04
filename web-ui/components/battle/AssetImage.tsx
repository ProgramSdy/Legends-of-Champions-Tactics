"use client";

import { useState } from "react";
import Image from "next/image";
import { initials, resolveAsset, type AssetRequest } from "@/lib/battle/assets";

type AssetImageProps =
  | { request: AssetRequest; className?: string; src?: never; name?: never; onImageDimensions?: (dimensions: { naturalWidth: number; naturalHeight: number } | null) => void }
  | { request?: never; className?: string; src: string | null; name: string; onImageDimensions?: (dimensions: { naturalWidth: number; naturalHeight: number } | null) => void };

export function AssetImage(props: AssetImageProps) {
  const [failed, setFailed] = useState(false);
  const request = props.request ?? { kind: "portrait" as const, key: props.name, name: props.name };
  const registered = resolveAsset(request);
  const direct = "src" in props ? { src: props.src, fallback: "initials" as const, label: `${props.name} placeholder artwork` } : registered;
  const asset = failed ? { ...direct, src: null, label: `${request.name} placeholder artwork` } : direct;
  const src = asset.src;
  if (!src || failed) {
    return <span className={`asset-fallback fallback-${asset.fallback} ${props.className ?? ""}`} role="img" aria-label={asset.label}>{initials(request.name)}<small>{asset.fallback === "class" ? "CLASS PLACEHOLDER" : "PLACEHOLDER"}</small></span>;
  }
  return <Image className={`${props.className ?? ""} fallback-${asset.fallback}`} src={src} alt="" aria-label={asset.label} width={160} height={160} unoptimized={src.startsWith("/game-images/")}
    onLoad={(event) => props.onImageDimensions?.({ naturalWidth: event.currentTarget.naturalWidth, naturalHeight: event.currentTarget.naturalHeight })}
    onError={() => { setFailed(true); props.onImageDimensions?.(null); }} />;
}
