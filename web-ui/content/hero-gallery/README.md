# Hero Gallery editorial content

Each approved hero has one YAML file in this folder. Edit these files when you
want to change a hero introduction, battle-style summary, skill introduction,
or an optional labelled strategy tip.

Use the stable `definitionId` and `skillId` values already present in the file.
Do not rename, add, or remove an ID unless the authoritative Python hero
catalogue changes at the same time. Damage, healing, cooldowns, classifications,
target rules, and other mechanical or numeric values do **not** belong here;
those values come from `GET /api/v1/heroes`.

Multiline copy uses YAML block syntax:

```yaml
introduction: |-
  The first line of copy.
  A second line when needed.
```

Optional tips are written under a skill:

```yaml
tips:
  - label: Strategy Tip
    text: |-
      A short player-facing suggestion, not a new combat rule.
```

Run `npm run content:build` from `web-ui` after editing. The normal
`npm run dev` and `npm run build` commands also compile the YAML before they
start, so restart the local development server to see an edit. Tests,
type-checking, and linting fail if the generated content is stale.

Validation rejects malformed YAML, duplicate/unknown/missing hero or skill IDs,
empty required copy, unknown fields, and mechanical fields. The generated
TypeScript module is build output; do not edit it directly. Mechanical metadata
refreshes never modify these YAML source files.
