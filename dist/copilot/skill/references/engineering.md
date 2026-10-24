# Engineering rules

Every factory run follows these rules. They bind every role that writes, plans, reviews or judges code. Where the repository's documented conventions contradict a rule, the repository wins (ENG-11).

## Rules

- **ENG-1** Write or extend a failing test for the behaviour before the code that implements it; then the smallest code that passes; then refactor only while tests are green, re-running them after. This yields to a test-first exemption the plan declares.
- **ENG-2** Record the red step in the task's commit body, in one of the two forms below. This yields to a test-first exemption the plan declares: an exempt task's commit carries no `Red:` line.
- **ENG-3** Commit a task once, test and implementation together; create no separate red commit.
- **ENG-4** Put under test only the seams the plan lists; never invent a seam. When a task needs an unlisted seam, stop and report the missing seam as a failure.
- **ENG-5** Skip a test only where the plan states the exemption and its reason, and only for a part that is documentation or configuration.
- **ENG-6** Before writing a new function or method, search the module being changed and the repository's shared utility locations by the concept's keywords, once, and reuse or extend an existing one that fits.
- **ENG-7** Write clean code: intention-revealing names, small single-purpose functions, no dead code or duplication, comments that say why. This yields to the repository's documented conventions.
- **ENG-8** Follow SOLID: one responsibility per unit, extend rather than modify, substitutable abstractions, narrow interfaces, depend on abstractions at the boundaries. This yields to the language's and repository's idiom.
- **ENG-9** Prefer functional style: pure functions, immutable data, side effects at the edges, composition over inheritance. This yields to the language's and repository's idiom, and a framework demanding inheritance wins.
- **ENG-10** Add the smallest change that meets the need; do not over-engineer, and state the reason for any new file, abstraction or dependency in the plan.
- **ENG-11** Where the repository's own constitution or documented conventions contradict a rule above, the repository wins, and the plan records `Overridden: ENG-n - <repo rule that wins>`.

## Red proof

Exactly two forms count, each on its own line in the task's commit body:

```text
Red: <test name> failed as expected
Red: not applicable - <existing test> already covers this
```

`<test name>` and `<existing test>` identify a test precisely enough to find it. The separator in the second form is a space, a hyphen-minus, a space. No other wording counts as a red proof, and there is no third form.

## Definitions

- **Behaviour-changing** (the trigger for ENG-1 and ENG-2): a unit of work changes what an entry point returns or does, and a change confined to documentation, configuration or generated output is not.
- **Shared utility locations** (the bound of ENG-6): the directories the repository's own conventions name as shared (for example `helpers/`, `utils/`, `util/`, `common/`, `lib/`, `shared/`), plus any module the module being changed already imports for helpers, searched as a keyword-level text search rather than a review of the whole repository.
- **When the red step cannot be observed at all** (ENG-1): a repository with a test runner whose test command cannot be run (missing dependency, broken configuration, no runner binary) is a stop, not an exemption — the role stops and reports the un-runnable command and its error as a failure, exactly as ENG-4 handles a missing seam, writing no behaviour-changing code and recording no third form of red proof, and this binds the fixing role on the same terms as the implementing role.
