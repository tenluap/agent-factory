# Protected test-scope confirmation (Q3, requires_user, not auto)

Persisted verbatim by the orchestrator. Shown to the user and answered 2026-10-29 (timeline wait 2, `fix` stage).

## Question shown

Q3 — Confirm the complete test scope, exactly as it now stands?

Q2 only recorded acceptance of the two added failure paths; this confirmation names the whole scope.

1. `PARTIAL_RETURN_ROLES` in `factory_cli.state`: `ui-designer` is accepted as a file-writing role returning `partial` with an overrun. Failure path: a `partial` from a non-file-writing role is still rejected.
2. `render.py <harness>` agent output: every harness renders `factory-ui-designer` with standard tier and write access, and the core role file names no harness tool. Failure path: none.
3. `factory drop` design rehome: Figma and image evidence in `factory/design/` moves to `docs/design/<branch>/`, with map references rewritten. Failure paths: a missing evidence file, a `../` traversal reference, and a symlink inside `factory/design/` pointing outside it. In each failure case the reference is reported, the map is unchanged, and `factory/` is not moved.

Everything else is exempt: documentation, prompt text, and `dist/`.

Options: A · Accept this exact scope (suggested) · B · Something else (add, remove or change seams or failure paths).

## Answer

`Q3: accept` → option A, accepted by the user (not auto). Recorded in `state.json` decisions (stage `fix`, question `Q3`).
