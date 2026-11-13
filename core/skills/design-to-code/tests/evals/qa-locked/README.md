# Eval: qa-locked

Behavioral eval for `design-to-code` `qa` mode, fidelity-locked form. `fixture/` is the `qa-html` page plus `docs/design-code-map.json`, which maps `index.html` and `styles.css` to a design. The design governs colors, so the 2.32:1 muted text is a design value.

Expected: the agent fixes the two non-visual defects (button accessible name, image `alt`), keeps `.muted` at `#aaaaaa`, and logs the contrast failure as a `design conflict`. The report still ends `Status: complete`, because logged design conflicts do not block.

## Run

1. `T=$(mktemp -d) && cp -R fixture/. "$T"/`
2. Fresh agent session, cwd `$T`, prompt:

   > I just edited index.html and styles.css in this directory. Load the design-to-code skill and run qa mode on them. Write your final report to qa-report.md in this directory.

3. Grade: `python3 -I ../qa-html/check.py "$T" --locked`.

## Results

| Date | Version | Model | Result | Notes |
|---|---|---|---|---|
| 2026-10-31 | 1.2.1 | GLM-5.3-Flash (coding-specialist subagent) | PASS, 1 iteration | 2 non-visual fixes applied; contrast kept and logged as design conflict (2.3:1, escalated with suggested value). |
| 2026-10-31 | 1.2.1 | GLM-5.3-Flash (coding-specialist subagent) | PASS, 1 iteration | 2 applied, 3 design conflicts logged (contrast critical + spacing + hover). |
| 2026-10-31 | 1.2.1 | GLM-5.3-Flash (coding-specialist subagent) | PASS, 1 iteration | 4 applied, 1 design conflict (contrast, escalated). |
