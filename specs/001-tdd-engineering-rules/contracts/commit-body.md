# Contract: the red proof in a commit body

The textual interface between the roles that write code and the reviewer that verifies the discipline. Producers: `code-build` (one line per task commit), `fixer` (one line per behaviour-changing fix, in its single fix commit). Consumer: `spec-conformance` (checks each line against `tasks.md`, or against the round's verdict for a fix commit); the user reads the same lines as the run's evidence (SC-007).

## Grammar

Exactly two accepted forms, each on its own line in the commit body:

```text
Red: <test name> failed as expected
Red: not applicable - <existing test> already covers this
```

- `<test name>` and `<existing test>` identify a test precisely enough to find it: the test function or case name, qualified by file or suite when the bare name is ambiguous.
- The separator in the second form is a space, a hyphen-minus, a space.
- No other wording counts as a red proof. "Tested manually", "covered by integration tests", a bare "Red: ok" and an empty value are all unparseable and are findings.
- There is no third form for a test run that could not happen. Where the repository has a test runner whose test command cannot be run, the producing role writes no commit at all: it stops and returns a failure naming the task or fix, the un-runnable command and its error (FR-011b for `code-build`, FR-013b for `fixer`), and the orchestrator's existing failure policy halts the run.

## Placement

- One commit per task carries the task's test and implementation changes; the commit subject stays `factory(implement): <task id> <task title>`, and the `Red:` line goes in that commit's body.
- No separate red commit is created, so the history stays bisectable.
- The fixing role commits all its fixes once (`factory(fix): <finding ids, or "user changes">`) and that body carries one `Red:` line per behaviour-changing fix, in the same two forms.
- A task or fix the plan exempts (documentation or configuration only) carries no `Red:` line; the exemption lives in the plan, not in the commit.

## Verification by spec-conformance

The run's squashed diff carries no commit messages, so the reviewer reads the commit metadata explicitly:

```bash
cd <worktree> && git log --format='%H%n%s%n%b%n--' <base>..HEAD
```

Implementation commits are those whose subject is `factory(implement): <task id> <task title>`; the fix commit is the one whose subject is `factory(fix): <finding ids, or "user changes">`. This scope line belongs in `core/skills/factory/references/findings.md` ("Reviewing") so any reviewer whose lens needs commit metadata has it (FR-015e).

### Implementation commits (matched against `tasks.md`)

| Observation | Result |
|---|---|
| A `Red:` line in one accepted form, naming a test a task in `tasks.md` maps to | No finding |
| No `Red:` line, and the commit's task is not exempt in the plan | Finding, naming the commit and its task |
| A `Red:` line that does not match either form, or whose value is empty | Finding (unparseable), naming the commit and its task |
| A `Red:` line naming a test no task in `tasks.md` maps to | Finding (unmatched), naming the commit, its task and the test |
| No `Red:` line, and the plan declares the commit's task exempt with a reason | No finding |

### The fix commit (matched against the round's verdict, not `tasks.md`)

A fix commit **is** checked (FR-013a would otherwise be unverifiable), and its `Red:` lines are matched against the judge verdict's `confirmed_blocking` findings, because a fix's test belongs to a finding and not to a task. The `tasks.md` "unmatched" rule above never applies to a fix commit.

The verdict is a file, named so a stateless reviewer can read it in one spawn (FR-015d, constitution IV):

```text
<spec_dir>/factory/reviews/round-<n-1>/verdict.json
```

where `n` is the review round the reviewer is running in, so `n-1` is the round whose verdict the fix commit answers. In round 1 there is no fix commit and no such file, and this whole section does not apply. The path is the one the orchestrator already writes (`core/skills/factory/SKILL.md`, review step 4); nothing new is persisted and no extra spawn input is needed.

| Observation | Result |
|---|---|
| One `Red:` line in an accepted form per behaviour-changing confirmed finding the commit fixes | No finding |
| A behaviour-changing confirmed finding fixed with no `Red:` line for it | Finding, naming the fix commit and the finding id |
| A `Red:` line that does not match either form, or whose value is empty | Finding (unparseable), naming the fix commit |
| A fix confined to documentation, configuration or generated output, with no `Red:` line | No finding (not behaviour-changing) |
| A fix commit whose subject names `user changes`, or whose round's verdict carries no `confirmed_blocking` entries | Grammar only: each `Red:` line it carries must be in an accepted form, and the diff's behaviour-changing fixes must each have one. It is matched against neither `tasks.md` nor the verdict |
| An empty `confirmed_blocking` list for the round | No finding by itself |

The approver's "Request changes" produces the second kind of fix commit (`factory(fix): user changes`), which re-runs review and is behaviour-changing often enough that FR-013a still demands a `Red:` line per behaviour-changing fix. Because it answers the user and not a verdict, the `confirmed_blocking` matching above does not apply to it: the reviewer checks grammar and per-fix presence from the diff alone, so two reviewers reach the same result on the same commit.

Verification is textual: the reviewer matches the line against `tasks.md` (or the verdict file), it does not replay the failing test run (ADR 0002).

Advisory engineering findings (`ENG-7`..`ENG-10`) produce no verdict-driven fix work, so a verdict-driven fix commit never carries a `Red:` line for one and the absence of one is never a finding (FR-015g). Where the user sent one back with "Request changes", the fix lands in a user-changes commit and is checked by the row above.

### Reporting a commit-level finding

A finding about a commit has no file and no line. In the reviewer report shape of `core/skills/factory/references/findings.md`, `file` holds the commit sha (followed by the task id or finding id where one applies, e.g. `a1b2c3d (T007)`), and `line` is omitted or `0` (FR-015e).
