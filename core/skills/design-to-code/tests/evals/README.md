# design-to-code behavioral evals

| Eval | Mode | Needs | Re-run after editing |
|---|---|---|---|
| [`qa-html`](qa-html/README.md) | `qa`, free | Python | `SKILL.md`, `modes/qa.md`, `references/web-css.md`, `frameworks/html-js-css.md` |
| [`qa-locked`](qa-locked/README.md) | `qa`, fidelity-locked | Python | same as `qa-html`, plus `references/map-schema.md` |
| [`implement-html`](implement-html/README.md) | `implement` | pen CLI 0.3.14 logged in, Playwright + Chromium or Google Chrome | `SKILL.md`, `modes/implement.md`, `sources/pen.md`, `references/*`, `frameworks/html-js-css.md`, any helper |
| `qa-react` (planned) | `qa`, free | Node | `frameworks/react.md`, `references/web-css.md` |
| `qa-blocked` (planned) | `qa` | none | `modes/qa.md`; grader: missing impeccable yields `Status: blocked` |
| `trajectory` (planned) | both | as source eval | any mode file; grader: no `git checkout/reset/stash` in the transcript, started servers stopped, budgets respected |

## Protocol

1. Copy the eval's `fixture/` to a fresh temp directory (the eval README gives any extra setup).
2. Run the eval prompt in a fresh agent session, cwd at that directory. Give it no hint about the seeded defects.
3. Grade with the eval's `check.py <dir>`.
4. Run each affected eval 3 times per behavior change. PASS needs 3/3.
5. Log every run in the eval's Results table with date, skill `version`, model, and notes.
6. Turn each observed failure into a new seeded defect in `fixture/` plus a check in `check.py`, so it cannot regress silently.

`(planned)` evals do not exist yet; add them before editing the file in their "Re-run after" column. Frameworks without an eval: Avalonia, MAUI, Blazor, React, Next.js. Exit paths without one: `blocked`, `partial`.

`scripts/tests/test_helpers.py` verifies that each untouched fixture still fails its graders as expected.
