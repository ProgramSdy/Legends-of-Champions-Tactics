\# Image Creation Rule

\#\# 1\. Purpose

This document defines the default technical and visual production rules for game image resources created with ChatGPT Images or other image-generation tools.

These rules are intentionally content-independent. Individual image requests will define the specific subject, character, environment, pose, effect, mood, and narrative content.

When an image-specific request conflicts with this document, the image-specific request takes priority only for the explicitly overridden points. All other rules remain in effect.

\#\# 2\. Scope

This standard applies to:

\- battle-scene backgrounds;  
\- hero portraits;  
\- hero full figures and battle figures;  
\- hero avatars;  
\- faction artwork;  
\- skill icons and skill-card images;  
\- status icons and status overlays;  
\- combat and magic effects;  
\- UI decorations, frames, badges, and placeholders;  
\- stage-selection maps;  
\- stage-location artwork;  
\- stage-selection effects and overlays;  
\- other future game image resources.

\#\# 3\. Global Production Principles

\#\#\# 3.1 Master-first workflow

\- Generate a high-resolution master image first.  
\- Create smaller runtime variants by downscaling the master.  
\- Do not generate tiny final-use assets directly unless there is a specific reason.  
\- Preserve the original master file before cropping, resizing, compressing, or converting.

\#\#\# 3.2 Readability before detail

\- Every image must remain understandable at its intended display size.  
\- Use one clear focal point unless the image type specifically requires multiple subjects.  
\- Avoid decorative detail that disappears when scaled down.  
\- Prefer strong silhouettes, value contrast, and clear shape language over excessive texture.

\#\#\# 3.3 No embedded text

\- Do not generate names, labels, numbers, UI text, logos, signatures, or watermarks inside images unless specifically requested.  
\- Text should be added later by the web UI or game interface.

\#\#\# 3.4 Safe composition

\- Keep important content away from the outer edge.  
\- Do not crop heads, hands, feet, weapons, spell effects, or other essential objects unless the image category explicitly requires a close crop.  
\- Leave safe space for UI overlays when the image will be used behind interface elements.

\#\#\# 3.5 Consistency

\- Assets belonging to the same category should use the same aspect ratio, framing logic, scale, lighting discipline, and level of detail.  
\- Related image groups should be generated from a shared prompt template and reference set where possible.

\#\# 4\. File Formats

\#\#\# 4.1 Source masters

Preferred formats:

\- PNG for transparent or lossless masters;  
\- high-quality PNG for icons and isolated characters;  
\- high-quality JPG only for large opaque backgrounds when file size becomes significant.

\#\#\# 4.2 Runtime delivery

Preferred formats:

\- WebP for most web UI runtime assets;  
\- PNG where alpha transparency, crisp edges, or lossless quality is important;  
\- JPG only for large opaque images where transparency is not required and compression artefacts remain acceptable.

\#\#\# 4.3 Transparency

Use a true alpha channel for hero figures, isolated avatars, skill icons where the UI provides the frame, status icons, combat effects, UI decorations, frames, badges, and overlays.

Do not use transparency for full battle-scene backgrounds, environmental paintings intended to fill the viewport, or artwork that includes its own complete background.

\#\# 5\. Colour and Technical Settings

\- Colour space: sRGB.  
\- Standard channel depth: 8-bit per channel.  
\- Avoid CMYK assets for game use.  
\- Avoid unnecessary HDR unless the rendering pipeline specifically supports it.  
\- Check transparent edges for dark or light halos.  
\- Avoid excessive sharpening, noise, banding, or compression artefacts.  
\- Preserve shadow detail so dark areas remain readable on common screens.

\#\# 6\. Asset Category Specifications

\#\#\# 6.1 Battle-scene background

Purpose: a complete battlefield environment displayed behind heroes, effects, and combat UI.

Default specification:

\- Aspect ratio: 16:9.  
\- Master resolution: 3840 x 2160\.  
\- Minimum working resolution: 1920 x 1080\.  
\- Runtime target: normally 1920 x 1080 or responsive WebP variants.  
\- Background: fully opaque.  
\- Orientation: landscape.

Composition rules:

\- Reserve the primary combat area through the centre and lower-middle portion of the frame.  
\- Keep important scenery from interfering with hero silhouettes.  
\- Use foreground, middle ground, and background layers to create depth.  
\- Do not include UI, text, health bars, markers, or permanent combatants.  
\- Avoid placing the strongest visual focal point directly behind expected hero positions.  
\- Keep essential content within the central 80% of width and height.  
\- Treat the outer 10% on each side as potentially cropped on responsive layouts.

\#\#\# 6.2 Battle foreground

\- Aspect ratio: match the battle background.  
\- Master resolution: 3840 x 2160\.  
\- Transparency: required.  
\- Format: PNG master, PNG or WebP runtime.  
\- Keep the centre sufficiently open for heroes and combat effects.  
\- Ensure all transparent edges are clean.

\#\#\# 6.3 Battle overlay

\- Aspect ratio: match the battle viewport.  
\- Master resolution: 3840 x 2160\.  
\- Transparency: required.  
\- Suitable for fog, dust, rain, smoke, light rays, or damage-state overlays.  
\- Use low visual density and avoid hiding gameplay information.

\#\#\# 6.4 Hero portrait

\- Aspect ratio: 3:4.  
\- Master resolution: 1536 x 2048\.  
\- Alternative large master: 2304 x 3072\.  
\- Transparency: optional.  
\- Framing: head-and-shoulders or waist-up, defined by the specific request.  
\- Face and eyes must remain clear at reduced size.  
\- Leave at least 8% margin around the head and major accessories.  
\- Avoid busy backgrounds that compete with facial readability.

\#\#\# 6.5 Hero full figure or battle figure

\- Aspect ratio: 2:3.  
\- Master resolution: 2048 x 3072\.  
\- Minimum working resolution: 1365 x 2048\.  
\- Transparency: required.  
\- Framing: full body.  
\- Show the complete head, body, hands, feet, clothing, and primary weapon.  
\- Maintain clear separation between limbs, body, weapon, cape, wings, and accessories.  
\- Keep at least 8% transparent margin on all sides.  
\- Avoid extreme perspective distortion unless specifically requested.

\#\#\# 6.6 Hero avatar

\- Aspect ratio: 1:1.  
\- Master resolution: 1024 x 1024\.  
\- Runtime targets: 256 x 256, 128 x 128, and 64 x 64\.  
\- Transparency: optional.  
\- Framing: face or head-and-shoulders.  
\- Test inside both square and circular masks.  
\- Keep identity-defining features clear at 64 x 64\.

\#\#\# 6.7 Faction image

\- Emblem: 1:1 at 1024 x 1024 with transparency.  
\- Banner: 3:1 at 2048 x 683\.  
\- Panel artwork: 16:9 or 4:3 according to the target UI.  
\- Use a simple, recognisable central symbol for emblems.  
\- Keep text outside the generated image.

\#\#\# 6.8 Skill icon

\- Aspect ratio: 1:1.  
\- Master resolution: 1024 x 1024\.  
\- Runtime targets: 256 x 256, 128 x 128, and 64 x 64\.  
\- Transparency: preferred when the UI provides the frame.  
\- Use one dominant subject or action.  
\- The icon must remain recognisable at 64 x 64\.  
\- Use bold shapes, strong contrast, and a simple silhouette.  
\- Avoid tiny characters, distant environments, and competing effects.  
\- Keep the central subject away from the outer 12%.  
\- Do not bake borders, rarity frames, cooldown numbers, or labels into the image.

\#\#\# 6.9 Skill-card image

\- Aspect ratio: 4:3 or 3:4 depending on UI layout.  
\- Landscape master: 2048 x 1536\.  
\- Portrait master: 1536 x 2048\.  
\- Transparency: normally no.  
\- May contain a wider action or narrative moment but must retain one clear focal point.  
\- Do not assume the card border is part of the artwork.

\#\#\# 6.10 Status icon

\- Aspect ratio: 1:1.  
\- Master resolution: 512 x 512\.  
\- Preferred high-quality master: 1024 x 1024 when derived independently.  
\- Runtime targets: 64 x 64 and 32 x 32\.  
\- Transparency: required or strongly preferred.  
\- Complexity: lower than a skill icon.  
\- Use one simple symbol or effect.  
\- The icon must remain understandable at 32 x 32\.  
\- Do not merely resize a complex skill icon without checking readability.  
\- A skill image may be the source reference, but the status version should normally be simplified and recropped.  
\- Do not bake duration numbers, stacks, borders, or labels into the image.

\#\#\# 6.11 Status overlay

\- Canvas size: match the target asset or viewport.  
\- Transparency: required.  
\- Visual density: low to medium.  
\- Do not obscure hero identity or health information.  
\- Keep the effect compatible with variable opacity.

\#\#\# 6.12 Combat or magic effect

\- Default aspect ratio: 1:1.  
\- Square master: 2048 x 2048\.  
\- Horizontal effect: 2048 x 1024\.  
\- Vertical effect: 1024 x 2048\.  
\- Transparency: required.  
\- Keep the centre and direction of travel obvious.  
\- Ensure the effect remains separable from the hero figure.  
\- Test visibility on both dark and light backgrounds.

\#\#\# 6.13 UI frame, panel, badge, and decoration

\- Master size: at least 2x intended display size.  
\- Transparency: usually required.  
\- Do not include labels or dynamic values.  
\- Keep centre areas clear when content will be placed inside.  
\- Prefer nine-slice-compatible construction for scalable panels where appropriate.  
\- Avoid unnecessary texture behind small text.

\#\#\# 6.14 Placeholder image

\- Match the target category's aspect ratio.  
\- Use a neutral style that is clearly temporary.  
\- Do not imitate final art quality.  
\- Do not contain user-facing text unless specifically required.

\#\#\# 6.15 Stage-selection map

Purpose: a large environmental scene used as the visual foundation of a stage-selection screen. Individual stage locations, interactive markers, labels, buttons, lock states, completion indicators, and other UI may later be layered over this artwork.

Default specification:

\- Aspect ratio: 16:9.  
\- Master resolution: 3840 x 2160\.  
\- Minimum working resolution: 1920 x 1080\.  
\- Runtime target: normally 1920 x 1080 or responsive WebP variants.  
\- Background: fully opaque.  
\- Orientation: landscape.  
\- Style and rendering quality should remain consistent with the game's established environment artwork.

Composition rules:

\- Design the environment as a coherent geographic space rather than a decorative fantasy landscape.  
\- The scene should support multiple visually distinct stage-location zones.  
\- Each intended stage zone must have enough surrounding negative space and visual separation for a future stage landmark to remain readable.  
\- Terrain should naturally explain why different types of locations could exist there.  
\- Use geography such as valleys, mountains, plateaus, forests, rivers, cliffs, roads, ruins, elevated ground, passes, and similar environmental structures to divide the map naturally.  
\- Avoid artificial-looking empty circles or obvious placeholder areas.  
\- Stage zones should appear to belong to the same continuous world.  
\- Avoid making every zone equally prominent. Visual hierarchy may be used to imply progression, distance, danger, or importance.  
\- Roads, paths, rivers, bridges, mountain passes, walls, or other environmental features may subtly communicate relationships between stage locations.  
\- Do not bake explicit navigation arrows or UI connectors into the environmental artwork unless specifically requested.  
\- Preserve foreground, middle-ground, and background depth.  
\- The environment must remain visually readable when displayed behind interactive UI.  
\- Avoid excessive micro-detail in areas intended to receive stage landmarks or UI overlays.  
\- Avoid strong environmental focal points that would compete with future interactive stage locations.  
\- Keep essential geography and intended stage zones within the central 80% of the canvas.  
\- Treat approximately the outer 10% on every side as a responsive crop-risk area.  
\- Do not place essential stage zones exclusively inside crop-risk areas.  
\- The composition should remain understandable under moderate responsive cropping.  
\- Do not include permanent hero characters unless explicitly requested.  
\- Do not include stage names, UI text, buttons, stars, lock symbols, progression numbers, selection borders, health bars, or other dynamic interface information.  
\- Lighting should provide one coherent environmental atmosphere while allowing future stage landmarks to use controlled local lighting or colour accents.  
\- The base terrain should generally use lower visual contrast than important interactive stage landmarks that will later be placed over it.  
\- Preserve sufficient tonal separation so stage landmarks remain identifiable at normal gameplay display size.

Layering principle:

The stage-selection screen should conceptually support separate layers:

1\. Base stage-selection map/environment.  
2\. Individual stage-location artwork or landmarks.  
3\. Optional environmental effects or overlays.  
4\. Interactive stage-state effects.  
5\. UI markers, labels, progression information, buttons, and other interface elements.

Do not permanently merge dynamic UI information into the base environment.

\#\#\# 6.16 Stage-location artwork

Purpose: an individual visual landmark representing a selectable stage or destination placed onto a stage-selection map.

Examples of this category may include structures, fortresses, towers, temples, camps, forests, ruins, caves, portals, settlements, or other identifiable destinations.

Default principles:

\- Stage-location artwork should normally be created as an independent asset so it can be positioned, selected, highlighted, locked, animated, replaced, or updated without regenerating the entire stage-selection map.  
\- Transparency is preferred when the location is intended to be composited onto an existing stage-selection map.  
\- Use a true alpha channel when transparency is required.  
\- Do not use fake checkerboard transparency.  
\- Do not include unrelated background scenery when the location is intended as an isolated composited landmark.  
\- Maintain clean transparent edges.  
\- Lighting direction, atmospheric perspective, viewing angle, horizon relationship, and colour temperature must be compatible with the intended stage-selection map.  
\- The landmark must visually belong to the terrain on which it will be placed.  
\- Avoid perspective that conflicts with the base map.  
\- The landmark should have a strong and recognisable silhouette.  
\- The location must remain identifiable when displayed at its actual runtime size.  
\- Use one dominant architectural/environmental identity per stage.  
\- Avoid excessive tiny decorative details that disappear after downscaling.  
\- Leave sufficient transparent margin around the landmark for selection glows, hover effects, outlines, or other runtime effects.  
\- Do not bake stage names, stage numbers, lock icons, completion stars, difficulty labels, selection borders, or other dynamic UI information into the artwork.  
\- Stage-specific colour accents are allowed, but they must remain compatible with the shared environmental lighting.  
\- Related stage locations belonging to the same map should share compatible perspective, rendering quality, material treatment, lighting discipline, and scale logic.  
\- Stage locations should feel visually distinct from one another without appearing to originate from unrelated games or art styles.

Integration rule:

When a stage-location asset is intended for a specific base map, design the base map and stage-location asset as one visual system.

Check:

\- intended placement;  
\- viewing angle;  
\- approximate scale;  
\- terrain contact;  
\- lighting direction;  
\- atmospheric depth;  
\- silhouette readability;  
\- surrounding negative space;  
\- responsive crop safety;  
\- UI overlap;  
\- visual hierarchy.

The final composite should look like the landmark was originally constructed within the environment rather than pasted onto the background.

\#\#\# 6.17 Stage-selection effects and states

Selection, hover, lock, completion, progression, accessibility, or availability states should normally be implemented separately from the base stage artwork.

Possible separate effects include:

\- selection glow;  
\- outline;  
\- subtle illumination;  
\- atmospheric highlight;  
\- particle accent;  
\- locked-state treatment;  
\- completed-state treatment;  
\- active-path treatment.

These effects must not require permanent modification of the source stage-selection map unless specifically requested.

Keep effects restrained enough that multiple stage locations can coexist without making the map visually noisy.

\#\# 7\. Cropping and Responsive Variants

\- Preserve one uncropped master.  
\- Create category-specific crops from the master rather than repeatedly editing previous crops.  
\- Prepare desktop-wide and narrower background crops when required.  
\- Never stretch an image to a different aspect ratio.  
\- Use crop, padding, or art-directed variants instead.  
\- Recheck faces, weapons, and focal points after every crop.

\#\# 8\. Downscaling and Export

\- Use high-quality downscaling.  
\- Apply minimal sharpening only after resizing when required.  
\- Inspect icons at actual display sizes, especially 64 x 64 and 32 x 32\.  
\- Inspect transparent edges against both dark and light backgrounds.  
\- Compare compressed runtime files with the master before approval.  
\- Never overwrite the source master with a compressed runtime version.

\#\# 9\. Naming Convention

Use lowercase snake\_case for filenames.

General pattern:

\`\<category\>\_\<subject\>\_\<variant\>\_v\<two-digit-version\>.\<extension\>\`

Examples:

\- \`battle\_ruined\_arena\_day\_v01.png\`  
\- \`hero\_warrior\_portrait\_v01.png\`  
\- \`hero\_warrior\_full\_v01.png\`  
\- \`hero\_warrior\_avatar\_v01.png\`  
\- \`skill\_shield\_throw\_icon\_v01.png\`  
\- \`status\_bleeding\_icon\_v01.png\`  
\- \`effect\_holy\_burst\_v01.png\`  
\- \`ui\_portrait\_frame\_common\_v01.png\`

Rules:

\- Use descriptive English words.  
\- Do not use spaces.  
\- Do not use final, final2, new, latest, or similar ambiguous labels.  
\- Use a two-digit version number starting at \`v01\`.  
\- Keep canonical game-data names consistent once defined.

\#\# 10\. Versioning

\- Increment the version when visual content changes materially.  
\- Do not increment for simple file-format conversion or runtime resizing.  
\- Preserve approved masters.  
\- Mark deprecated files outside the runtime asset path rather than deleting them immediately.  
\- Avoid overwriting a previously approved version unless correcting a purely technical defect.

\#\# 11\. Prompt-writing Rules

Every future image request should include only content-specific information not already defined here.

A prompt should normally specify:

\- image category;  
\- subject;  
\- action or pose;  
\- environment, if applicable;  
\- mood;  
\- required content-specific colours or effects;  
\- approved reference assets;  
\- any explicit exception to this standard.

Do not repeatedly restate default resolution, aspect ratio, transparency, or composition rules unless overriding them.

Before generation, confirm which category specification applies. After generation, verify the result against both the specific request and this document.

\#\# 12\. AI Generation Constraints

\- Prefer one primary subject per icon.  
\- Avoid readable text inside artwork.  
\- Avoid relying on very small expressions or props to communicate meaning.  
\- Keep anatomy, hands, weapons, equipment, and repeated costume details consistent across related hero images.  
\- Use approved reference images whenever consistency matters.  
\- For image edits, preserve identity-defining features unless the request explicitly changes them.  
\- Generate related asset groups in a controlled sequence rather than as unrelated one-off prompts.  
\- Inspect and correct AI-generated transparent edges.  
\- Review every asset at its intended runtime size before approval.

\#\# 13\. Consistency Matrix

| Asset type | Default ratio | Master resolution | Transparency | Small-size test | Detail level |  
|---|---:|---:|---|---:|---|  
| Battle background | 16:9 | 3840 x 2160 | No | 1920 x 1080 | Very high |  
| Battle foreground | 16:9 | 3840 x 2160 | Yes | 1920 x 1080 | High |  
| Battle overlay | 16:9 | 3840 x 2160 | Yes | 1920 x 1080 | Medium |  
| Hero portrait | 3:4 | 1536 x 2048 | Optional | 256 px wide | Very high |  
| Hero full figure | 2:3 | 2048 x 3072 | Yes | 512 px high | Very high |  
| Hero avatar | 1:1 | 1024 x 1024 | Optional | 64 x 64 | High |  
| Faction emblem | 1:1 | 1024 x 1024 | Yes | 64 x 64 | Medium |  
| Skill icon | 1:1 | 1024 x 1024 | Preferred | 64 x 64 | High |  
| Skill-card image | 4:3 or 3:4 | 2048 x 1536 or 1536 x 2048 | Usually no | 512 px wide | Very high |  
| Status icon | 1:1 | 512 x 512 | Preferred | 32 x 32 | Medium |  
| Status overlay | Target-dependent | Match target | Yes | Target-dependent | Low to medium |  
| Combat effect | 1:1 default | 2048 x 2048 | Yes | 256 x 256 | High |  
| UI decoration | Target-dependent | At least 2x display size | Usually yes | Actual display size | Medium |
| Stage-selection map | 16:9 | 3840 x 2160 | No | 1920 x 1080 | Very high |  
| Stage-location artwork | Target-dependent | At least 2x intended display size | Usually yes | Actual display size | High |

\#\# 14\. Approval Checklist

Before an asset is approved, verify:

\- correct category and aspect ratio;  
\- correct master resolution;  
\- correct transparency requirement;  
\- clear focal point;  
\- no unwanted text, logo, signature, or watermark;  
\- no important object is accidentally cropped;  
\- clean transparent edges where required;  
\- readable at intended display size;  
\- suitable contrast against the expected UI or battlefield;  
\- consistent appearance with related approved assets;  
\- intended stage zones remain readable, where applicable;  
\- important stage zones are outside responsive crop-risk areas, where applicable;  
\- future landmarks have sufficient visual and negative space, where applicable;  
\- base terrain does not overpower interactive locations, where applicable;  
\- stage landmarks match the base map's perspective and lighting, where applicable;  
\- stage names and dynamic stage-state UI are not baked into artwork, where applicable;  
\- isolated stage-location assets have clean alpha edges where applicable;  
\- correct filename and version;  
\- source master preserved;  
\- runtime export visually matches the master.

\#\# 15\. Future Revision Rule

Update this document when repeated production experience reveals a better technical standard. Revisions must remain content-independent and must not define individual heroes, skills, environments, or story elements.  
