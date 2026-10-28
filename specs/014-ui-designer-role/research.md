# Research: UI Designer Role

- Decision: route by explicit `[UI]` task marker. Rationale: deterministic, no new route. Alternatives: infer from file type (fragile).
- Decision: framework detection in spec-builder at plan; role re-verifies. Rationale: stop unsupported runs before tasks. Alternatives: detect only at implement (late failure).
- Decision: reuse `design-code-mapping-avalonia.md`, add one web reference. Rationale: FR-010, YAGNI. Alternatives: per-framework web files (premature).
- Decision: extend existing `PARTIAL_RETURN_ROLES` and budget table. Rationale: single source of truth (ENG-6). Alternatives: separate list (duplication).
- Decision: `ui-agent` single pass, flag in design context. Rationale: FR-024 resume safety. Alternatives: ledger lookup (indirect).
