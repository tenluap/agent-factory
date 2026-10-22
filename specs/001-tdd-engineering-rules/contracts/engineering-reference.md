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
| `ENG-2` | Record the red step in the task's commit body, in one of the two forms of [commit-body.md](./commit-body.md). | Nothing |
| `ENG-3` | Commit a task once, test and implementation together; create no separate red commit. | Nothing |
| `ENG-4` | Put under test only the seams the plan lists; never invent a seam. When a task needs an unlisted seam, stop and report the missing seam as a failure. | Nothing |
| `ENG-5` | Skip a test only where the plan states the exemption and its reason (documentation or configuration only). | Nothing |
| `ENG-6` | Before writing a new function or method, search the module being changed and the repository's shared utility locations by the concept's keywords, once, and reuse or extend an existing one that fits. | Nothing; a genuinely different concern may be new code, with the difference stated |
| `ENG-7` | Write clean code: intention-revealing names, small single-purpose functions, no dead code or duplication, comments that say why. | The repository's documented conventions |
| `ENG-8` | Follow SOLID: one responsibility per unit, extend rather than modify, substitutable abstractions, narrow interfaces, depend on abstractions at the boundaries. | The language's and repository's idiom |
| `ENG-9` | Prefer functional style: pure functions, immutable data, side effects at the edges, composition over inheritance. | The language's and repository's idiom (a framework demanding inheritance wins) |
| `ENG-10` | Add the smallest change that meets the need; do not over-engineer, and state the reason for any new file, abstraction or dependency in the plan. | Nothing |
| `ENG-11` | Where the repository's own constitution or documented conventions contradict a rule above, the repository wins, and the run records `Overridden: ENG-n - <repo rule that wins>` in the plan. | Nothing |

Eleven rules. `ENG-1`..`ENG-5` are test-first (FR-003, FR-007..FR-013a), `ENG-6` reuse (FR-014, FR-014a), `ENG-7`..`ENG-10` clean code, SOLID, functional style and no over-engineering, `ENG-11` precedence (FR-005, FR-006).

## Role reference contract

Each of these six roles contains one reference to the file, and restates no rule inline:

| Role file | Use |
|---|---|
| `core/roles/code-build.md` | Follows every rule while implementing; writes the red proof |
| `core/roles/fixer.md` | Follows every rule when a fix changes behaviour; one red proof line per such fix |
| `core/roles/spec-builder.md` | Plans for the rules: test seams, exemptions, test task ordering, analyze's mapping check, clarify's seam questions, the override line |
| `core/roles/code-standards.md` | Enforces the rules on the diff; cites the id in `evidence` |
| `core/roles/spec-conformance.md` | Checks the red proofs against `tasks.md`; cites the id in `evidence` |
| `core/roles/review-judge.md` | Verifies and rates engineering findings against the same rules, by id |

Unchanged and holding no reference: `security-reviewer.md`, `ui-reviewer.md`, `ux-reviewer.md`, `core/skills/factory/SKILL.md`, every file under `adapters/`, `tools/render.py`.
