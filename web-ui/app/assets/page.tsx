import Link from "next/link";
import { AssetImage } from "@/components/battle/AssetImage";
import { effectRegistry, heroPresentation, resolveAsset, skillPresentation, statusRegistry, type AssetKind } from "@/lib/battle/assets";

const heroes = [
  { id: "hero.warrior.weapon_master", name: "Ragnar", className: "Warrior" },
  { id: "hero.rogue.comprehensiveness", name: "Nighthawk", className: "Rogue" },
];
const heroKinds: AssetKind[] = ["portrait", "figure", "thumbnail", "class"];

function AssetFacts({ kind, id, name, className }: { kind: AssetKind; id: string; name: string; className?: string }) {
  const asset = resolveAsset({ kind, key: id, name, className });
  return <dl className="asset-facts">
    <div><dt>ID</dt><dd>{id}</dd></div><div><dt>Category</dt><dd>{kind}</dd></div>
    <div><dt>Resolved path</dt><dd>{asset.resolvedPath ?? "CSS / initials"}</dd></div>
    <div><dt>Fallback</dt><dd>{asset.fallback}</dd></div><div><dt>Status</dt><dd>{asset.status}</dd></div>
    <div><dt>Association</dt><dd>{asset.association}</dd></div>
  </dl>;
}

export default function AssetsPage() {
  return (
    <main className="gallery-shell">
      <header><div><p>DEVELOPMENT ROUTE</p><h1>Battle Asset Registry</h1><span>Stable IDs, resolved paths, fallback tiers, and production readiness.</span></div><Link href="/">← Return to battle</Link></header>
      <section><h2>Reference hero asset sets</h2><div className="gallery-grid heroes">{heroes.flatMap((hero) => heroKinds.map((kind) =>
        <article key={`${hero.id}.${kind}`}><AssetImage request={{ kind, key: hero.id, name: hero.name, className: hero.className }} /><strong>{hero.name} · {kind}</strong><AssetFacts kind={kind} id={hero.id} name={hero.name} className={hero.className} /><small>{heroPresentation[hero.id].placeholder ? "Placeholder-ready internal asset set" : "Final artwork"}</small></article>,
      ))}</div></section>
      <section><h2>Skill presentation registry</h2><div className="gallery-grid">{Object.entries(skillPresentation).map(([id, visual]) => <article className={`glyph-card ${visual.tone}`} key={id}><span>{visual.glyph}</span><strong>{id.split(".").at(-1)?.replaceAll("_", " ")}</strong><AssetFacts kind="skill" id={id} name={id} /><small>{visual.description ?? `${visual.effect} presentation cue`} · {visual.targetStyle ?? "Provider target rules"}</small></article>)}</div></section>
      <section><h2>Status registry</h2><div className="gallery-grid">{Object.entries(statusRegistry).map(([id, status]) => <article className={`glyph-card ${status.harmful ? "red" : "blue"}`} key={id}><span>{status.glyph}</span><strong>{status.name}</strong><AssetFacts kind="status" id={id} name={status.name} /><small>{status.description}</small></article>)}</div></section>
      <section><h2>Effect language</h2><div className="effect-gallery">{Object.keys(effectRegistry).map((effect) => <article className={`effect-swatch ${effect}`} key={effect}><span /><strong>{effect}</strong><small>ID effect.{effect}<br />CSS fallback · placeholder</small></article>)}</div></section>
    </main>
  );
}
