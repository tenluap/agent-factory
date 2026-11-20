# Eval: qa-html

Behavioral eval for `design-to-code` `qa` mode, free form. Needs no pen login and no toolchain beyond Python.

`fixture` is a plain HTML page with three seeded accessibility defects:

1. Icon-only menu button with no accessible name.
2. Hero image with no `alt` attribute.
3. Muted paragraph text at 2.32:1 contrast (`#aaaaaa` on white).

## Run

1. Copy the fixture to a fresh directory: `T=$(mktemp -d) && cp -R fixture/. "$T"/`.
2. Start a fresh agent session with cwd `$T` and this prompt:

   > I just edited index.html and styles.css in this directory. Load the design-to-code skill and run qa mode on them. No design source applies. Write your final report to qa-report.md in this directory.

3. Grade: `python3 -I check.py "$T"`.

## Pass

`check.py` exits 0: all three defects fixed with their elements kept, `qa-report.md` contains `Status: complete`, and the report shows at most 2 iterations. Follow the protocol in [`../README.md`](../README.md) (3 runs, 3/3 to pass) and log each run below.

`scripts/tests/test_helpers.py` checks that the untouched fixture still fails exactly these three checks.

## Results

| Date | Version | Model | Result | Notes |
|---|---|---|---|---|
| 2026-10-31 | 1.2.0 | claude-opus-5-5 (coding-specialist subagent) | PASS, 1 iteration | 3/3 defects fixed; 3 extra polish fixes; 3 deferred. QwenCloud critique subagent unavailable (nested subagent depth limit), fell back to current agent as designed. |
| 2026-10-31 | 1.2.0 | claude-opus-5-5 (coding-specialist subagent) | PASS, 1 iteration | Run 2. 3/3 defects fixed (contrast 5.33:1); 3 extra polish fixes; 4 deferred. Critique subagents again blocked by depth limit; fallback used. |
| 2026-10-31 | 1.2.0 | GLM-5.3-Flash (coding-specialist subagent) | FAIL | Report wrote `Status: **complete**` (markdown emphasis); grader's literal substring missed it. Fixed in v1.2.1: status line is exactly `Status: <value>` plain text. |
| 2026-10-31 | 1.2.1 | GLM-5.3-Flash (coding-specialist subagent) | PASS, 1 iteration | 3/3 defects fixed (7.0:1), tokens.css extracted. |
| 2026-10-31 | 1.2.1 | GLM-5.3-Flash (coding-specialist subagent) | PASS, 1 iteration | 3/3 fixed (6.83:1); 5/5 findings applied. |
| 2026-10-31 | 1.2.1 | GLM-5.3-Flash (coding-specialist subagent) | PASS, 1 iteration | 3/3 fixed (7.0:1); 7 findings all applied. |
