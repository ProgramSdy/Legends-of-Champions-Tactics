# Legends of Champions Tactics — EGF Funding and Strategic Game Design Meeting Notes

**Date:** 2026-08-06  
**Topic:** Emerging Gamemakers Fund readiness, project status, strategic combat identity, and funding direction  
**Project:** Legends of Champions Tactics

## 1. Meeting Purpose

The purpose of this discussion was to reassess the current development status of *Legends of Champions Tactics*, review suitable near-term funding options, examine the Screen Australia Emerging Gamemakers Fund (EGF), and clarify the game's strongest creative and strategic differentiators for a future funding application.

A key decision was made not to rush the August 2026 EGF round. The project will instead prepare for the next round, expected to open in December 2026 and close in February 2027. This gives the project time to improve the MVP, gather stronger evidence, refine the creative proposition, and prepare a realistic funding plan without disrupting the developer's limited part-time schedule.

## 2. Current Project Status

The project has moved away from the previous Godot-first UI direction. The current active architecture is:

- Python remains the authoritative combat engine.
- The player-facing client is a Next.js Web UI.
- A thin Python adapter/API connects the Web UI to the engine.
- The frontend consumes authoritative snapshots, legal actions, commands, and semantic battle events rather than reimplementing combat rules.
- The current Web UI includes a Team Builder and battle experience, and the Python adapter/API is runnable in the active development environment.
- The project is best described as an early-stage playable Web tactical RPG prototype with a substantial battle engine, rather than a polished public vertical slice.

The existing engine is technically substantial. It already supports eight hero faculties, multiple specialisations, skills, buffs, debuffs, resistances, control effects, summons, AI, agility-based turn ordering, and 1v1/2v2/3v3 battle structures.

## 3. Development Stage and EGF Positioning

The current project should be positioned as **pre-production / early playable prototype**, not as a completed production-stage game.

The core combat technology is already proven, but the player-facing experience remains early in areas such as:

- visual polish;
- player readability;
- hero presentation;
- skill VFX and audio;
- onboarding;
- accessibility;
- external playtesting;
- audience validation;
- public-facing build quality.

This creates a credible EGF story: the project does not need funding simply to prove that a combat engine can be built. Instead, funding would help convert an already functioning technical prototype into a focused, player-testable, visually coherent prototype that can validate the game's strategic identity.

## 4. EGF Application Direction

### 4.1 Timing Decision

The project will **not** rush the August 2026 EGF round.

Target:

- Next EGF round: expected opening December 2026.
- Expected closing date: February 2027.

This timing better suits the project's part-time development model and avoids diverting several weeks away from core development for a rushed application.

### 4.2 Main EGF Materials Required

The EGF application is expected to require:

- a pitch video of up to approximately three minutes;
- a Creative Pitch Deck using the official template;
- a Project Plan using the official template, with a limited page count;
- CVs for relevant team members participating during the grant period;
- budget, milestone, and schedule information within the application;
- clear responses to assessment areas such as creative merit, viability, impact, inclusion, accessibility, and project outcomes;
- evidence of relevant rights and IP ownership / chain of title.

Additional requirements may apply if the project incorporates First Nations stories, characters, communities, cultural material, or related consultation needs.

### 4.3 Material Already Available

The project already has strong source material for the application:

- substantial GDD documentation;
- detailed combat system documentation;
- hero and skill system documentation;
- current project overview and onboarding documentation;
- active development history in `docs/Codex/Completed.md`;
- current Web UI architecture documentation;
- Python adapter/API documentation;
- a functioning combat engine;
- working Web UI combat flows;
- existing screenshots and gameplay that can be captured for a pitch video;
- a development roadmap and clear technical architecture.

This means the main application challenge is not a lack of project substance. The challenge is to compress the existing technical and design depth into a clear, persuasive application that a reviewer can understand quickly.

### 4.4 Materials Still Needing Significant Work

The main work items are:

- EGF-specific Creative Pitch Deck;
- EGF-specific Project Plan;
- realistic grant milestone definition;
- detailed budget based on actual hours, contractor rates, and deliverables;
- three-minute pitch video;
- audience definition and market positioning;
- external validation / playtest evidence;
- accessibility strategy;
- formal IP / chain-of-title check;
- concise explanation of the game's originality and creative experimentation.

The most time-consuming items are expected to be the budget, pitch video, final milestone design, audience validation, and the articulation of the game's distinctive creative identity.

## 5. Funding Strategy

The project owner is developing part-time and generally has only a limited daily development window. Therefore, high-pressure funding models that demand rapid full-time delivery are not a natural fit at this stage.

The preferred funding philosophy is:

- avoid premature publisher or investor pressure;
- avoid rushing crowdfunding before a stronger public-facing prototype exists;
- use government grants as acceleration capital rather than as the only source of survival funding;
- later consider small recurring community support, founder/supporter memberships, or other low-pressure revenue streams;
- consider Early Access only when the game has enough stable content and polish to justify direct player payment.

The ideal funding structure in the medium term is a combination of:

1. **Government grant funding** for a defined milestone;
2. **small recurring community support** for ongoing development;
3. **eventual game / Early Access sales** once the product is ready.

Grant money should ideally purchase work that is difficult for the solo/part-time developer to produce efficiently, especially:

- character art;
- skill icons;
- VFX;
- sound effects;
- music;
- UI polish;
- accessibility improvements;
- QA and external playtesting;
- marketing / presentation assets.

## 6. Game Type and EGF Fit

The game is a dark-fantasy, turn-based tactical hero-combat RPG. There is no requirement for the game to use an Australian setting or theme. The project therefore does not need to artificially add Australian imagery or narrative material purely for grant eligibility.

The current genre is compatible with EGF. The more important question is not whether turn-based tactical combat is new, but whether the project has a distinct creative proposition within that genre.

The project should avoid presenting itself as a derivative version of an existing released title. Visual references such as *Ruined King* may remain internal benchmarking references, but the EGF application should articulate the game's own design identity rather than pitch it as “X but with Y”.

## 7. Strategic Combat Design Philosophy

A major part of the discussion focused on the original combat design philosophy.

### 7.1 Strategy Exists Before and During Battle

The game's strategy operates across two connected layers:

**Pre-battle strategy**

- team composition;
- faculty and specialisation selection;
- role coverage;
- synergy planning;
- counter-planning;
- resistance and status considerations.

**In-battle tactical execution**

- target selection;
- skill timing;
- cooldown management;
- status setup and exploitation;
- control timing;
- dispel timing;
- prediction of opponent actions;
- adaptation when the original plan is disrupted.

A useful internal description is:

> The battle is won twice: first when building the team, and again through how that team is piloted.

This is not claimed as a completely new genre mechanic, but it is a core pillar of the intended experience.

## 8. Interlocking Status System

The project's status system is one of its most important strategic differentiators.

The design goal is not simply:

> Skill -> damage -> HP reduction.

Instead, skills can establish layered conditions that persist, interact, spread, modify statistics, change resistances, alter turn order, affect later skills, create windows of opportunity, or enable counters.

Examples identified from the status system include mechanics such as:

- poison with stacking behaviour;
- damage-over-time effects;
- agility reduction that changes turn economy;
- bleed-linked conditional effects;
- disease / plague propagation;
- target selection influenced by existing states;
- state interactions that cross between allied and enemy targets;
- damage and agility boosts with self-damage trade-offs;
- defence reduction combined with damage-over-time;
- elemental / shadow resistance manipulation;
- healing amplification or suppression;
- full damage immunity windows;
- anti-magic immunity;
- evasion modifications;
- hard-control effects such as fear, paralysis, freeze / glacier-style states;
- summon duration and summon-linked states.

The key concept is that **status effects are not passive decorations; they are strategic tools that alter the evolving battle state**.

A strong internal working term is:

> **Interlocking Battle States**

or

> **Layered Status Warfare**

A possible future pitch formulation is:

> *Legends of Champions Tactics explores tactical combat where status effects are not passive modifiers but interconnected strategic tools. Players build combinations across heroes, manipulate resistances and turn order, spread or exploit conditions, and time counters against evolving battle states.*

## 9. Battle-State Manipulation as a Signature Design Direction

The player is not only managing HP. The player may be simultaneously considering:

- current HP;
- damage and defence;
- agility and initiative;
- resistances;
- poison, bleeding, disease, and other persistent conditions;
- buff and debuff duration;
- immunity;
- evasion;
- healing modifiers;
- control states;
- summon lifecycle;
- cooldowns;
- casting states;
- the opponent's likely next action.

This means a strong skill may not be the one with the largest immediate damage value. A control effect, resistance reduction, setup state, dispel, or delayed combination can have more strategic value depending on the current battle state.

This provides a basis for a future signature mechanic / signature design proposition, but the project should validate this through actual playtesting rather than merely claiming it in marketing copy.

## 10. Strategic Equality — Hero Design Philosophy

A second major design principle was clarified during the meeting.

Unlike many hero-collection or long-running service games, *Legends of Champions Tactics* is not intended to create a hierarchy of “strong” and “trash” heroes.

The intended principle is:

> **Every hero is designed to remain strategically viable.**

The value of a hero should come primarily from:

- composition;
- synergy;
- counter relationships;
- battlefield state;
- timing;
- player knowledge;
- player decision-making.

The game should avoid deliberate power creep where new heroes replace older heroes simply because their numbers are larger.

Instead:

> **New heroes expand the possibility space rather than replacing existing heroes.**

New heroes should create new combinations, counters, and interactions. Ideally, a newly introduced hero can even make an older hero newly relevant by creating a new synergy or counter relationship.

An internal name for this philosophy is:

> **Strategic Equality**

Three supporting pillars were identified:

### Every Hero Matters

Every hero should have a durable strategic purpose and remain potentially viable as the roster grows.

### States Create Strategy

Statuses should create tactical relationships, timing windows, combinations, and counters rather than merely add or subtract numbers.

### Mastery Beats Power

The game should reward understanding, planning, prediction, adaptation, and execution more than the ownership of inherently stronger characters.

A concise design statement is:

> **Power comes from relationships and decisions rather than inherently stronger heroes.**

Another useful phrase is:

> **Mastery comes from understanding relationships, not acquiring stronger pieces.**

## 11. Go-Like Design Analogy

The project owner described the design philosophy as being closer to Go than to chess.

This is not meant to imply that the gameplay mechanics resemble Go. Instead, the analogy describes the intended value structure of the pieces:

- heroes should not belong to permanent “high-value” and “low-value” tiers;
- the usefulness of a hero should depend heavily on context and player use;
- expanding the roster should increase strategic combinations rather than invalidate existing pieces.

This analogy is useful internally, but the EGF application should avoid simply saying “the game is like Go”, as that could incorrectly suggest that the gameplay itself resembles Go.

## 12. Player Mastery

The meeting clarified that “player skill” in *Legends of Champions Tactics* should mean something specific rather than a vague claim.

Player mastery includes:

- **Roster Knowledge** — understanding what heroes and specialisations can do;
- **Composition Skill** — building teams with useful synergies and counters;
- **State Reading** — understanding the current battlefield condition;
- **Timing** — using important skills at the correct moment;
- **Prediction** — anticipating the opponent's likely action;
- **Adaptation** — changing strategy when the original plan fails;
- **Counterplay** — disrupting the opponent's setup or exploiting their weakness.

This supports the long-term vision of a game where superior decision-making matters more than simply possessing a higher-tier hero.

## 13. Future PvP Direction

PvP is part of the intended future direction but is **not currently implemented**.

The project must be precise in future funding applications and avoid claiming that PvP already exists.

A suitable framing is:

> The combat architecture and hero design are being developed with future player-versus-player tactical competition in mind.

PvP is relevant because it can amplify the existing design pillars:

- team composition becomes draft / counter-pick strategy;
- status application and cleansing become mind games;
- cooldown and important skills can be deliberately held to threaten future turns;
- players can bait counters or force premature defensive actions;
- roster knowledge and prediction become more important;
- the absence of intentional power creep becomes particularly valuable for competitive fairness.

Future PvP should therefore be treated as a natural extension of the current combat philosophy rather than as a separate feature added only for grant appeal.

## 14. Readability Risk

A strategic system can only become a player-facing strength if players can understand it.

A major risk identified is that a deep status system can become opaque. The project must therefore make state relationships legible through the Web UI.

The interface should help players quickly understand:

1. what a status does;
2. how long it remains active;
3. what other skills or statuses it is currently interacting with.

For example, if a condition empowers another condition or changes the behaviour of a later skill, that relationship should be visible rather than hidden only inside the Python engine.

This creates a strong potential EGF funding rationale: the core strategic systems already exist, but funding can help make that complexity readable, learnable, visually expressive, accessible, and externally testable.

## 15. Audience Direction

The likely core audience is not simply “RPG players”.

The project is better suited to players who enjoy:

- team building;
- theorycrafting;
- counters;
- skill synergy;
- status interaction;
- turn optimisation;
- competitive decision-making;
- tactical prediction;
- planning and adaptation.

A useful internal audience description is:

> Players who enjoy thinking about how to win, not only how to level up.

This audience definition should be researched and validated further before the EGF application.

## 16. Monetisation Implications

The Strategic Equality philosophy has direct consequences for future monetisation.

The game should avoid monetisation that depends on intentional power creep or the sale of increasingly stronger heroes.

More philosophically aligned options include:

- cosmetics;
- skins;
- visual effects;
- supporter / founder packs;
- expansion content;
- convenience features that do not damage competitive fairness;
- new heroes sold for variety, expression, or new strategic possibilities rather than superior power.

A potential product value statement is:

> **Spend for variety or expression, not power.**

This will require more detailed commercial design later and is not yet a final monetisation model.

## 17. Emerging Creative Identity for EGF

The meeting concluded that the game's originality should not be presented as any single mechanic being completely unprecedented.

Instead, the creative identity emerges from the interaction of several deliberately aligned systems:

- **Strategic Equality**;
- **team-composition-driven strategy**;
- **interlocking status effects**;
- **timing and battle-state manipulation**;
- **counterplay**;
- **specialisation-driven roster design**;
- **future competitive PvP**.

The current strongest high-level proposition is:

> **Power comes from relationships and decisions rather than inherently stronger heroes.**

This is supported by a second proposition:

> **New heroes expand the possibility space rather than replacing existing heroes.**

These principles should now be treated as hypotheses to be validated through real gameplay and external player testing before the EGF application.

## 18. Recommended Work Before the Next EGF Round

Between August 2026 and the next application round, development and funding preparation should reinforce each other rather than run as separate projects.

Recommended priorities:

1. Continue improving the playable MVP without rushing feature volume.
2. Make status interactions and battle-state changes highly readable in the Web UI.
3. Identify 5–8 real hero / status combinations that clearly demonstrate the game's design identity.
4. Capture strong screenshots and short gameplay clips as development progresses.
5. Begin small-scale external playtesting once the battle loop is sufficiently stable.
6. Record player feedback, especially around:
   - team composition;
   - skill timing;
   - status interactions;
   - perceived hero usefulness;
   - clarity of battle information;
   - moments of tactical reversal.
7. Test the “Strategic Equality” hypothesis by monitoring whether players perceive some heroes as obsolete or universally dominant.
8. Refine the target audience through actual player observation rather than assumption alone.
9. Define a realistic six-to-nine-month EGF milestone compatible with the developer's part-time capacity.
10. Build a transparent budget based on real hours and realistic contractor rates.
11. Prepare the Creative Pitch Deck and Project Plan only after the core proposition and milestone are sufficiently clear.
12. Produce the final pitch video closer to submission, using actual representative gameplay rather than placeholder claims.

## 19. Key Decisions

- Do not rush the August 2026 EGF application.
- Target the next EGF round.
- Continue positioning the project as pre-production / early playable prototype while that remains factually accurate.
- Do not add artificial features solely to appear innovative.
- Treat the interlocking status system as a major candidate for the project's signature strategic identity.
- Treat Strategic Equality as a foundational hero-design philosophy.
- Avoid intentional power creep.
- Design new heroes to expand combinations rather than replace existing heroes.
- Treat future PvP as a long-term extension of existing tactical principles, not as a currently completed feature.
- Use the coming months to collect evidence for the future EGF pitch through gameplay, playtesting, visual progress, and real player feedback.

## 20. Working Design Statements

The following statements are useful internal working language and may later inform the EGF pitch, GDD, website copy, or product positioning:

> **Every hero is designed to remain strategically viable.**

> **New heroes expand the possibility space rather than replacing existing heroes.**

> **Power comes from relationships and decisions rather than inherently stronger heroes.**

> **Mastery comes from understanding relationships, not acquiring stronger pieces.**

> **The battle is won twice: first when building the team, and again through how that team is piloted.**

> **Status effects are not passive modifiers; they are interconnected strategic tools.**

> **Spend for variety or expression, not power.**

These are working formulations rather than final marketing claims. They should be refined and validated through continued development and player testing.

---

**Next review point:** Reassess EGF readiness after further MVP improvement and initial external playtesting, with particular focus on creative differentiation, player readability, audience validation, realistic milestone scope, and budget design.
