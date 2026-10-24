# Remediation — pass 4

Source report: `factory/analyze-4.md` (CRITICAL 0 · HIGH 0 · MEDIUM 1 · LOW 2). All three findings fixed
in place; none needed a user decision, so `pending_clarify` is empty.

| ID | Severity | Status | What changed |
|----|----------|--------|--------------|
| D1 | LOW | fixed | `tasks.md` T012: the drifting line number is gone. `(`README.md:71`, the "SpecKit set up" bullet)` is now `(the "SpecKit set up for your harness" bullet)`, which quotes the bullet's own text (`README.md:72`) and cannot go stale. The quoted ZCode sentence T012 adds is unchanged. |
| D2 | MEDIUM | fixed | The instruction no longer re-adds a command that is already on `DESIGN.md:69`. `tasks.md` T013 now reads: the line "already reads `specify init --here <harness.speckit_init>`; delete only the Claude-shaped parenthetical `(--ai <harness>, plus --ai-skills outside Claude Code ...)`, leaving a neutral gloss: each adapter states its own `speckit_init` arguments (ZCode's: …)". Aligned the two places that justified the edit: `plan.md` Constitution Check → I. Design First (the line "loses its Claude-shaped parenthetical …, leaving the generalised `specify init --here <harness.speckit_init>` already on that line") and `plan.md` R4 → FR-011 ("loses its `--ai`/`--ai-skills` gloss"), plus `research.md` R4's Note (`DESIGN.md:69` "already carries the generalised …; this feature deletes that parenthetical and keeps the generalised command"). `spec.md` FR-016 is outcome-worded ("MUST be generalised to state that each adapter declares its own setup arguments") and stays true of the resulting line, so it was left alone. |
| D3 | LOW | fixed | `tasks.md` T012: the dictated README row is now backticked like the existing rows — `` | ZCode | `./install.sh --harness zcode` | `/factory <feature>` | `~/.zcode/agents/factory-*.md` | `` — with "(backticked like `README.md:9-12`)" naming the pattern. `<feature>` is inside backticks, so it cannot be read as an HTML tag. |

## Word budgets

Trimmed `tasks.md` while editing so it stays inside its 2500-word budget (it had 7 words of headroom and
the D1/D3 wording is longer): removed the duplicate `(research R4)` after T012's quoted command (R4 is
still cited in the following sentence), shortened "after the existing requirement line" to "after the
requirement line", and replaced "Note, as research R4 does, that the other harnesses' recorded form is out
of scope here (FR-016)" with "The other harnesses' recorded form is out of scope (FR-016, research R4)".
No requirement, task, seam, exemption or citation was dropped.

`wc -w` after remediation: `spec.md` 2508/3000 · `plan.md` 1872/2000 · `tasks.md` 2497/2500.

## Deferred to clarify

None.
