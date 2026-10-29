# Data Model: UI Designer Role

Design context (existing file, optional fields added; no schema version):

- `source_kind`: `pen | figma | image | text`
- `framework`: `avalonia | web` (unsupported stops at plan)
- `scope`: `{ "kind": "file", "target": "<path>" }` or `{ "kind": "surface", "accepted_files": [...], "excluded": [...] }`
- `ui_agent_pass`: `null | { "at", "applied", "skipped", "deferred" }`
- `gates`: existing build/runtime, mapping, fidelity; text-only marks mapping/fidelity `not_applicable` with reason "no design reference"

Task: `[UI]` marker on UI design tasks; batch order tokens/assets, shared components, views.

State transitions (role): discover → survey → plan components/map → implement batches → validate → report.

Evidence files (Pen/Figma/image) live under `<spec_dir>/factory/design/`; `factory drop` moves the folder to `docs/design/<branch>/` and rewrites map references (existing behaviour, FR-030).
