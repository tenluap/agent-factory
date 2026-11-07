# Changelog

## 1.5.0 — 2026-11-07

- Moved to `core/skills/design-to-code/` as a first-party factory skill again (ADR 0012, ADR 0018): the vendored library is now `.agents/skills/`, managed by the `skills` CLI and `skills-lock.json`, which cannot own first-party skills. The renderer copies it verbatim into `dist/<harness>/skills/` and installation links it from there. `pen-design` moved alongside it. No behaviour change.

## 1.4.0 — 2026-11-01

- Moved back to `skills/design-to-code/` as a vendored library skill with a `SOURCES.md` provenance row: installation links it from this checkout into every harness's skills root under the same frontmatter name, replacing the rendered links from `dist/<harness>/skills/` on the next install. `pen-design` moved alongside it. No behaviour change.

## 1.3.0 — 2026-10-31

- Moved to `core/skills/design-to-code/` as a first-party factory skill (ADR 0012): the renderer copies it verbatim into `dist/<harness>/skills/` and installation links it from there into every harness's skills root. `pen-design` moved alongside it. No behaviour change.

## 1.2.1 — 2026-10-31

- `commands.launch` is one runnable shell command from the project root, no annotations (implement-html run 3 recorded `python3 -m http.server 8000 --bind 127.0.0.1 (run from project root)`, which the verifier cannot start).
- HTML/JS/CSS framework: the `__design/` capture harness stays while the map's recorded capture command references it — deleting it made the recorded gate unreproducible (implement-html run 4). Deploy exclusion still asked in the grouped question; deletion only when capture no longer depends on it and deployment would publish it with no ignore list.
- `map.commands.capture` keeps the `<id>`/`<dir>`/`<scale>`/`<theme>` placeholders — run 6 recorded resolved values, so the verifier's `<dir>` substitution missed and the fresh capture reused the agent's stale output.
- Implement mode must persist the working capture command into `map.commands.capture` (and `commands.launch` when a server is needed) before the visual gate passes — resume and independent verification re-run it as recorded (observed in implement-html eval run 2: gate passed in-run but the map had no command, so the grader could not reproduce it).
- `web-capture.mjs` resolves the project's Playwright from cwd upward, so a nested test package (`tests/visual/node_modules`) works when the recorded capture command runs from the project root (observed in implement-html eval run 1).
- Report contract tightened: the status line is exactly `Status: complete|partial|blocked` in plain text — markdown emphasis breaks graders and factory parsers (observed in qa-html eval run 2).

## 1.2.0 — 2026-10-31

- Role rename: `ui-designer` -> `design-to-code`; the standalone `ui-agent` skill alias is retired (plugins and harness skills now reference `design-to-code` directly). Dropped from the absorbed ui-agent skill with no replacement: CI/pre-commit hook recipes (the skill never commits unless asked), `auto` model-provider selection (config pins the critique model), and the example-output walkthrough.

- Smoke and dev servers bind to `127.0.0.1`; never fetch `.pen` or dotfiles through them (closes LAN exposure and a `.pen` deny bypass).
- QA scope also covers token, theme, config, locale, and markup-rendering JS/TS files.
- Undo snapshots track created files in `created.txt` and delete them on revert; snapshot paths get a fixed `YYYYMMDD-HHMMSS` run id; gates append to `run.log`.
- Timeouts also cover `impeccable context` and the QA critique subagent.
- Locked QA outside `implement` uses `maxIterations` and runs no capture.
- Agent permissions: destructive git and the remaining install commands ask first.
- `__design/` deploy exclusion goes through the grouped question.

## 1.1.0 — 2026-10-31

- Survey expands component instances (`resolveInstances`) and adds a `refs` section, so instance internals are mapped and bounds-checked.
- Pen schema corrections: stroke alignment `inner`/`center`/`outer`, `lineHeight` is a multiplier, shadows have no spread, gradient `rotation` is degrees counter-clockwise from up.
- Logged `design conflict` findings no longer block `complete`.
- Timeouts (300 s) for builds, captures, smoke checks, and `pen-read.py`; runs stop the servers and apps they start.
- QA critique subagent contract (read-only, fixed line format); skipped when already running as a subagent.
- File snapshots before each QA iteration and implement batch; undo never uses git.
- `.pen` guards moved to global `opencode.jsonc`; the agent adds approval prompts for local installs and scaffolds.
- Evals: `qa-locked` and `implement-html` added; 3-run protocol in `tests/evals/README.md`.

## 1.0.0 — 2026-10-31

- `design-to-code` replaces the `pen-to-avalonia` agent and absorbs `ui-agent` as `qa` mode. Frameworks: Avalonia, MAUI, Blazor, React, Next.js, HTML/JS/CSS.
