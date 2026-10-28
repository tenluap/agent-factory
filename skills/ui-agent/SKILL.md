---
name: ui-agent
description: Use when UI files are altered (.tsx, .jsx, .vue, .svelte, .razor, .cshtml, .html, .css, .scss, .less, .xaml, .axaml, .qml), design tokens or theme config change, or user-visible copy is modified — and the user wants a fixed critique→audit→typeset→polish→re-verify pipeline with a configurable model provider, capped at two iterations
---

# UI Agent

Automated UI quality assurance through a fixed critique-and-fix pipeline. When any UI surface is altered, this skill delegates analysis to a configurable model provider, then runs a `/impeccable critique` → `/impeccable audit` → `/impeccable typeset` → `/impeccable polish` → re-verify sequence, capped at two critique-and-fix iterations per change set.

**REQUIRED BACKGROUND:** You MUST understand superpowers:impeccable and superpowers:design-critique-pipeline. This skill complements the pipeline by adding the full audit→typeset→polish→re-verify sequence, escalation for remaining high/critical findings, and model-provider swappability that the pipeline lacks.

## When to Use

- Any UI surface file was edited (component, stylesheet, template, markup, or partial rendered to a screen)
- Design tokens, theme config, or Tailwind config changed
- User-visible copy, labels, error messages, empty states, or i18n strings were modified
- A pre-commit hook or CI step needs to validate UI quality automatically
- The user explicitly invokes `/ui-quality-agent` or `/ui-agent [target]`

**Do NOT use for:**
- Backend code, API logic, or non-UI files
- One-shot UI reviews (use `/impeccable critique` directly)
- New feature design work (use `/impeccable shape` or `/design-critique-pipeline`)

## Configuration

All behavior is externalized. Load the configuration file first:

```
~/.agents/skills/ui-agent/ui-agent.config.json
```

```json
{
  "modelProvider": "qwencloud",
  "modelName": "auto",
  "maxIterations": 2,
  "skillBaseDir": "~/.agents/skills/impeccable",
  "buildCommand": ""
}
```

| Key | Default | Description |
|-----|---------|-------------|
| `modelProvider` | `qwencloud` | Provider for UI analysis. Swap to `openai`, `anthropic`, or any installed provider skill. |
| `modelName` | `auto` | Model name. `auto` delegates to `qwencloud-model-selector` for optimal UI model selection. |
| `maxIterations` | `2` | Hard cap on critique→fix iterations per change set. |
| `skillBaseDir` | `~/.agents/skills/impeccable` | Path to the impeccable skill for context.mjs. |
| `buildCommand` | `""` | Project-specific build/verify command; run during the re-verify step. If empty, skip build verification. |

## The UI Change Critique Loop

### Trigger

Any edit to:
- Component/view files (`.tsx`, `.jsx`, `.vue`, `.razor`, `.cshtml`, `.html`, `.svelte`, `.xaml`, `.axaml`)
- Templates, markup, or partials rendered to a screen
- Stylesheets (`.css`, `.scss`, `.less`) or utility-class markup
- Design tokens, theme, or Tailwind config
- Layout, spacing, typography, colour, or motion
- User-visible copy, labels, error messages, empty states, or i18n strings

### Per-Iteration Steps

**Before declaring the task complete, execute these steps in order:**

1. **Invoke `/impeccable critique`** on the changed UI. Pass the changed files and the user-facing intent.
2. **List every returned recommendation** with its priority (usability > hierarchy > safety > accessibility > cosmetic).
3. **Implement each one** that is actionable in scope and does not contradict an explicit user constraint.
4. **Run `/impeccable audit`** on the updated UI to catch issues that survive the first pass.
5. **Run `/impeccable typeset`** to validate hierarchy, typography, spacing, and reading rhythm.
6. **Run `/impeccable polish`** to finalise the visual consistency and quality pass.
7. **Re-verify**: re-read the edited files, confirm each implemented item is present, and confirm the change still builds or renders via the project's existing command (if `buildCommand` is configured).
8. **Report** which recommendations were applied and which were deferred, one line of justification per deferred item.

### Iteration Flow

```
iteration = 0

while iteration < maxIterations:
    iteration++

    Execute per-iteration steps 1-8 (above).

    If no high or critical findings remain:
        EXIT — report done

    If iteration < maxIterations:
        Continue to next iteration

    If iteration == maxIterations AND high/critical findings remain:
        STOP — escalate to user
        List remaining high/critical findings with one-line descriptions
```

### Escalation Rules

After `maxIterations` (default: 2), if **high or critical** findings remain:
- **Stop** — do not loop further.
- **List** each remaining high/critical finding.
- **Escalate** to the user with context: "X findings remain after Y iterations. These need human judgment."

Low-priority or cosmetic findings remaining after the cap are **not** escalated — they are deferred and reported as "deferred (iteration cap reached)."

### Never

- Declare a UI task complete without at least one `/impeccable critique`
- Surface recommendations without acting on the actionable ones
- Expand scope beyond the changed surface
- Loop more than `maxIterations` times
- Skip audit, typeset, or polish — each step catches different categories of issues

## Step-by-Step Workflow

### 1. Detect Changed UI Files

Identify the target files from the user's request, the current git diff, or the provided path. Filter to only UI-surface files.

```bash
git diff --name-only HEAD | grep -E '\.(tsx|jsx|vue|svelte|razor|cshtml|html|css|scss|less|xaml|axaml|qml)$'
```

### 2. Load Configuration

Read `~/.agents/skills/ui-agent/ui-agent.config.json`. Fall back to defaults for any missing keys.

### 3. Resolve Model Provider

If `modelName` is `auto`, invoke `qwencloud-model-selector` to pick the best model for UI tasks. If `modelProvider` is not `qwencloud`, skip model selection and use the configured provider directly.

### 4. Initialize Impeccable Context

Run the impeccable context script once per session:

```bash
node <skillBaseDir>/scripts/context.mjs --target <files>
```

Follow its directives. Do not rerun it within the same session.

### 5. Execute the Critique Loop

Follow the iteration flow above. Each iteration runs the full pipeline: critique → audit → typeset → polish → re-verify.

### 6. Report Results

After the loop exits, report:
- Number of iterations executed
- Total recommendations found vs. applied vs. deferred
- One line of justification per deferred item
- High/critical findings escalated to the user (if iteration cap reached)
- Confirmation that the build or render verification passed (if `buildCommand` was configured)

## Gotchas

- **Always load the config file first.** Model provider, iteration cap, and build command must come from config, not hardcoded assumptions.
- **Never skip context.mjs.** Impeccable's context script loads PRODUCT.md, DESIGN.md, and surface briefs — without it, critique recommendations lack project context.
- **Stop at maxIterations.** Escalate remaining high/critical issues; do not loop further.
- **Don't add scope.** Fix the requested design surface; do not invent new features or workflows.
- **Treat copy as UI.** Labels, helper text, errors, and empty states are in scope for critique.
- **Keep the config visible** during the whole workflow. If the model provider or iteration cap changes between runs, the behavior should reflect it.
- **This skill complements `/design-critique-pipeline`**, it does not replace it. Use the pipeline for design-time refinement; use this skill for post-edit quality assurance with the full audit→typeset→polish→re-verify sequence.

## Integration Hooks

### Git Pre-Commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit
CHANGED_UI_FILES=$(git diff --cached --name-only | grep -E '\.(tsx|jsx|vue|svelte|razor|cshtml|html|css|scss|less|xaml|axaml|qml)$')
if [ -n "$CHANGED_UI_FILES" ]; then
    echo "Running UI quality agent on changed files..."
    /ui-quality-agent $CHANGED_UI_FILES
    if [ $? -ne 0 ]; then
        echo "UI quality check failed. Fix issues before committing."
        exit 1
    fi
fi
```

### Impeccable Hook Chain

```bash
# Enable impeccable's design detector
$impeccable hooks on

# The UI agent can be chained as a post-hook:
# After impeccable detects UI changes, it invokes this agent for the critique loop
```

### CI Pipeline (GitHub Actions)

```yaml
- name: UI Quality Check
  run: |
    CHANGED_UI=$(git diff --name-only origin/main...HEAD | grep -E '\.(tsx|jsx|vue|svelte|razor|cshtml|html|css|scss|less|xaml)$' || true)
    if [ -n "$CHANGED_UI" ]; then
      /ui-quality-agent $CHANGED_UI
    fi
```

## Example Usage

```
/ui-agent src/OmniRoute.App/Pages/Dashboard.razor
```

**Expected output:**

```
UI Quality Agent — config: qwencloud/auto, max iterations: 2

[1/2] Running /impeccable critique on Dashboard.razor...
  Found 12 recommendations:
    [HIGH] Colour contrast on primary CTA is 3.2:1 (WCAG AA requires 4.5:1)
    [MED] Missing aria-label on 3 icon buttons
    [MED] font-display: swap not set on custom font
    [LOW] Inconsistent spacing in card grid (16px vs 24px)
    ... 8 more

[1/2] Implementing 10 actionable fixes...
  ✓ Fixed: colour contrast on primary button (3.2:1 → 5.8:1)
  ✓ Fixed: added aria-labels to icon buttons
  ✓ Fixed: font-display: swap on custom font
  ... 7 more fixes applied
  ✗ Deferred: 2 recommendations (out of scope — require backend API changes)

[1/2] Running /impeccable audit...
  ✓ Accessibility: passed
  ✓ Responsive: 1 minor issue fixed

[1/2] Running /impeccable typeset...
  ✓ Heading hierarchy: h1→h2→h3 correct
  ✓ Line-height: adjusted body text from 1.3 to 1.5

[1/2] Running /impeccable polish...
  ✓ Visual consistency: 3 adjustments applied

[1/2] Re-verify: re-read files, all fixes confirmed. Build verified with `dotnet build`.

[2/2] Running /impeccable critique...
  Found 3 recommendations:
    [HIGH] Primary CTA still uses non-semantic <div> — needs <button> for keyboard access
    [LOW] Mobile card padding is 12px, desktop is 16px — inconsistent
    [LOW] Empty state illustration missing alt text

[2/2] Implementing 2 actionable fixes...
  ✓ Fixed: replaced <div> with <button> element
  ✓ Fixed: added alt text to empty state illustration
  ✗ Deferred: mobile padding inconsistency (out of scope — requires design system decision)

[2/2] Running /impeccable audit/typeset/polish...
  ✓ All checks passed

[2/2] Re-verify: confirmed. Build passes.

Done. 2 iterations, 12 fixes applied, 3 deferred.
Deferred:
  - 2 recommendations require backend API changes (out of scope)
  - Mobile padding inconsistency requires design system decision (out of scope)
No high/critical findings escalated.
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Config file not found | Create `~/.agents/skills/ui-agent/ui-agent.config.json` with defaults from this document |
| Model provider not available | Fall back to the default agent; skip the model-provider delegation step |
| context.mjs fails | Ensure `skillBaseDir` points to a valid impeccable installation; run `$impeccable doctor` |
| Critique recommends broad product changes | Reject out-of-scope items; only apply design-quality fixes tied to the changed files |
| Build verification fails after fixes | Revert the last iteration's fixes one by one to isolate the breaking change; report to user |
| Max iterations reached with high/critical findings | Escalate to user with full list; do not loop further |

