# Eval: implement-html

Behavioral eval for `design-to-code` `implement` mode on plain HTML/JS/CSS.

`fixture/design/cards.pen` (built by `build-design.txt` with `pen interactive --out`) holds:

- Frame `Screen` (`dqvK9`): 360×224, vertical layout, padding 24, gap 16, fill `$surface`.
- Component `Card` (`wYD2U`): 312×80, horizontal layout, padding 16, gap 12, centered, white, radius 12, outer shadow 0/4/12 `#0000001F`. Children: `Swatch` 48×48 `$primary` radius 8; `Bar` fill-width × 12 `#D1D5DB` radius 6.
- Two instances in `Screen`; `Card 2` overrides `Bar` fill to `#9CA3AF`.
- Tokens: `primary` `#1A56DB`, `surface` `#F3F4F6`. No text, so no font prerequisites.

`expected/rows.txt` and `expected/dqvK9.png` are the survey and the scale-2 reference, produced with `sources/pen.md` commands.

## Run

1. `T=$(mktemp -d) && cp -R fixture/. "$T"/ && ln -s "$(npm root -g)/@playwright/cli/node_modules" "$T/tests/visual/node_modules"` (any directory whose `node_modules` holds `playwright` works).
2. Fresh agent session, cwd `$T`, prompt:

   > Implement frame dqvK9 ("Screen") from design/cards.pen in this plain HTML/CSS project, light theme, scale 2. Playwright is available in tests/visual. You may scaffold the design harness. Write your final report to report.md in this directory.

3. Grade: `python3 -I check.py "$T"`. The grader re-runs `commands.launch` and `commands.capture` from the agent's map itself, then runs `bounds-diff.py` (7 nodes) and `pixel-diff.py` (0.5%) against `expected`.

## Results

| Date | Version | Model | Result | Notes |
|---|---|---|---|---|
| 2026-10-31 | 1.2.1 | GLM-5.3-Flash (coding-specialist subagent) | FAIL (capture) | All in-run gates passed but the map recorded no `commands.capture`, so the grader could not reproduce the capture. Fixed in v1.2.1: persist the exact command into the map before the gate passes; helper also now resolves Playwright from cwd upward. |
| 2026-10-31 | 1.2.1 | GLM-5.3-Flash (coding-specialist subagent) | FAIL (capture) | `commands.launch` recorded as `python3 -m http.server 8000 --bind 127.0.0.1 (run from project root)` — annotation broke the verifier. Fixed: launch is one runnable command, no annotations. Grader also hardened against `killpg` PermissionError. |
| 2026-10-31 | 1.2.1 | GLM-5.3-Flash (coding-specialist subagent) | FAIL (capture) | Agent followed the old framework rule and deleted `__design/` at run end, which the recorded capture command references. Fixed: harness stays while `commands.capture` references it. |
| 2026-10-31 | 1.2.1 | GLM-5.3-Flash (coding-specialist subagent) | FAIL (capture) | `commands.capture` recorded with resolved values instead of `<id>`/`<dir>`/`<scale>`/`<theme>` placeholders, so the verifier's substitution missed. Fixed: placeholders intact, never resolved. |
| 2026-10-31 | 1.2.1 | GLM-5.3-Flash (coding-specialist subagent) | PASS | 7/7 bounds, 0.01% pixels, capture reproduced by the grader from the map. |
| 2026-10-31 | 1.2.1 | GLM-5.3-Flash (coding-specialist subagent) | PASS | Same, fresh run. |
| 2026-10-31 | 1.2.1 | GLM-5.3-Flash (coding-specialist subagent) | PASS | Same, fresh run; anchor-path repair loop converged in-run. |
