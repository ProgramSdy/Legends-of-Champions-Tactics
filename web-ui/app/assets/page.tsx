import Link from "next/link";
import { AssetImage } from "@/components/battle/AssetImage";
import { skillPresentation, statusRegistry } from "@/lib/battle/assets";

const heroes = ["Arthas", "Black Heart", "Flesh Puppet", "Sashein", "Andonidas"];
const classes = ["Necromancer", "Warlock", "Warrior", "Mage"];

export default function AssetsPage() {
  return (
    <main className="gallery-shell">
      <header><div><p>DEVELOPMENT ROUTE</p><h1>Battle Asset Registry</h1><span>Stage 1 placeholders are explicitly marked and exercise every fallback tier.</span></div><Link href="/">← Return to battle</Link></header>
      <section><h2>Hero portraits & battlefield figures</h2><div className="gallery-grid heroes">{heroes.map((name) => <article key={name}><AssetImage request={{ kind: "portrait", key: name.toLowerCase().replaceAll(" ", "."), name }} /><strong>{name}</strong><small>Class-specific fallback or readable initials</small></article>)}</div></section>
      <section><h2>Class icons · repository assets</h2><div className="gallery-grid">{classes.map((name) => <article key={name}><AssetImage request={{ kind: "class", key: name, name }} /><strong>{name}</strong><small>Existing repository icon</small></article>)}</div></section>
      <section><h2>Skill presentation registry</h2><div className="gallery-grid">{Object.entries(skillPresentation).map(([id, visual]) => <article className={`glyph-card ${visual.tone}`} key={id}><span>{visual.glyph}</span><strong>{id.split(".").at(-1)?.replaceAll("_", " ")}</strong><small>Original typographic placeholder</small></article>)}</div></section>
      <section><h2>Status registry</h2><div className="gallery-grid">{Object.entries(statusRegistry).map(([id, status]) => <article className={`glyph-card ${status.harmful ? "red" : "blue"}`} key={id}><span>{status.glyph}</span><strong>{status.name}</strong><small>{status.description}</small></article>)}</div></section>
      <section><h2>Effect language</h2><div className="effect-gallery">{["magic", "healing", "melee", "status", "summon"].map((effect) => <article className={`effect-swatch ${effect}`} key={effect}><span /><strong>{effect}</strong><small>CSS presentation fallback</small></article>)}</div></section>
    </main>
  );
}
