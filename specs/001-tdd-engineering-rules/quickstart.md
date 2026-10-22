# Quickstart: validating the engineering discipline change

How to prove this change is correct. The change is documentation/configuration-exempt from test-first (see "Test seams" in [plan.md](./plan.md)), so validation is the repository's own build and test commands plus the inspection checks below, and then the end-to-end observation on the next real run.

## Prerequisites

- The worktree for `001-tdd-engineering-rules`, with the change applied.
- Python 3 (for `tools/render.py`). No test runner is needed or installed.
- Run every command from the worktree root.

## 1. Build: render every harness (SC-005)

```bash
for h in $(python3 tools/render.py --list); do python3 tools/render.py "$h" || exit 1; done
```

Expected: exit 0, no output. A failure here means a role file lost its frontmatter, or a role body contains `'''` and cannot be written into the Codex TOML agent.

## 2. Test: generated output matches its source (FR-023, SC-005)

```bash
git diff --exit-code -- dist/
```

Expected: exit 0. A non-empty diff means `dist/` was committed stale or hand-edited; re-render and commit the result with the source change. Never edit `dist/` by hand (constitution III).

## 3. The rules exist once (FR-001, SC-004)

```bash
ls core/skills/factory/references/engineering.md
grep -rlE 'ENG-[0-9]+' core/ | sort
grep -rnE 'ENG-[0-9]+' core/roles/ core/skills/factory/references/findings.md
```

Expected: the file exists; the first list is `core/skills/factory/references/engineering.md` plus only files whose `ENG-n` mentions are citation instructions or the severity ceiling; and every hit of the second command outside `engineering.md` either instructs a role to cite an id (for example "cite the `ENG-n` id in `evidence`") or states the severity a cited id may carry (the `ENG-7`..`ENG-10` ceiling in `findings.md`, FR-015f), rather than restating what a rule requires. Any line outside `engineering.md` that states a rule's content is a duplication and belongs in the reference (SC-004).

## 4. Every rule has a unique id (FR-004a, SC-004a)

```bash
grep -o 'ENG-[0-9]\+' core/skills/factory/references/engineering.md | sort -V | uniq -c
```

Expected: `ENG-1` through `ENG-11`, each appearing as a rule exactly once, with no gaps.

## 5. The six roles reference the file, and only those six (FR-004, FR-015c)

```bash
grep -l 'references/engineering.md' core/roles/*.md | sort
```

Expected exactly: `code-build.md`, `code-standards.md`, `fixer.md`, `review-judge.md`, `spec-builder.md`, `spec-conformance.md`. The security, UI and UX reviewers must not appear.

## 6. Every harness carries the rules (FR-023, US4)

```bash
for h in $(python3 tools/render.py --list); do
  diff -q core/skills/factory/references/engineering.md "dist/$h/skill/references/engineering.md" || echo "DRIFT: $h"
done
```

Expected: no output. Each harness's skill copy is byte-identical to the source.

## 7. The design document leads (FR-022, constitution I)

```bash
grep -n 'Engineering discipline' DESIGN.md
git log --oneline -- DESIGN.md core/ | head
```

Expected: `DESIGN.md` has the "Engineering discipline" section describing the rules reference, the red proof, the seams and the enforcement; and its change is part of this feature's commits, not a later afterthought.

## 8. The planning instructions carry the test-first behaviour (FR-006a)

```bash
grep -n 'Test seams\|failing test\|seam' core/roles/spec-builder.md
git status --porcelain .specify/
```

Expected: the plan, tasks, analyze and clarify stage entries in `spec-builder.md` state the behaviour of [contracts/plan-artifact.md](./contracts/plan-artifact.md); and `.specify/` is untouched, proving the run edited no SpecKit template, skill or command.

## 9. The severity ceiling overrides the default guidance (FR-015f, FR-015g)

```bash
grep -n 'ENG-7\|ENG-10\|blocking' core/skills/factory/references/findings.md
grep -n 'engineering.md\|ENG-' core/roles/code-standards.md core/roles/review-judge.md core/roles/fixer.md
```

Expected: `findings.md` states the `ENG-7`..`ENG-10` ceiling (at most MEDIUM, never blocking, lowered rather than dropped) **next to and as an explicit override of** its own default line "`critical` and `high` are blocking unless the reviewer says why not", so a reviewer reading the file cannot follow the default for those ids; it also states that an `advisory[]` entry derived from an engineering finding keeps its `ENG-n` citation. `code-standards.md` and `review-judge.md` point at the ceiling and do not restate the rules; `fixer.md` states that no fix work is done on an advisory engineering finding and that "Request changes" at the approver gate is the user's route. No new severity value appears anywhere (`grep -n 'advisory' core/skills/factory/references/findings.md` shows the existing list only).

## 10. The plan-time reason check and the un-runnable-command stop (FR-020b, FR-011b, FR-013b)

```bash
grep -n 'reason\|new file\|dependency' core/roles/spec-builder.md
grep -n 'cannot be run\|un-runnable\|failed' core/roles/code-build.md core/roles/fixer.md
```

Expected: `spec-builder.md` requires a reason line per new file, new abstraction and new dependency in `plan.md`, and has analyze report a MEDIUM, **non-blocking** `ENG-10` finding for a missing one, per [contracts/plan-artifact.md](./contracts/plan-artifact.md); `code-build.md` and `fixer.md` each state the same stop for a test command that cannot be run (name the command and its error, return `failed`, write no code and no third form of red proof). This plan's own worked example is its "Reasons for new files, abstractions and dependencies" section (SC-003a).

## 11. Trial reviews (SC-006, SC-006a, SC-006b, SC-006c) - manual, next run

These need a diff to review, so they are observed on the next real factory run rather than here:

- Hand `code-standards` a diff that adds behaviour with no asserting test and a function duplicating an existing helper: expect two HIGH, blocking findings, each citing an `ENG-n` id (`ENG-1`, `ENG-6`).
- Hand `spec-conformance` a run whose implementation commit bodies lack a `Red:` line: expect it to read the run's commit log (not just the diff), one finding per such commit with the sha in `file`, and none for commits whose proof matches a task, per [contracts/commit-body.md](./contracts/commit-body.md).
- Hand `spec-conformance` a round-2 run with a correct `factory(fix):` commit carrying one `Red:` line per behaviour-changing fix: expect it to read `specs/<branch>/factory/reviews/round-1/verdict.json`, match the lines against its `confirmed_blocking` entries, and raise nothing — in particular no "unmatched against `tasks.md`" finding (FR-015d).
- Confirm the judge's verdict entries keep the `ENG-n` citations when it merges and rates those findings.
- In the same trial review, confirm every finding citing `ENG-7`..`ENG-10` is MEDIUM or lower with `blocking: false`, so no run halts on a clean-code, SOLID, functional-style or over-engineering finding alone, while the `ENG-6` and untested-behaviour findings in the same diff stay HIGH and blocking (SC-006b).
- Confirm the fix round changes nothing for those advisory findings and that each is readable in the verdict's `advisory[]` with its `ENG-n` id (SC-006c).

## 12. End-to-end (DESIGN.md validation plan)

Run `/factory` on a tiny real feature in a repository that has a test runner, and confirm: the plan has a "Test seams" section and a stated reason for every new file, abstraction and dependency it introduces (SC-003a); `tasks.md` puts a failing-test task before each implementation task; each implementation commit body carries a `Red:` line; the analyze report raises nothing for exempt tasks, and any missing reason line appears there as MEDIUM and non-blocking without halting the run. This is the observation the design document's validation plan already prescribes, and it is the only check that exercises the whole discipline.
