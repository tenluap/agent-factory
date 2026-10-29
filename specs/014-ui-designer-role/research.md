# Research: UI Designer Role

- Decision: route by explicit `[UI]` task marker. Rationale: deterministic, no new route. Alternatives: infer from file type (fragile).
- Decision: framework detection in spec-builder at plan; role re-verifies. Rationale: stop unsupported runs before tasks. Alternatives: detect only at implement (late failure).
- Decision: reuse `design-code-mapping-avalonia.md`, add one web reference. Rationale: FR-010, YAGNI. Alternatives: per-framework web files (premature).
- Decision: extend existing `PARTIAL_RETURN_ROLES` only; budget lookup is role-generic (default 300 s), no change. Rationale: single source of truth (ENG-6). Alternatives: separate list (duplication).
- Decision: FR-030 drop rehome is a regression test; `factory drop` already moves the whole `factory/design/` folder and rewrites map refs. Code change only if the missing-evidence failure path is red. Alternatives: new rehome code (duplicate).
- Decision: no adapter edits; adapters do not enumerate roles, render discovers `core/roles/`.
- Decision: `ui-agent` single pass, flag in design context. Rationale: FR-024 resume safety. Alternatives: ledger lookup (indirect).
