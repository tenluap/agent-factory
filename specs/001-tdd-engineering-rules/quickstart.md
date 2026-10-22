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
grep -rl 'ENG-1\b' core/ | sort
```

Expected: the file exists, and `core/skills/factory/references/engineering.md` is the only file under `core/` that states a rule. Role files may cite ids in instructions about citation, but no role restates a rule's content.

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

## 9. Trial reviews (SC-006, SC-006a) - manual, next run

These need a diff to review, so they are observed on the next real factory run rather than here:

- Hand `code-standards` a diff that adds behaviour with no asserting test and a function duplicating an existing helper: expect two HIGH, blocking findings, each citing an `ENG-n` id (`ENG-1`, `ENG-6`).
- Hand `spec-conformance` a run whose implementation commit bodies lack a `Red:` line: expect one finding per such commit and none for commits whose proof matches a task, per [contracts/commit-body.md](./contracts/commit-body.md).
- Confirm the judge's verdict entries keep the `ENG-n` citations when it merges and rates those findings.

## 10. End-to-end (DESIGN.md validation plan)

Run `/factory` on a tiny real feature in a repository that has a test runner, and confirm: the plan has a "Test seams" section; `tasks.md` puts a failing-test task before each implementation task; each implementation commit body carries a `Red:` line; the analyze report raises nothing for exempt tasks. This is the observation the design document's validation plan already prescribes, and it is the only check that exercises the whole discipline.
