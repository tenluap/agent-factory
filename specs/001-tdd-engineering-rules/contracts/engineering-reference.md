# Contract: the engineering rules reference

The interface this feature exposes to every role, and through the rendered output to every harness. Consumers: the implementing and fixing roles (follow), the planning role (plan for), the code-standards and spec-conformance reviewers (enforce), the review judge (rate). Source of truth: `core/skills/factory/references/engineering.md`.

## File contract

- Path in source: `core/skills/factory/references/engineering.md`.
- Path a role addresses: `<F>/references/engineering.md`.
- Rendered path, every harness: `dist/<harness>/skill/references/engineering.md`, byte-identical to the source.
- Self-contained: no link or dependency to a skill outside the factory.
- Harness-neutral: no harness tool, path or command named.
- Style: one rule per list entry, imperative, one idea per sentence, glossary terms only.

## Rule id contract

- Format: `ENG-` followed by a positive integer, contiguous from `ENG-1`, unique within the file.
- Stable: an id always means the same rule; a rule that is withdrawn keeps its id retired rather than reused.
- Citation: `ENG-n` is the token used in a reviewer finding, a judge verdict entry, and a plan override line. A citation is valid only if the id exists in the file.

## Rule set

| Id | Statement | Yields to |
|---|---|---|
| `ENG-1` | Write or extend a failing test for the behaviour before writing the code that implements it; then the smallest code that passes; then refactor only while tests are green, re-running them after. | A declared test-first exemption in the plan |
| `ENG-2` | Record the red step in the task's commit body, in one of the two forms of [commit-body.md](./commit-body.md). | A declared test-first exemption in the plan (an exempt task's commit carries no `Red:` line) |
| `ENG-3` | Commit a task once, test and implementation together; create no separate red commit. | Nothing |
| `ENG-4` | Put under test only the seams the plan lists; never invent a seam. When a task needs an unlisted seam, stop and report the missing seam as a failure. | Nothing |
| `ENG-5` | Skip a test only where the plan states the exemption and its reason (documentation or configuration only). | Nothing |
| `ENG-6` | Before writing a new function or method, search the module being changed and the repository's shared utility locations by the concept's keywords, once, and reuse or extend an existing one that fits. | Nothing; a genuinely different concern may be new code, with the difference stated |
| `ENG-7` | Write clean code: intention-revealing names, small single-purpose functions, no dead code or duplication, comments that say why. | The repository's documented conventions |
| `ENG-8` | Follow SOLID: one responsibility per unit, extend rather than modify, substitutable abstractions, narrow interfaces, depend on abstractions at the boundaries. | The language's and repository's idiom |
| `ENG-9` | Prefer functional style: pure functions, immutable data, side effects at the edges, composition over inheritance. | The language's and repository's idiom (a framework demanding inheritance wins) |
| `ENG-10` | Add the smallest change that meets the need; do not over-engineer, and state the reason for any new file, abstraction or dependency in the plan. | Nothing |
| `ENG-11` | Where the repository's own constitution or documented conventions contradict a rule above, the repository wins, and the run records `Overridden: ENG-n - <repo rule that wins>` in the plan. | Nothing |

**Definitions the rule text carries** (so two agents draw the same boundary):

- **Behaviour-changing** (the trigger for `ENG-1` and `ENG-2`): a unit of work changes what an entry point returns or does. A change confined to documentation, configuration or generated output is not behaviour-changing.
- **Shared utility locations** (the bound of `ENG-6`): the directories the repository's own conventions name as shared (for example `helpers/`, `utils/`, `util/`, `common/`, `lib/`, `shared/`), plus any module the module being changed already imports for helpers. The search is a keyword-level text search over those locations, not a semantic review of the whole repository.
- **When the red step cannot be observed at all** (`ENG-1`): a repository with a test runner whose test command cannot be run (missing dependency, broken configuration, no runner binary) is a stop, not an exemption. The role stops and reports the un-runnable command and its error as a failure, exactly as `ENG-4` handles a missing seam, and writes no behaviour-changing code and no third form of red proof (FR-011b, FR-013b). This binds the fixing role on the same terms as the implementing role.

Eleven rules. `ENG-1`..`ENG-5` are test-first (FR-003, FR-007..FR-013b), `ENG-6` reuse (FR-014, FR-014a), `ENG-7`..`ENG-10` clean code, SOLID, functional style and no over-engineering, `ENG-11` precedence (FR-005, FR-006).

## Severity contract: which rules can block

| Rules | Ceiling | Blocking? | Where it is enforced |
|---|---|---|---|
| `ENG-6` (duplication) and behaviour added with no asserting test (`ENG-1`) | HIGH | Yes | `code-standards.md`, confirmed by the judge (FR-015, FR-015a) |
| `ENG-2`..`ENG-5` red-proof and seam defects | As the finding's own requirement states (HIGH for a missing, unparseable or unmatched `Red:` line; HIGH for an unlisted seam at artifact time) | Yes | `spec-conformance.md`, the analyze check (FR-015b, FR-015d, FR-020). "Unmatched" has no meaning for a user-changes fix round's commit, which is matched against neither the verdict nor `tasks.md` |
| `ENG-7`, `ENG-8`, `ENG-9`, `ENG-10` | MEDIUM | **Never** | The raising reviewer and the judge alike; a finding above the ceiling is lowered to MEDIUM, never dropped (FR-015f). The ceiling is keyed on the cited id and reaches these four only: a finding citing `ENG-1`..`ENG-6` keeps the severity of its own row above |

- A finding held at the `ENG-7`..`ENG-10` ceiling is advisory: no verdict-driven fix round acts on it, it travels to the user in the verdict's `advisory[]` list keeping its `ENG-n` citation in that entry's existing `summary` (its `sources` still link the reviewer finding with the full evidence, so no verdict field is added), and the user's route to having it fixed is the approver's existing "Request changes" — a change request naming an advisory finding is implemented exactly as asked, like any other request (FR-015g, SC-006b, SC-006c).
- This ceiling is written into `core/skills/factory/references/findings.md` as an explicit **override of that file's own default severity guidance** ("`blocking`: the reviewer's call; `critical` and `high` are blocking unless the reviewer says why not"), so the two instructions in that file cannot be read as a conflict (FR-015f). `code-standards.md` and `review-judge.md` point at it and do not restate it.
- `ENG-10` has an artifact-time counterpart with the same ceiling: a new file, abstraction or dependency the plan introduces with no stated reason is a MEDIUM, non-blocking analyze finding ([plan-artifact.md](./plan-artifact.md), FR-020b).
- No new severity level and no new field carry any of this: `severity` and `blocking` of the existing reviewer-report and verdict shapes are enough.

## Role reference contract

Each of these six roles contains one reference to the file, and restates no rule inline:

| Role file | Use |
|---|---|
| `core/roles/code-build.md` | Follows every rule while implementing; writes the red proof; stops on a missing seam or an un-runnable test command |
| `core/roles/fixer.md` | Follows every rule when a fix changes behaviour; one red proof line per such fix; stops on an un-runnable test command; performs no verdict-driven fix work on advisory engineering findings, while implementing a user change request that names one exactly as asked |
| `core/roles/spec-builder.md` | Plans for the rules: test seams, exemptions, test task ordering, the reason line per new file/abstraction/dependency, analyze's mapping and reason checks, clarify's seam questions, the override line |
| `core/roles/code-standards.md` | Enforces the rules on the diff; cites the id in `evidence`; applies the severity ceiling above |
| `core/roles/spec-conformance.md` | Checks the red proofs against `tasks.md`, a verdict-driven fix round's commit against the previous round's verdict, and a user-changes fix round's commit for grammar and per-fix presence only; cites the id in `evidence` |
| `core/roles/review-judge.md` | Verifies and rates engineering findings against the same rules, by id; applies the same ceiling and routes capped findings to `advisory[]` |

Unchanged and holding no reference: `security-reviewer.md`, `ui-reviewer.md`, `ux-reviewer.md`, `core/skills/factory/SKILL.md`, every file under `adapters/`, `tools/render.py`.
