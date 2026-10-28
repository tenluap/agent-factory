# Engineering rules

Professional code is correct, readable, maintainable, secure, and fast enough for its requirements. Every role that plans, writes, reviews or judges code follows the applicable rules below. SOLID, Clean Code and coding styles are guidelines applied with judgement; no architecture guarantees quality. The repository's documented conventions take precedence (ENG-11).

The original `ENG-1`..`ENG-11` ids retain their meanings; the 2026-10-25 revision expands their guidance and adds `ENG-12`..`ENG-31`. Test-first, planned seams and commit evidence remain factory process requirements. Apply the broader quality practices in proportion to the change and its risks.

## Rules

- **ENG-1** Test behaviour and important boundaries, including relevant failure paths and edge cases. Use unit tests for focused logic, integration tests for real interactions, and end-to-end tests for critical journeys where appropriate; coverage percentage alone is not proof of quality. Write or extend a failing test before implementing the behaviour, then the smallest passing code, then refactor while tests stay green. This yields to a test-first exemption the plan declares.
- **ENG-2** Record the red step in the task's commit body, in one of the two forms below. This yields to a test-first exemption the plan declares: an exempt task's commit carries no `Red:` line.
- **ENG-3** Complete each commit unit once, with test and implementation together in one passing commit; use the commit-unit definition below for new tasks and legacy resume.
- **ENG-4** Put under test only the seams the plan lists; never invent a seam. When a task needs an unlisted seam, stop and report the missing seam as a failure.
- **ENG-5** Skip a test only where the plan states the exemption and its reason, and only for a part that is documentation or configuration.
- **ENG-6** Give each business rule or piece of knowledge a clear source of truth (DRY). Before a new function or method, search the changed module and shared utility locations once by the concept's keywords; reuse or extend a suitable implementation. Similar-looking code can represent different concepts: abstract only when shared meaning justifies the coupling.
- **ENG-7** Use meaningful, consistent domain names and the repository's vocabulary. Write focused, readable functions with straightforward control flow and no unnecessary nesting; no universal line limit applies. Comments and documentation explain reasoning, constraints, surprising behaviour and public contracts; update them when behaviour changes. Follow the repository's conventions.
- **ENG-8** Apply SOLID where it improves the design, respecting the language and repository idiom: **S**, one coherent responsibility and main reason to change, not one method per class; **O**, extend stable behaviour where variation is expected, without speculative extension mechanisms; **L**, preserve callers' behavioural contracts when replacing implementations; **I**, expose focused interfaces consumers need; **D**, keep core policy independent of infrastructure details. Dependency injection can help; interfaces everywhere are unnecessary.
- **ENG-9** Prefer predictable functions, local state, immutable values and visible side effects where practical. Control shared mutation explicitly. Compose collaborating components when inheritance adds complexity; use inheritance when the relationship, behavioural contract or framework requires it. A functional style is a preference, not a universal architecture.
- **ENG-10** Keep it simple (KISS) and build only demonstrated needs (YAGNI). Choose the simplest solution satisfying the requirements over clever code, speculative features, configuration and extension points. State the reason for each new file, abstraction or dependency in the plan.
- **ENG-11** Where the repository's own constitution or documented conventions contradict a factory rule, the repository wins, and the plan records `Overridden: ENG-n - <repo rule that wins>`.
- **ENG-12** Understand the problem before coding. Clarify expected behaviour, constraints, edge cases and acceptance criteria; resolve consequential ambiguity through the orchestrator before implementing it.
- **ENG-13** Separate business rules, presentation, persistence and external integrations enough to make changes manageable. A concern does not automatically need a separate service or project.
- **ENG-14** Keep related behaviour cohesive and dependencies between unrelated components low. A feature change should require understanding a limited portion of the system.
- **ENG-15** Encapsulate internal representation behind operations that preserve valid state. Make inputs, outputs, errors, ownership and side effects explicit in contracts.
- **ENG-16** Use types to express valid states where practical: meaningful domain types, enums and explicit optional values. Prevent invalid combinations instead of scattering repeated checks.
- **ENG-17** Handle errors deliberately. Distinguish expected failures from programming defects, preserve diagnostic context, and release resources on success and failure. Surface failures rather than silently swallowing exceptions.
- **ENG-18** Keep tests deterministic, readable and capable of detecting meaningful regressions. Mock external boundaries when useful while retaining enough integration testing to verify real interactions.
- **ENG-19** Refactor incrementally while preserving behaviour. Remove dead code and obsolete abstractions; add regression tests for consequential bug fixes. Keep checks green between small structural changes.
- **ENG-20** Measure before optimising performance: establish a baseline, profile representative workloads, identify the bottleneck, and compare after the change. Investigate CPU, waiting, memory, storage and network activity as appropriate. Optimise to stated requirements, not unmeasured intuition.
- **ENG-21** Choose algorithms and data structures for the expected data volume and growth. Consider time and space complexity; avoid repeated searches, redundant calculations and loading entire datasets when bounded processing meets the need.
- **ENG-22** Treat database and network access as performance decisions. Check relevant N+1 queries, round trips, indexes, payload sizes and result bounds; inspect query plans and measure realistic volumes when changing a performance-sensitive access path.
- **ENG-23** Use concurrency and caching deliberately. Bound parallel work, support cancellation where appropriate, and protect shared state. Define cache freshness, invalidation, size and failure behaviour. Asynchronous execution does not automatically accelerate CPU work.
- **ENG-24** Design for failures and resource limits. Set appropriate timeouts and bounds on queues, requests and memory. Retry transient failures with limits and backoff; protect consequential operations from duplicate effects.
- **ENG-25** Build security into the change: validate untrusted input, parameterise queries, encode output for its context, and enforce authorisation at trusted boundaries. Keep secrets out of source and logs; use established security libraries rather than custom security mechanisms.
- **ENG-26** Protect data integrity with appropriate invariants, constraints and transactions. Account for concurrent updates, duplicate requests, partial failures and compatibility when changing schemas or APIs.
- **ENG-27** Prefer suitable standard-library and existing-project features. Evaluate new dependencies for maintenance, security, licensing, size and operational cost; track versions and keep builds reproducible.
- **ENG-28** Automate relevant routine quality checks: formatting, linting, type checks, tests and security checks in continuous integration. Reuse repository tooling and make builds and checks repeatable with minimal manual setup.
- **ENG-29** Keep changes, commits and pull requests focused and reviewable. Explain the problem, resulting behaviour and relevant verification. Review correctness, design, complexity, security and maintainability.
- **ENG-30** Make relevant production behaviour observable through useful structured logs, metrics and tracing. For services, consider latency, traffic, errors and resource saturation. Protect sensitive information in telemetry and avoid unnecessary instrumentation.
- **ENG-31** Plan safe delivery and maintenance: relevant rollout, rollback, configuration, migrations and compatibility. Record significant tradeoffs and address technical debt according to its actual impact.

## Application

Apply each practice to a concrete problem and verify that it improves the result. Do not turn a preference into a requirement for interfaces, abstraction, complete deduplication, maximum coverage, design patterns or microservices. Plan relevant quality constraints and verification without adding unrelated infrastructure or checks.

Reviewers cite the applicable rule and concrete evidence, and follow the severity policy in `findings.md`. A design preference alone is advisory; demonstrated correctness, security, integrity, resource or stated-performance defects are judged by consequence.

## Further reading

The rules above are self-contained; external reading is optional:

- [Martin Fowler: YAGNI](https://martinfowler.com/bliki/Yagni.html) — build capabilities when needed.
- [Google: what to look for in a code review](https://google.github.io/eng-practices/review/reviewer/looking-for.html) — design, complexity, tests, naming, comments and documentation.
- [Brendan Gregg: performance methodology](https://www.brendangregg.com/methodology.html) — investigate representative performance with a method.
- [OWASP: secure code review](https://cheatsheetseries.owasp.org/cheatsheets/Secure_Code_Review_Cheat_Sheet.html) — trust boundaries, security controls and sensitive data.
- [Martin Fowler: continuous integration](https://martinfowler.com/articles/continuousIntegration.html) — repeatable automated builds and checks.
- [Google SRE: monitoring distributed systems](https://sre.google/sre-book/monitoring-distributed-systems/) — useful service signals and monitoring.

## Commit units

A new behavior-changing task has one checkbox containing ordered failing-test, implementation and passing-verification steps, the mapped test seam, required red proof and an observable completion condition. The test step alone is unfinished work. Observe red, implement, verify green, then check the unit and commit its test, implementation and task status together. Documentation/configuration exemptions retain ENG-5.

On resume, inspect task status, worktree changes, test output and commit history before selecting the first unfinished unit. Preserve a completed passing commit; continue unfinished work without duplicating it. Adjacent legacy test/implementation entries form one unit only when their named target, dependencies or explicit pairing identify one unambiguous pair; adjacency alone is insufficient. A checked test half does not prove a completed unit: reconcile the evidence, finish the implementation and passing checks, then check both entries in the same passing commit. Preserve existing commits rather than rewriting history. Ambiguous pairing stops before behavior edits and is reported for resolution.

Generation, analysis, execution, fixing and review use this same definition. A fix may group related changes in its existing single passing fix commit while retaining the required red proof per behavior-changing fix.

## Confirmed test scope

The plan's declarations list each public test seam and its required injected failure paths (`none` when no injection is needed). Task requirements map to those declarations. Confirmation is separate evidence of explicit acceptance of that exact seam-to-failure-path scope; it never declares a seam. Store the accepted scope with the `Confirmed:` line or a referenced immutable snapshot. Reuse legacy name-only confirmation only when separate explicit acceptance evidence proves the complete current scope.

Adding, removing, renaming or expanding a declared seam or failure path invalidates prior confirmation. Missing coverage or absent/stale scope acceptance blocks implementation with a HIGH finding; obtain fresh protected confirmation through the orchestrator. Valid documentation/configuration exemptions remain exempt. Later-discovered gaps stop implementation/fixing under ENG-4.

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
