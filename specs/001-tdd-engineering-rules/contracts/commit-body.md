# Contract: the red proof in a commit body

The textual interface between the roles that write code and the reviewer that verifies the discipline. Producers: `code-build` (one line per task commit), `fixer` (one line per behaviour-changing fix, in its single fix commit). Consumer: `spec-conformance` (checks each line against `tasks.md`); the user reads the same lines as the run's evidence (SC-007).

## Grammar

Exactly two accepted forms, each on its own line in the commit body:

```text
Red: <test name> failed as expected
Red: not applicable - <existing test> already covers this
```

- `<test name>` and `<existing test>` identify a test precisely enough to find it: the test function or case name, qualified by file or suite when the bare name is ambiguous.
- The separator in the second form is a space, a hyphen-minus, a space.
- No other wording counts as a red proof. "Tested manually", "covered by integration tests", a bare "Red: ok" and an empty value are all unparseable and are findings.

## Placement

- One commit per task carries the task's test and implementation changes; the commit subject stays `factory(implement): <task id> <task title>`, and the `Red:` line goes in that commit's body.
- No separate red commit is created, so the history stays bisectable.
- The fixing role commits all its fixes once (`factory(fix): <finding ids>`) and that body carries one `Red:` line per behaviour-changing fix, in the same two forms.
- A task or fix the plan exempts (documentation or configuration only) carries no `Red:` line; the exemption lives in the plan, not in the commit.

## Verification by spec-conformance

For each implementation commit in `git diff <base>...HEAD`:

| Observation | Result |
|---|---|
| A `Red:` line in one accepted form, naming a test a task in `tasks.md` maps to | No finding |
| No `Red:` line, and the commit's task is not exempt in the plan | Finding, naming the commit and its task |
| A `Red:` line that does not match either form, or whose value is empty | Finding (unparseable), naming the commit and its task |
| A `Red:` line naming a test no task in `tasks.md` maps to | Finding (unmatched), naming the commit, its task and the test |
| No `Red:` line, and the plan declares the commit's task exempt with a reason | No finding |

Verification is textual: the reviewer matches the line against `tasks.md`, it does not replay the failing test run (ADR 0002).
