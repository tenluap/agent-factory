# Phase 1 Data Model: Engineering discipline for factory code-writing roles

This feature stores no records. Its "entities" are textual artefacts that roles read and write: files, sections and commit-body lines. Each one is defined below with its location, its fields, the rules that validate it, and the requirement it serves. Terms are the glossary's (`CONTEXT.md`).

## Engineering rules reference

- **Location**: `core/skills/factory/references/engineering.md` (rendered to `dist/<harness>/skill/references/engineering.md`; addressed by roles as `<F>/references/engineering.md`).
- **Fields**: a short preamble (scope, and that the repository's documented conventions win); an ordered list of rules, each with an `ENG-n` id, a one-line imperative statement, and at most a sentence of qualification; and two one-sentence definitions the rules depend on — **behaviour-changing** (the trigger for `ENG-1` and `ENG-2`) and **shared utility locations** (the bound of `ENG-6`).
- **Rules**: exactly one such file exists in `core/` (SC-004); it names no harness tool, path or command (constitution II); it depends on no skill outside the factory (FR-002); it covers test-first, clean code, SOLID, functional preference and reuse (FR-003); it states the repository-conventions-win rule (FR-006).
- **Relationships**: referenced by six roles (below); cited by findings, verdicts and plan overrides through rule ids.
- **Requirements**: FR-001, FR-002, FR-003, FR-006, FR-024.

## Rule

- **Location**: one list entry in the engineering rules reference.
- **Fields**: `id` (`ENG-n`), `statement` (imperative, one idea), optional `qualification` (when the rule yields: language idiom, repository convention).
- **Rules**: ids are unique and stable; numbering is contiguous from `ENG-1`; renumbering is deliberate because findings cite ids (SC-004a).
- **Relationships**: cited by a finding, a verdict entry or a rule override.
- **Requirements**: FR-004a, SC-004a. Full set in [contracts/engineering-reference.md](./contracts/engineering-reference.md).

## Role reference

- **Location**: one line in each of `core/roles/spec-builder.md`, `code-build.md`, `fixer.md`, `code-standards.md`, `spec-conformance.md`, `review-judge.md`.
- **Fields**: the path `<F>/references/engineering.md` and what the role does with it (follow, plan for, enforce, rate).
- **Rules**: the role points at the file and does not restate a rule inline (SC-004); the other three roles (security, UI, UX reviewers) and the orchestrator skill are unchanged.
- **Requirements**: FR-004, FR-015c.

## Test seam

- **Location**: the plan's "Test seams" section; named again by the test task and the implementation task in `tasks.md`.
- **Fields**: the public entry point put under test, and the behaviour it covers.
- **Rules**: agreed at plan time; an implementation task is mapped to exactly one listed seam unless the plan exempts it; the implementing role never invents one (FR-011, FR-011a).
- **State transitions**: listed in the plan -> targeted by a failing-test task -> asserted by a passing test after the implementation task. A task that needs an unlisted seam ends the run's implement stage in `failed` instead.
- **Requirements**: FR-016, FR-019, FR-011, FR-011a, SC-002, SC-003.

## Test-first exemption

- **Location**: the plan's "Test seams" section.
- **Fields**: the part of the change exempted (whole change, or named tasks/files) and the reason.
- **Rules**: documentation- or configuration-only parts only; never implicit; an exempt task is excluded from the analyze seam-mapping check rather than reported at a lower severity (FR-012, FR-020a).
- **Requirements**: FR-017, FR-012, FR-020a, FR-025, SC-003.

## Red proof

- **Location**: the body of the single commit carrying a task's test and implementation changes; for the fixing role, the body of its single fix commit.
- **Fields**: one line per behaviour-changing unit of work, in one of exactly two forms (`Red: <test name> failed as expected`, or `Red: not applicable - <existing test> already covers this`).
- **Behaviour-changing** (when a line is required): the unit of work changes what an entry point returns or does. A unit confined to documentation, configuration or generated output is not behaviour-changing and carries no line.
- **Rules**: no other wording stands in for a proof; in an implementation commit the named test must map to a task in `tasks.md`; in the single fix commit each line is matched against the `confirmed_blocking` findings of the verdict at `<spec_dir>/factory/reviews/round-<n-1>/verdict.json` (the previous round's verdict, the one the fix commit answers) instead, so the `tasks.md` unmatched rule never fires on a fix commit; the fixing role writes one line per behaviour-changing fix (FR-009, FR-009a, FR-013a, FR-015b, FR-015d).
- **Absent, never substituted**: where the repository has a test runner whose test command cannot be run, no line is written at all — the role stops and returns a failure naming the un-runnable command and its error (FR-011b for the implementing role, FR-013b for the fixing role), so there is no commit and no third form of proof.
- **Relationships**: checked by the spec-conformance reviewer, which reads the run's commit log (`git log <base>..HEAD`, subjects and bodies) because the squashed diff carries no commit messages; read by the user as the run's positive evidence (SC-007).
- **Requirements**: FR-009, FR-009a, FR-010, FR-013a, FR-015b, FR-015d, FR-015e, SC-001, SC-006a. Grammar in [contracts/commit-body.md](./contracts/commit-body.md).

## Rule override

- **Location**: the plan's "Test seams" section, as `Overridden: ENG-n - <repo rule that wins>`.
- **Fields**: the rule id and the repository rule that wins.
- **Rules**: the overriding rule must be documented in the consuming repository (its constitution or written conventions); the factory's rules file is never edited per-run; one line per overridden rule, or `Overridden: none`.
- **Requirements**: FR-005, FR-006, SC-004a.

## Engineering finding

- **Location**: a reviewer report (`STD-n`, `SPEC-n`) and then the judge verdict, in the shapes already defined in `core/skills/factory/references/findings.md`.
- **Fields**: the existing finding fields; `evidence` additionally names the `ENG-n` id the finding rests on. A commit-level finding (a red-proof finding) has no file and no line: `file` holds the commit sha with the task or finding id, and `line` is omitted or `0` (FR-015e). An `advisory[]` entry derived from an engineering finding keeps the `ENG-n` citation, so the verdict's advisory entry gains an `evidence` field (SC-004a).
- **Rules**: untested added behaviour and real duplication are HIGH and blocking (FR-015, FR-015a); a missing, unparseable or unmatched `Red:` line is a spec-conformance finding (FR-015b, FR-015d); the judge verifies and rates it against the same rule by id (FR-015c); style preference that no document or neighbouring code supports is not a finding.
- **Severity ceiling by rule** (FR-015f): a finding whose cited id is `ENG-7`..`ENG-10` has `severity` at most `medium` and `blocking: false`, set by the reviewer that raises it and preserved by the judge that rates it; one above the ceiling is lowered to `medium`, never dropped. This ceiling is written into `core/skills/factory/references/findings.md` as an explicit override of that file's default guidance ("`critical` and `high` are blocking unless the reviewer says why not"), so the two instructions cannot be read as a conflict. Only `ENG-6` duplication and untested added behaviour carry HIGH and blocking.
- **Advisory lifecycle** (FR-015g): a finding held at or below the ceiling goes to the verdict's `advisory[]` with its `evidence`/`ENG-n` citation; the fix round performs no work on it; it reaches the user through the existing approver screen, whose "Request changes" is the only route back into the run for it. No new field, list, severity or stage carries it (SC-006b, SC-006c).
- **Requirements**: FR-015, FR-015a, FR-015b, FR-015c, FR-015d, FR-015e, FR-015f, FR-015g, FR-004a, SC-006, SC-006a, SC-006b, SC-006c, SC-004a.

## Analyze seam-mapping finding

- **Location**: the analyze report at `specs/<branch>/factory/analyze-<n>.md`, in the existing report shape.
- **Fields**: the offending implementation task id, which of the three conditions failed (no mapped seam, no immediately preceding test task, or a named seam the plan does not list), severity HIGH, blocking.
- **Rules**: HIGH, never CRITICAL (reserved for constitution violations); exempt tasks are excluded entirely; a HIGH finding feeds the existing remediation loop.
- **Requirements**: FR-020, FR-020a.

## Simplicity reason

- **Location**: `plan.md`, one line (or one table row) per new file, new abstraction and new dependency the plan introduces; in this feature's own plan, the section "Reasons for new files, abstractions and dependencies".
- **Fields**: the thing introduced (path for a file, name for an abstraction or dependency), its kind (file / abstraction / dependency), and the reason it is needed.
- **Rules**: one reason per introduced thing; "none" is stated explicitly for a kind the change introduces nothing of, so silence is never read as completeness; a generated file is justified as mandated by the render (constitution III) rather than chosen. The reason may live in the Constitution Check (V) instead of being repeated, as long as the line points at it.
- **Relationships**: read by the analyze stage's reason check; derived from `ENG-10` and constitution V; read by the user at the approver gate as the record of what the change added and why.
- **Requirements**: FR-020b, SC-003a, FR-025 (for this change's own plan).

## Analyze simplicity finding

- **Location**: the analyze report at `specs/<branch>/factory/analyze-<n>.md`, in the existing report shape.
- **Fields**: the new file, abstraction or dependency whose reason is missing, the rule id `ENG-10`, severity MEDIUM, `blocking: false`.
- **Rules**: MEDIUM and non-blocking always, because `ENG-10` is a judgement call and the FR-015f ceiling applies at artifact time too; it MUST NOT block the run or by itself trigger the remediation loop's blocking path; one finding per unjustified thing, so the user can see how many there are.
- **Relationships**: the artifact-time counterpart of a review-time `ENG-10` finding, with the same ceiling.
- **Requirements**: FR-020b, SC-003a, FR-015f.
