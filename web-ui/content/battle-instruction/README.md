# Battle Instruction editorial content

Edit `manual.yaml` to change player-facing chapter titles and prose. Mechanical
tables, formation diagrams, and numeric rules remain in the Battle Instruction
component and must be verified against the Python engine before they change.

After editing, run `npm run content:build` from `web-ui`, then restart the
development server if it is already running. `npm run content:check` validates
the schema and confirms the generated TypeScript module is current.
