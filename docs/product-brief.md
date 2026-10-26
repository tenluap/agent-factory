# Agent Factory — product brief and rebuild blueprint

**Prepared:** 24 October 2026  
**Engineering policy revised:** 25 October 2026  
**Audience:** Product owners, developers, and coding agents recreating or extending a software factory.  
**Status:** Reviewable product brief. It describes the existing factory and recommends a more efficient rebuild; it does not change the factory's behaviour.

## 1. Product in one paragraph

Agent Factory turns a feature request into an isolated, specified, implemented, tested, reviewed change that a person can approve for a pull request. A single orchestrator manages specialist roles, records progress and decisions on disk, and resumes interrupted work without depending on the original conversation. A portable core defines the workflow; small adapters translate it into the coding-agent harness the user chooses. The product should reduce the human coordination, repeated context loading, and recovery work involved in delivering a feature while keeping the user responsible for scope decisions and publication.

**Product promise:** Describe the change, settle the important decisions, and receive a reviewable implementation with evidence of what was built, checked, assumed, and left unresolved.

The factory's primary unit is **one feature in one repository**, ending at an open pull request. Its success depends on delivery quality and recoverability as well as speed.

## 2. Evidence and how to use this brief

This brief combines the supplied [README](../README.md), the [harness-agnostic plan](<Harness-agnostic factory design and plan.md>), and the repository's current design, role prompts, protocols, adapters, and helper scripts. The inspection baseline is commit `3162747`, together with the supplied plan and the working-tree files present during inspection. Existing local changes were left in place.

Three labels distinguish evidence from product choices:

| Label | Meaning |
|---|---|
| **Baseline** | Present in the repository's documented workflow, prompts, or scripts. This is evidence of the intended implementation, not a claim that every path was exercised on every harness. |
| **Rebuild requirement** | Behaviour a new implementation should preserve or make explicit. |
| **Recommendation** | An improvement proposed here. It needs its own design decision before changing this repository. |

The attached plan is historical input. Its opening describes a proposal, but the current repository already contains the portable core, five adapters, stateless roles, a renderer, and shared run discovery. Recreating the factory should start from that consolidated product definition rather than replaying the migration from Claude Code.

Use sections 3–8 to understand the product, sections 9–14 to specify it, and sections 15–19 to build and validate it. The source map at the end identifies the detailed contracts to preserve.

## 3. Problem and desired outcomes

Coding agents can produce useful changes, but users still coordinate much of the delivery process:

- Turn an incomplete request into agreed requirements.
- Carry decisions between specification, implementation, and review.
- Keep generated work separate from their active checkout.
- Recover progress after a context limit, crash, or session change.
- Determine whether the implementation matches the request and repository conventions.
- Reconcile overlapping or contradictory review findings.
- Decide whether a change is ready to publish.

The factory packages those responsibilities into one repeatable workflow. A successful run leaves enough durable evidence for someone who was absent from the conversation to understand the change and continue the work.

| Desired outcome | Observable evidence |
|---|---|
| Less human coordination | Fewer waits for routine decisions; one orchestrator presents the questions and final approval. |
| Less repeated work | Completed stages and tasks survive restarts; accepted answers are reused. |
| More predictable delivery | Explicit completion conditions, retry limits, review limits, and halt reasons. |
| Better reviewability | Linked brief, specification, plan, tasks, verification results, findings, and verdict. |
| Harness portability | The same workflow and saved run can execute through another conforming adapter. |
| Measurable efficiency | Time, human waits, role invocations, and usage estimates are available per run. |

“More efficient” has two meanings here: **easier to recreate the factory itself**, and **cheaper to operate the factory on future features**. The build sequence addresses the first; adaptive planning, compact context, conditional reviews, and bounded repair address the second.

## 4. Users and jobs to be done

| User | Job | What they need from the product |
|---|---|---|
| Individual developer | Deliver a feature without manually coordinating every agent. | Fast setup, sensible defaults, isolated changes, understandable approval. |
| Technical lead or maintainer | Delegate work while preserving repository expectations. | Explicit scope, documented rule precedence, verification evidence, review findings. |
| Developer returning to interrupted work | Continue without reconstructing the previous conversation. | Run discovery, a concise status digest, saved decisions, a reliable next action. |
| Factory builder or adapter author | Recreate the workflow or support a different harness. | Stable contracts, small adapter responsibilities, executable acceptance scenarios. |

The initial user is comfortable with git, a coding-agent harness, and a pull-request workflow. A nontechnical user who cannot assess repository setup or a code change is outside the initial target audience.

Representative jobs:

1. “When I describe a feature, help me settle its requirements and carry it through implementation and review.”
2. “When a run stops, show what is complete, what is waiting, and how to continue.”
3. “When my preferred harness changes, preserve the work and decisions already made.”
4. “Before publishing, show the change, the checks, the automatic decisions, and the remaining risks.”
5. “When building my own factory, give me a small working foundation and an ordered path to feature parity.”

## 5. Scope, product boundaries, and priorities

### Essential product boundaries

- One run owns one feature branch and one worktree.
- The orchestrator owns routing, state, user interaction, verification gates, and publication.
- Roles perform bounded work and return structured output.
- Every continuation starts from persisted inputs and files.
- The user approves before the branch is pushed and a PR is opened.
- The consuming repository's documented rules take precedence over factory defaults.
- The initial product runs locally through an existing harness and its authentication.

### Prioritisation

| Priority | Capability | Release expectation |
|---|---|---|
| P0 | Start, discover, inspect, pause, resume, and abort a run. | Required for the first useful release. |
| P0 | Isolated worktree; specification, plan, tasks, implementation, independent verification. | Required for an end-to-end feature. |
| P0 | Three core review lenses, a judge, bounded fixes, human approval, PR creation. | Required before using the factory to deliver real changes. |
| P0 | Durable decisions, structured role output, visible failures, checkpoints. | Required to make interruption and automation trustworthy. |
| P0 | One working adapter behind a portable interface. | Proves the product without multiplying integration work. |
| P1 | Full planning chain, automatic escalation, fast-mode relays, conditional UI/UX review, delta review. | Completes the current workflow's efficiency and review features. |
| P1 | A second adapter and tested cross-harness resume. | Proves the portability claim. |
| P1 | Conformance checks for installation, rendering, state, and role output. | Reduces maintenance and rebuild errors. |
| P2 | Additional adapters, richer usage reporting, convenience notifications. | Expand after the shared contracts are stable. |

P0, P1, and P2 are proposed build priorities. They do not describe which features are already present in this repository.

### Outside the initial product

Automatic merging or deployment; a hosted dashboard; organisation accounts and billing; multi-repository feature coordination; autonomous roadmap selection; an agent marketplace; arbitrary workflow builders; mandatory external databases; cloud coding-agent modes that cannot relay decisions; and automatic deletion of worktrees after publication.

These can be separate products or later extensions. None is necessary to prove a resumable feature-to-PR workflow.

## 6. Existing capability inventory

The following is the consolidated baseline a builder can recreate.

| Area | Baseline behaviour |
|---|---|
| Entry points | Start with a feature description; invoke without a description to discover runs; resume by branch or pending-run name. |
| Preflight | Identify the harness, repository and default branch; resolve required skills; establish build and test commands; offer missing setup. |
| Requirements | Interactive grilling records the settled feature and decisions before repository changes begin. |
| Isolation | Create a numbered feature branch and sibling worktree; use a matching specification directory. |
| Planning modes | Lite is the default; full adds clarify and grill-with-docs; serious lite-analysis findings trigger full planning. |
| Relay automation | Fast mode is on by default; eligible recommended answers are accepted and marked automatic. |
| Implementation | Execute tasks, commit completed work, resume from checkboxes, and hand over to a fresh role when context is low. |
| Verification | The orchestrator runs build and tests independently after implementation and fixes. |
| Pen references | Automatic cross-framework design-code mapping, persisted source/target context, scoped committed visual evidence, and mandatory mapping/runtime/fidelity gates independent of optional UI review. |
| Review | Security, code standards, and specification conformance always run; UI and UX are conditional on the diff. |
| Judgement | A separate judge verifies, deduplicates, and accounts for the reviewers' findings. |
| Repair | Up to two automatic verdict-driven fix rounds; later reviews normally inspect the fix delta. |
| Approval | Show evidence, advisories, unresolved findings, capability tier, and automatic answers; accept approval, changes, or abort. |
| Publication | Push and open a ready-for-review PR after approval; record its URL; retain the worktree. |
| Persistence | Versioned JSON state, stage checkpoints, saved relay answers, user-wait timeline, per-spawn ledger. |
| Distribution | Shared skill and roles; per-harness agent files; Python renderer; symlink installation and removal. |
| Harnesses | Adapter folders for Claude Code, OpenCode, Codex, GitHub Copilot, and ZCode. |

The baseline is primarily an instruction-driven orchestrator supported by small scripts. A documented gate is not automatically an executable enforcement mechanism. A rebuild should decide which invariants require code enforcement rather than relying entirely on a role following instructions.

## 7. End-to-end user experience

### Start and settle the feature

The user invokes the factory from the target repository. Preflight identifies missing dependencies before expensive agent work starts. The orchestrator asks about scope, expected behaviour, constraints, exclusions, and completion criteria. It batches independent questions and defers questions whose options depend on unresolved decisions.

Initial grilling always remains interactive. Its final summary names the chosen planning mode and becomes the feature brief once the user confirms shared understanding. Pending state and the brief live outside the repository until the worktree exists.

### Plan and build

The factory creates the branch and worktree, writes the initial checkpoint, and runs the selected specification chain. Each stage reads its inputs, produces its files or questions, and returns a structured envelope. Answers are persisted before the stage continues.

Analysis checks whether the specification, plan, and tasks agree and are implementable. Blocking findings trigger the bounded remediation rules. Implementation begins when the analysis condition is satisfied or the user explicitly chooses to proceed after a halt.

### Verify and review

The implementing role completes the tasks and runs the checks. The orchestrator repeats the documented build and test commands. Reviewers examine the relevant diff through separate lenses; the judge decides which findings are confirmed, advisory, or rejected. Confirmed blockers can enter the bounded repair loop.

### Pen design references (agreed 25 October 2026)

Runs creating, referencing, or updating a Pen design as an implementation reference follow the [approved contract](superpowers/specs/2026-10-25-pen-design-code-mapping-design.md) and the shared [mapping workflow](../core/skills/factory/references/design-code-mapping.md). It applies across frameworks, with separate [Avalonia translation/capture guidance](../core/skills/factory/references/design-code-mapping-avalonia.md). Resolve `pen-design` conditionally; discover actual backend capabilities instead of assuming stable IDs, revisions, or a file format.

Keep one permanent repository map, supporting multiple sources and every scoped node/component/instance through stable code anchors. Later update requests resolve a unique saved target and default to design → code. Preserve application behavior and obtain agreement before shared visual scope expands. Bootstrap existing implementations only within requested scope. Design-only tasks record source and targets until implementation exists.

Design governs visuals. Current build/runtime, mapping, and matching rendered-comparison evidence are mandatory independently of optional impeccable evaluation. Static desktop inspection contributes findings but cannot establish rendered fidelity. Concrete reference violations cite their approved requirement and evidence rather than being dismissed as styling opinions. Reuse current surveys/evidence and invalidate affected results when source/code/capture identity changes.

Mapping/visual findings share the same two automatic fix rounds. Missing prerequisites or exhausted repairs leave work partial/blocked; explicit scoped exceptions can permit proceeding while preserving unverified results. Fast mode and ordinary approval cannot infer an exception. Persist source context, scoped sources/exports/captures and comparison metadata under the feature's `factory/design/`, with references from the canonical map. Fresh roles and resumes receive these references and retain the original repair counter. Standalone Pen invocations are outside factory interception.

### Approve and publish

The user sees a decision package: what changed, what was checked, what was fixed, what remains unresolved, and which answers were accepted automatically. They can approve publication, request changes, or abort while retaining the work.

Approval permits the push and PR creation. It does not merge or deploy the change. A resumed publication stage checks for an existing PR before creating another.

### Resume

An empty invocation lists the current repository's saved runs with their stage, status, and last activity. Resume loads a compact digest, uses the recorded worktree, re-resolves harness-specific paths when needed, and continues the recorded stage. Already answered questions and completed tasks remain settled.

Cross-machine resume additionally requires the actual repository, branch, artifacts, and usable worktree paths to be available or restored. Sharing `FACTORY_HOME` alone does not transfer them.

## 8. Interaction and mode requirements

The baseline command surface uses `/factory` on most harnesses and `$factory` on Codex. A rebuild may choose another name but should preserve these semantics:

```text
factory <feature>                         start a run
factory                                   list runs for this repository
factory resume <branch-or-pending-name>    continue a saved run
factory <feature> --full --no-fast         use the full chain and manual relays
factory <feature> --stop-at review         pause before review
factory resume <branch> --full            change mode before restarting the stage
```

| Control | Required semantics |
|---|---|
| `--lite` / `--full` | Select the planning chain. Lite is the baseline default. Last explicit flag wins. |
| `--fast` / `--no-fast` | Enable or disable automatic recommendation acceptance in eligible relays. Fast is the baseline default. |
| `--stop-at <stage>` | Persist a pause before that stage starts. Resume executes the stage rather than immediately pausing again. |
| Invalid arguments | Name the invalid value and require correction; never silently ignore it. |

Fast mode never answers initial grilling, remediation questions that overturn settled decisions, halts, or final approval. A missing or ambiguous recommendation is not an answer. A pause at a stage omitted by the chosen chain does not trigger.

The baseline's valid stop points are `specify`, `clarify`, `grill-with-docs`, `plan`, `tasks`, `analyze`, `implement`, `review`, `approver`, and `pr`. A stop point is consumed when it triggers. Resume can set another stop point or change the planning/relay mode before execution continues.

Relay questions have stable stage-local IDs, context, meaningful choices where appropriate, a recommendation, and a separate rationale. Accept keyed choices, keyed custom answers, and keyed acceptance. Bare `accept` fills only unanswered recommendations; it preserves explicit answers. Ambiguous replies are clarified rather than assigned by guesswork.

**Recommendation:** Retain the current question semantics while treating emojis and exact typography as presentation details. Recreating the factory does not require reproducing decorative formatting before the workflow works.

## 9. Functional requirements and completion gates

| ID | Requirement | Completion or acceptance condition |
|---|---|---|
| FR-01 | Validate the run environment. | Repository, harness, skills, paths, and verification commands are known; missing prerequisites produce actionable guidance. |
| FR-02 | Persist the agreed feature. | Brief includes scope, exclusions, decisions, acceptance conditions, and chosen mode; initial confirmation is recorded. |
| FR-03 | Isolate the change. | Dedicated branch, worktree, and matching spec directory exist; later work targets that worktree. |
| FR-04 | Produce traceable planning artifacts. | Specification, plan, and tasks exist and reference the settled feature; analysis checks their consistency. |
| FR-05 | Support lite and full chains. | Lite runs specify → plan → tasks → analyze; full adds clarify and grill-with-docs before plan. |
| FR-06 | Escalate and remediate predictably. | Serious lite findings enter the full chain; remediation preserves settled decisions and follows explicit loop limits. |
| FR-07 | Execute tasks incrementally. | Each completed task is checked and committed; a fresh role continues unfinished work from durable progress. |
| FR-08 | Verify implementation independently. | Orchestrator observes successful build and test commands for the reviewed change; failures enter the retry or halt path. |
| FR-09 | Run appropriate review lenses. | Three core reviews run; UI/UX reviews are included when relevant; skipped reviews are disclosed. |
| FR-10 | Produce an accountable verdict. | Every submitted finding is represented exactly once as confirmed, advisory, or rejected, with evidence or a reason. |
| FR-11 | Bound automatic repair. | No more than two verdict-driven fix rounds; outstanding blockers remain visible when the limit is reached. |
| FR-12 | Obtain informed publication approval. | Approval package includes automatic decisions, check results, advisories, unresolved blockers, and review limitations. |
| FR-13 | Publish idempotently. | Approved branch is pushed; one PR is created or an existing PR is reused; URL is recorded. |
| FR-14 | Recover saved work. | Resume preserves answers and task progress; it restarts the recorded stage using current harness resolution. |
| FR-15 | Install through an adapter. | Core workflow is shared; generated agent files use the target harness format; removal preserves unrelated user files. |
| FR-16 | Expose useful run information. | Discovery and inspection return bounded routing context plus links to detailed evidence. |
| FR-17 | Preserve the decision audit. | Explicit and automatic answers remain available at final approval after stage relay state is cleared. This is a rebuild requirement addressing a baseline ambiguity. |

### Analysis and remediation policy

On the full chain, CRITICAL/HIGH analysis findings trigger remediation of all reported severities in place, followed by another analysis. Questions that would change a settled user decision return to the user; they are never guessed or auto-accepted. Re-enter clarification only when those questions require it. After two remediation loops, halt and let the user choose how to proceed.

MEDIUM/LOW-only analysis findings receive one remediation pass before implementation. They do not trigger another verification loop in the baseline. On lite, CRITICAL/HIGH findings switch to full, starting at clarify and re-deriving plan and tasks before analysis.

### Failure policy

A crashed, timed-out, or malformed role invocation gets one fresh retry with the failure context. A second failure halts. After failed orchestrator verification, one fresh implementation attempt receives the decisive failure output; continuing failure halts. These are separate limits from analysis loops and review fix rounds.

An implementation can yield `partial` when its context is low. It must leave finished work committed and identify the next unfinished task. A context handover is not evidence that the feature is complete.

### Review and approval policy

Reviewers inspect code and relevant surrounding context, report only evidenced defects in scope, and make no edits. The judge deduplicates overlapping findings and verifies their claims. Later rounds ordinarily review the fix delta against the prior verdict. Unexpected file changes without a declared reason escalate that round once to a full review.

The baseline permits the approver to see unresolved blockers after automatic fix rounds are exhausted. It therefore does not promise that every PR has a clean verdict. **Rebuild requirement:** any approval with unresolved blockers must explicitly acknowledge those blockers and preserve that acknowledgement with the published evidence.

User-requested changes return through fixing, verification, and review. They are not capped by the automatic fix-round limit.

## 10. Professional engineering discipline

Professional code should be **correct, readable, maintainable, secure, and fast enough for its requirements**. SOLID and Clean Code help when applied with judgement; no single architecture or coding style guarantees quality.

The shared [engineering reference](../core/skills/factory/references/engineering.md) is authoritative for roles. Its 25 October revision retains `ENG-1` through `ENG-11` and adds `ENG-12` through `ENG-31`. The 34 checklist items below map to those 31 rule IDs because existing rules already group related practices, such as SOLID. Preserve those IDs so earlier findings, overrides and saved reviews remain understandable.

### Practical quality checklist

| # | Practice | What the factory should expect | Rule |
|---|---|---|---|
| 1 | Understand the problem | Clarify expected behaviour, constraints, edge cases and acceptance criteria before coding. A solution to the wrong problem fails regardless of code quality. | ENG-12 |
| 2 | KISS — keep it simple | Choose the simplest solution meeting the requirements; favour straightforward code over unnecessary cleverness. | ENG-10 |
| 3 | YAGNI — build demonstrated needs | Add capabilities when needed; avoid speculative features, configuration and extension points. | ENG-10 |
| 4 | DRY — one source of business knowledge | Reuse shared rules and suitable existing implementations. Similar-looking code can represent different concepts; premature abstraction can create coupling. | ENG-6 |
| 5 | Separation of concerns | Keep business rules, presentation, persistence and integrations distinct enough to change safely. A concern need not become a separate service or project. | ENG-13 |
| 6 | High cohesion, low coupling | Put related behaviour together and minimise unrelated dependencies so a feature requires understanding a limited part of the system. | ENG-14 |
| 7 | S — single responsibility | Give a module one coherent responsibility and main reason to change. This does not require one method per class. | ENG-8 |
| 8 | O — open/closed | Extend stable behaviour where variation is expected; avoid elaborate extension mechanisms for hypothetical changes. | ENG-8 |
| 9 | L — substitution | A replacement implementation or subtype honours the behavioural contract its callers expect. | ENG-8 |
| 10 | I — focused interfaces | Give consumers the operations they need without dependencies on unrelated operations. | ENG-8 |
| 11 | D — dependency inversion | Keep business policy independent of infrastructure details. Use dependency injection where helpful; interfaces everywhere are unnecessary. | ENG-8 |
| 12 | Encapsulation and explicit contracts | Hide representation and preserve valid state; make inputs, outputs, errors, ownership and side effects clear. | ENG-15 |
| 13 | Composition when inheritance adds complexity | Assemble collaborating components; use inheritance when the relationship and behavioural contract fit or the framework requires it. | ENG-9 |
| 14 | Meaningful, consistent names | Communicate intent and domain meaning using established project vocabulary and language conventions. | ENG-7 |
| 15 | Focused, readable functions | Keep control flow understandable and reduce unnecessary nesting. There is no universal maximum line count. | ENG-7 |
| 16 | Useful comments and documentation | Explain reasoning, constraints, surprising behaviour and public contracts; update documentation when behaviour changes. | ENG-7 |
| 17 | Types that express valid states | Use meaningful domain types, enums and explicit optional values where practical; prevent invalid combinations. | ENG-16 |
| 18 | Controlled mutation and shared state | Prefer local state and immutable values where practical; make side effects visible and account for concurrent access. | ENG-9 |
| 19 | Deliberate error handling | Distinguish expected failures from programming defects, preserve diagnostics, surface failures, and release resources reliably. | ENG-17 |
| 20 | Behaviour and boundary tests | Select unit, integration and end-to-end tests for the risk and behaviour; cover important edge and failure paths. Coverage percentage alone proves little. | ENG-1 |
| 21 | Trustworthy tests | Keep tests deterministic, readable and able to detect meaningful regressions. Mock boundaries when useful and verify real interactions through integration tests. | ENG-18 |
| 22 | Incremental refactoring | Improve structure in small behaviour-preserving steps, remove dead code and obsolete abstractions, and add regression tests for consequential bugs. | ENG-19 |
| 23 | Measured performance | Establish a baseline, profile representative workloads, identify bottlenecks and compare after optimisation. Investigate CPU, waiting, memory, storage or network as relevant. | ENG-20 |
| 24 | Appropriate algorithms and data structures | Consider time/space complexity and data growth; avoid redundant work and unbounded loading when bounded processing suffices. | ENG-21 |
| 25 | Deliberate database/network access | Watch for N+1 queries, round trips, missing indexes, oversized payloads and unbounded results; use query plans and realistic data for relevant changes. | ENG-22 |
| 26 | Deliberate concurrency and caching | Bound parallelism, support cancellation where appropriate and protect shared state. Define cache freshness, invalidation, size and failures; async does not automatically accelerate CPU work. | ENG-23 |
| 27 | Failure and resource limits | Use suitable timeouts, bounded queues/requests/memory, limited transient retries with backoff, and protection against duplicate consequential effects. | ENG-24 |
| 28 | Everyday security | Validate untrusted input, parameterise queries, encode output for context and enforce trusted-boundary authorisation. Protect secrets and use established security libraries. | ENG-25 |
| 29 | Data integrity | Use appropriate invariants, constraints and transactions; consider concurrent updates, duplicate requests, partial failures and schema/API compatibility. | ENG-26 |
| 30 | Careful dependency management | Prefer suitable standard-library or existing features; assess maintenance, security, licensing, size and operations. Track versions and preserve reproducible builds. | ENG-27 |
| 31 | Automated quality checks | Reuse formatters, linters, type checks, tests and relevant CI security checks; keep building and testing repeatable with minimal setup. | ENG-28 |
| 32 | Reviewable changes | Keep commits and PRs focused; explain the problem, resulting behaviour and verification. Review correctness, design, complexity, security and maintainability. | ENG-29 |
| 33 | Observable production behaviour | Use relevant structured logs, metrics and tracing; for services consider latency, traffic, errors and saturation. Protect sensitive telemetry. | ENG-30 |
| 34 | Safe delivery and maintenance | Consider rollout, rollback, configuration, migrations and compatibility; record significant tradeoffs and prioritise technical debt by actual impact. | ENG-31 |

SOLID primarily concerns object-oriented design. Apply its ideas where they help the language and system being changed. Be careful with “always”: universal interfaces, complete deduplication, maximum coverage, compulsory patterns and microservices can increase maintenance cost. Apply each practice to a concrete problem and verify that it improves the result. Relevant risks belong in the plan; this checklist does not require 34 new artifacts or unrelated infrastructure for every feature.

Optional background: [Fowler on YAGNI](https://martinfowler.com/bliki/Yagni.html), [Google's review guidance](https://google.github.io/eng-practices/review/reviewer/looking-for.html), [Gregg's performance methodology](https://www.brendangregg.com/methodology.html), [OWASP's secure review checklist](https://cheatsheetseries.owasp.org/cheatsheets/Secure_Code_Review_Cheat_Sheet.html), [Fowler on CI](https://martinfowler.com/articles/continuousIntegration.html), and [Google SRE on monitoring](https://sre.google/sre-book/monitoring-distributed-systems/).

### Factory process and repository precedence

The quality checklist sits alongside the existing delivery process:

- `ENG-1` requires test-first work for changed behaviour; `ENG-2` records test evidence and `ENG-3` keeps tests and implementation together in one task commit.
- `ENG-4` requires planned public test seams; `ENG-5` permits only declared documentation/configuration exemptions with reasons. A missing required seam or an unavailable required test runner stops the role.
- `ENG-6` requires a bounded reuse search; `ENG-10` requires a reason for each new file, abstraction or dependency.
- `ENG-11` gives the consuming repository's documented rules precedence and records each override in the plan.

The accepted commit-body forms remain:

```text
Red: <test name> failed as expected
Red: not applicable - <existing test> already covers this
```

### Review enforcement

A design or style judgement alone, including guidance under `ENG-7` through `ENG-10`, produces a finding no higher than MEDIUM and never blocks a verdict-driven fix round. The user can request it at approval. Similar-looking code alone is not proof of a DRY violation, and duplication is not automatically HIGH.

Concrete correctness, security, integrity, resource-limit, documented-contract or stated-performance defects retain the severity justified by their consequences. Reviewers cite the violated requirement or applicable rule and provide evidence; an architectural preference neither establishes nor excuses a defect. Test-first, seam and commit-evidence requirements retain their existing enforcement.

Keep product-level verification separate from recreating every enforcement detail on day one. The P0 release needs meaningful tests and independent verification; exact engineering-rule parity can be completed as a named follow-on before claiming full baseline compatibility.

## 11. Architecture and responsibility boundaries

### Recommended starting architecture

Recreate the existing portable, instruction-driven core with small deterministic helpers. Prove one adapter and one complete run first. Add enforcement to the mechanical operations that repeatedly cause failures. A new distributed orchestration service is unnecessary for the initial product.

| Module | Owns | Must remain outside its responsibility |
|---|---|---|
| Orchestrator | Stage selection, role invocation, user relays, gates, state ownership. | Harness-specific tool names and specialist implementation work. |
| Role definitions | Bounded specialist work, inputs, outputs, done conditions. | Spawning other roles, publication, direct user interaction. |
| Run-state helpers | Discovery, inspection, validation, and any explicitly added state operations. | Product judgement or hidden mode changes. |
| Protocol references | Envelope, question, finding, verdict, state, and engineering contracts. | Separate copies of harness behaviour. |
| Harness adapter | Tool mappings, capabilities, skill discovery, model/access mapping, install locations. | Duplicating the workflow or review policy. |
| Renderer and installer | Produce native agent files and install/remove factory-owned links. | Editing the consuming repository's work. |
| External tools | Git isolation, SpecKit artifacts, repository checks, GitHub PR operations. | Owning the factory's run state or stage order. |

### Six portable operations

| Operation | Contract |
|---|---|
| `SPAWN(role, inputs)` | Execute one role from explicit inputs in a fresh context and collect its structured output. |
| `SPAWN_PARALLEL(roles)` | Execute independent roles concurrently when supported; collect every output before judgement. |
| `ASK(questions)` | Present decisions to the user and wait for a valid answer. |
| `NOTIFY(text)` | Notify when available; otherwise do nothing. |
| `RESOLVE(name)` | Map a logical skill/command name to the active harness's readable instruction file. |
| `SHELL(command)` | Execute a command in the intended repository or worktree. |

Keep harness paths, tool names, and model identifiers inside adapters. Pass the installed factory directory to roles so references resolve consistently. Use JSON configuration and a small Python standard-library renderer, matching the current implementation rather than the older plan's YAML sketch.

### Roles

| Role | Access intent | Main output |
|---|---|---|
| Spec-builder | Write planning artifacts | One stage's files, questions, or analysis summary. |
| Code-build | Write implementation | Completed tasks and verification status. |
| Security reviewer | Read | Evidenced security findings. |
| Code-standards reviewer | Read | Findings against documented repository and engineering rules. |
| Spec-conformance reviewer | Read | Findings against the spec, plan, tasks, and required evidence. |
| UI reviewer | Read | Visual, accessibility, and UI-quality findings on relevant changes. |
| UX reviewer | Read | Flow, state, interaction, and copy findings on relevant changes. |
| Review judge | Read | Verified, deduplicated verdict with complete finding accounting. |
| Fixer | Write | Confirmed fixes or requested changes, with updated checks and commit evidence. |

The baseline maps spec-builder and judge to a `deep` model tier and the other roles to `standard`. These are configurable labels, not permanent model names. Adapter conformance must establish whether read-only access is technically enforced or only instructed.

### Capability tiers

1. **Native subagents:** separate role contexts through the harness's agent support.
2. **Headless subprocesses:** roles run through noninteractive harness processes; results are collected from their output.
3. **Inline:** the orchestrator performs the roles sequentially in its own context.

All tiers follow the same output contracts. Tier 3 provides weaker review independence and must be disclosed. A concurrency cap should queue independent reviewers rather than silently omit them. Supporting the fallback contract is distinct from proving every adapter's implementation of it.

### Dependencies and configuration

| Dependency | Purpose and when needed |
|---|---|
| Coding-agent harness with a conforming adapter | Executes the orchestrator and roles. Required to run the factory. |
| Git and a usable repository | Creates branches, worktrees, diffs, and checkpoints. Required before a run starts. |
| Python 3 | Runs the renderer and state CLI without third-party Python dependencies. |
| SpecKit in the consuming repository | Supplies the specification, planning, task, and implementation instructions. Preflight offers setup when absent. |
| `grilling`, `domain-modeling`, and `pr` skills | Supply the baseline interview, terminology/decision capture, and PR-writing workflows. Resolve them before expensive work. **Required**, every run. |
| `ponytail` and `tdd` skills | Supply reuse-first simplification and test-driven implementation technique for code-writing and fixing turns, bounded by the factory's own engineering rules and plan-time seam confirmation. Resolve before any run commits to code delivery. **Required**, every run that reaches delivery. |
| `brainstorming` skill | Supports the idea-exploration path (intake intent: exploration). **Conditional**: resolve only on that path; never on the feature path. |
| `impeccable` skill | Supports the UI review lens; resolve only when needed and disclose a skipped UI review. **Conditional**: resolve only on a UI diff. |
| `pen-design` skill and supported backend | **Conditional**: Pen implementation references activate persistent mapping and mandatory fidelity checks; unavailable capabilities produce explicit gaps, not assumed success. |
| Authenticated `gh` and a writable remote | Support GitHub repository lookup and approved PR publication. Confirm publication readiness before the final gate. |
| Repository build/test tools | Execute the recorded verification commands. A missing or broken required tool is an actionable setup failure. |

Use `FACTORY_HARNESS` to select an adapter explicitly and `FACTORY_HOME` to select shared local state/configuration storage. User configuration can override the `deep` and `standard` model mappings per harness. Show the effective configuration after applying overrides; do not require one provider's model identifiers in the portable core.

## 12. Persistence, contracts, and recovery

### Files and locations

```text
factory/
  DESIGN.md
  core/
    skills/factory/
      SKILL.md
      bin/factory
      references/{state,protocol,findings,verbs,engineering}.md
    roles/*.md
  adapters/<harness>/{harness.md,adapter.json}
  tools/render.py
  install.sh
  dist/<harness>/{skill,agents}/

target-worktree/
  specs/<feature-branch>/
    spec.md
    plan.md
    tasks.md
    factory/
      brief.md
      state.json
      analyze-<pass>.md
      remediation-<pass>.md
      design/{context.json,comparison.json,scoped-sources-and-captures}
      reviews/round-<n>/*.json
  docs/design-code-map.json    # default canonical project map; reuse an existing equivalent
```

Pending runs and user configuration live under `${FACTORY_HOME:-~/.factory}`. Detailed specifications may introduce additional research or design artifacts when relevant. A proposed durable decision archive can be embedded in state or stored beside it; choose one authoritative representation.

### Minimum durable state

Store schema version; feature and repository identity; branch, base and worktree; spec directory; current harness; stage and status; mode and stop point; resolved skills and commands; open questions and answers; durable decision history; analysis and review counters; checkpoints; wait timeline; invocation ledger; halt reason; and PR URL.

The baseline status vocabulary is `running`, `waiting_user`, `paused`, `halted`, `aborted`, and `pr-open`. Stages and statuses are separate: for example, a run can be paused before review or halted during implementation.

The baseline stage vocabulary is `grill`, `worktree`, `specify`, `clarify`, `grill-with-docs`, `plan`, `tasks`, `analyze`, `remediate`, `implement`, `verify`, `review`, `fix`, `approver`, and `pr`. A halted or aborted run needs an explicit user decision before restarting; ordinary resume must not silently reverse an abort.

### Role output contracts

Ordinary roles end with exactly one final fenced JSON envelope containing status, stage, summary, written-file paths, questions, and relevant analysis/error information. Status is `done`, `needs_input`, `partial`, or `failed`; `partial` is for implementation handover.

Reviewers return findings with an ID, severity, blocking judgement, location, defect statement, evidence, and concrete fix. The judge returns `pass` or `fix`, confirmed blockers, advisories, rejected findings and reasons, plus an optional delta-review escalation.

**Recommendation:** Validate required fields and allowed values mechanically before accepting an output or advancing a stage. Treat malformed output as the existing retryable failure. Do not infer successful completion from persuasive prose around an invalid envelope.

### Recovery invariants

- Every stage transition records durable state and a checkpoint.
- Save each valid answer immediately, including partial replies to a batch.
- Resume an open question round rather than creating duplicate questions.
- Restart spec stages with saved answers and existing files; continue implementation from completed task evidence.
- Preserve and inspect interrupted work before changing it; ambiguous ownership of dirty files requires resolution.
- Re-resolve skills after a harness change; verify or rebind paths after a machine change.
- Check existing branches, worktrees, commits, and PRs before recreating external effects.
- Retain work on abort and leave cleanup explicit.

**Recommendations:** Use atomic state-file replacement, validate the schema before writing, and prevent two orchestrators from mutating the same run concurrently. Keep the first implementation local and file based; a database is unnecessary until actual concurrency or hosting requirements justify it.

## 13. Efficiency requirements and measurement

### Preserve the baseline's useful optimisations

| Mechanism | Why it helps | Constraint |
|---|---|---|
| Lite planning by default | Avoids repeating clarification for an already settled small feature. | Escalate serious analysis findings; keep full mode available. |
| Frontier question batches | Reduces user waits without asking dependent questions prematurely. | Preserve IDs and explicit answers. |
| Fast-mode relays | Removes routine waits. | Keep automatic choices visible and vetoable; protect user-owned decisions. |
| Fresh roles with scoped inputs | Contains context growth and makes handover normal. | Persist everything needed by the next invocation. |
| Compact discovery/resume digest | Avoids loading growing state histories merely to route a run. | Link to detailed evidence rather than discarding it. |
| Conditional UI/UX review | Avoids irrelevant specialist work on backend changes. | Detect UI-related paths and disclose skipped reviews. |
| Parallel independent reviews | Reduces review elapsed time. | Respect concurrency limits and collect every required review. |
| Delta review after fixes | Avoids rereading the entire original change. | Escalate unexplained scope expansion to full review. |
| Bounded repair loops | Prevents unattended repetition. | Surface unresolved work and require a human next step. |

The baseline also flags oversized artifacts during analysis: specification above 3,000 words, plan above 2,000, tasks above 2,500. These are concise-input guidelines, not measures of specification quality. A rebuild should preserve necessary acceptance criteria when trimming artifacts.

### Metrics

| Metric | Definition |
|---|---|
| End-to-end elapsed time | Run start to approval-ready, and separately to PR opened. |
| Human wait | Time waiting for replies, plus the number of waits; it is not a measure of active human effort. |
| Aggregate agent time | Sum of all invocation durations, including overlapping invocations. |
| Agent elapsed time | Union of invocation time intervals; overlapping work is counted once. |
| Usage | Input/output estimates and reported usage, clearly distinguished. |
| Rework | Analysis loops, fix rounds, failure retries, and user-requested change rounds. |
| Recovery overhead | Time and repeated work needed to continue an interrupted run. |
| Delivery quality | Accepted requirements covered; unresolved blockers; defects found after approval. |

**Recommendation:** Persist invocation start/end times so aggregate agent effort and agent elapsed time can be reported correctly. Do not subtract aggregate parallel-agent durations from wall time to calculate overhead. If intervals overlap user waits, compute interval unions/differences rather than assuming all categories are additive.

The baseline's word-count usage estimate is a proxy for named inputs and selected outputs. It does not represent complete billable usage or hidden context. Currency reporting requires actual usage and a dated pricing configuration; estimated tokens must never be presented as an invoice.

### Proposed efficiency acceptance targets

These are initial targets to validate, not observed performance claims:

1. No accepted answer is asked again after an ordinary pause or crash.
2. A committed completed task is not reimplemented on resume.
3. Non-UI fixtures do not spawn UI or UX roles.
4. The routing digest excludes completed relay rounds and full historical ledgers while retaining the next action.
5. A simple-feature lite run uses fewer specification-stage invocations than the equivalent full run.
6. Every comparison of modes records the same acceptance criteria and any quality regression.

Benchmark the same small backend feature and UI feature under fixed repository revisions, harness/model configurations, and check commands. Repeat each condition enough to report a median and range. Set a percentage savings target only after measuring the baseline and reviewing output quality.

## 14. Known ambiguities and recommended resolutions

These are source-level observations relevant to a rebuild, not runtime failures reproduced during this work. Two of them are settled by 007-stabilise-factory: the audit row (settled answers now live in the append-only `decisions` list of schema v4, and the approver reads its veto list from there — relay is only temporary routing data) and the totals row (effort is interval union in `factory_cli/totals.py`; parallel durations are never summed, and human + agent cannot exceed wall clock by construction). The state CLI row is now half-settled: every state mutation goes through the single writer with validation, atomic writes and commit; locking, output validation and transition gates land with M2.

| Observation | Implication | Recommended resolution |
|---|---|---|
| Stage checkpoints clear `relay`, while the approver is told to list automatic answers from `relay`. | The specified audit trail can lose earlier automatic decisions. | Preserve completed decisions in a durable archive, with stage, question, answer, origin, and time. Treat active relay state as temporary routing data. |
| The totals helper sums invocation durations and subtracts them from wall time. | Parallel reviewers make that sum unsuitable as an elapsed-time component. | Separate aggregate effort from interval-based elapsed time as defined above. |
| README and some harness notes describe model inheritance, while inspected Codex/ZCode adapter JSON files pin models. | Installation behaviour can differ from the written expectation. | Make adapter configuration authoritative and expose effective models after user overrides. Generate or check the documentation against it. |
| Cross-harness resume uses saved absolute repository/worktree paths. | Portability between harnesses on one machine does not automatically establish portability between machines. | Validate paths and support an explicit restore/rebind flow before claiming cross-machine resume. |
| Most orchestration rules are instructions. The state CLI currently implements read-only discovery and inspection. | Atomic mutation, locking, output validation, and transition enforcement should not be assumed to exist. | Add narrowly scoped deterministic helpers for proven failure points; keep judgement in roles. |
| The original migration plan describes one eventual implementation commit; current runs use stage checkpoints and task commits. | Reusing the old migration instruction would conflict with the run's recovery design. | Distinguish development history for migrating the factory from checkpoint policy for features produced by it. Preserve the latter. |

Keep these decisions explicit in a new implementation. For changes to this repository, update `DESIGN.md` first and follow its constitution rather than treating this brief as an automatic override.

## 15. Rebuild strategy and trade-offs

| Approach | Benefit | Cost | Fit |
|---|---|---|---|
| Portable skill and roles with small helpers — recommended | Closest to the existing product; reuses harness execution and authentication; low initial surface area. | Some reliability depends on instruction following until critical mechanics are enforced. | Individual developers and local delivery workflows. |
| Full deterministic orchestration engine | Stronger transition enforcement and central scheduling. | Requires a new runtime, integration layer, and larger maintenance commitment. | Later, if measured recovery/concurrency problems justify it. |
| Hosted service and dashboard | Central visibility and shared execution. | Adds tenancy, infrastructure, credentials, storage, and operational concerns. | A separate team/hosted-product initiative. |

Build the recommended approach around stable contracts. The important early seam is between **portable workflow policy** and **harness execution**, followed by the boundary between **agent judgement** and **mechanical state operations**.

Efficiency comes from a working vertical slice, reusable contracts, and measured improvements. Implementing five adapters before one reliable run multiplies integration uncertainty.

## 16. Ordered build plan

Each milestone has a reviewable deliverable and an exit condition. These are delivery milestones for recreating the factory, distinct from stages inside a factory run. No calendar estimate is implied.

| Milestone | Build | Exit condition |
|---|---|---|
| M0 — Contracts | Product boundary, stage/status table, state schema, envelopes, findings/verdicts, adapter interface, acceptance fixtures. | A builder can describe every next action, pause, failure, and output without relying on unstated conversation. |
| M1 — One harness, one isolated run | Preflight, pending brief, worktree, start/list/show, checkpoints, basic resume. | Create a run, pause it, restart in a new session, and recover the same worktree and decisions. |
| M2 — Feature to tested implementation | Lite specification chain, analysis, tasks, implementation handover, independent checks. | A small real feature satisfies its acceptance criteria; interruption during implementation resumes correctly. |
| M3 — Reviewed and approved delivery | Three reviewers, judge, bounded fixes, durable decision audit, approval, idempotent PR creation. | Evidence reaches the approver; rejection publishes nothing; approval creates one PR. This completes P0. |
| M4 — Adaptive efficiency and UI parity | Full chain and escalation, fast-mode eligibility, conditional UI/UX review, delta review, engineering-rule parity, corrected metrics. | Failure, advisory, UI, escalation, and override fixtures pass; compare lite/full on the same feature. |
| M5 — Portability proof | Second adapter, shared skill distribution, configuration, capability disclosures, adapter conformance. | Start on one harness, stop before implementation, and finish through the other without repeating settled decisions. |
| M6 — Broader distribution | Remaining adapters, canonical render checks, install/remove checks, contributor guide, effective-configuration display. | Each advertised adapter passes the same conformance suite and its own end-to-end acceptance run. |

Until full-chain escalation is implemented at M4, a serious analysis finding must halt with guidance. An intermediate release must never continue past a blocker merely because its escalation path is not built yet. Publish a supported-capability list for each milestone rather than claiming full baseline parity early.

### Rules that keep the rebuild small

1. Start with Markdown instructions, JSON artifacts, git, and Python standard-library helpers.
2. Reuse SpecKit rather than recreating its document-generation workflow.
3. Use the existing harness's execution and user authentication.
4. Implement one shared skill; generate only native role files and necessary entry points.
5. Put new helper code around measured mechanical failure points.
6. Keep one source for every contract and engineering rule.
7. Add each adapter as a conformance exercise, without copying the workflow.
8. Keep generated distribution files mechanically reproducible; never edit them manually.
9. Preserve user work and existing unrelated files during installation, recovery, and removal.
10. Defer convenience UI and hosting until the local workflow proves useful.

## 17. Acceptance scenarios and release gates

Run deterministic contract/helper checks separately from real agent-driven acceptance runs. A rendered file passing a structural check does not establish that a harness can execute the workflow correctly.

| ID | Scenario | Required evidence |
|---|---|---|
| AT-01 | Small backend feature | Lite run reaches approval with completed tasks, successful checks, three core reviews, and a verdict. |
| AT-02 | Feature with UI changes | Both UI and UX reviews are included; any missing UI-review dependency or skipped review is disclosed. |
| AT-03 | Serious lite-analysis finding | State switches to full; clarify and grill-with-docs run; plan/tasks are updated before analysis repeats. |
| AT-04 | Partial relay reply and restart | Explicit answer survives; only unanswered questions reappear with original IDs and positions. |
| AT-05 | Fast-mode decision audit | Eligible answers are automatic; protected questions reach the user; all automatic answers remain visible at approval after checkpoints. |
| AT-06 | Stop before review | Review does not start; a fresh-session resume starts review once. |
| AT-07 | Interrupted implementation | Completed tasks remain complete; interrupted changes are inspected and preserved or resolved; work continues at the correct task. |
| AT-08 | Broken verification | Actual command/output is recorded; one recovery attempt is made; continuing failure halts without publication. |
| AT-09 | Malformed role output | Output fails validation, a fresh retry receives the error, and repeated failure halts. |
| AT-10 | Overlapping review findings | Judge merges duplicates and accounts for every finding ID exactly once. |
| AT-11 | Scope expansion during fixing | Unexplained additional files trigger one full-review escalation. |
| AT-12 | Two fix rounds still leave blockers | Automatic fixing stops; unresolved blockers are shown; any publication approval acknowledges them explicitly. |
| AT-13 | Advisory engineering finding | It remains advisory and untouched by verdict-driven fixing; an explicit user change request can have it fixed. |
| AT-14 | Abort or request changes | Abort retains work and creates no PR; changes rerun checks and review before another approval. |
| AT-15 | Interrupted PR creation | Resume discovers an existing PR and records its URL; no duplicate PR is created. |
| AT-16 | Cross-harness resume | Another adapter resolves its own skills and continues the saved branch, artifacts, answers, and mode. |
| AT-17 | Restricted capability tier | Sequential/inline behaviour is correct; review limitations appear in the approval package. |
| AT-18 | Installation and removal | Factory-owned links are installed/removed; unrelated user files remain; effective models and paths are inspectable. |
| AT-19 | Canonical rendering | Every advertised adapter renders; expected files exist; shared skill trees match; generated distribution has no tracked or untracked drift. |
| AT-20 | State safety | Interrupted write leaves a valid prior/new state; invalid schema does not advance; a second orchestrator cannot mutate the same run concurrently. Recommended helper capabilities must be implemented before claiming this gate. |
| AT-21 | Consuming-repository rules | A documented override is recorded and respected; an unavailable required test runner stops behaviour-changing work. |
| AT-22 | Pen reference implementation/update | Scoped source-qualified mapping and actual matching runtime/reference evidence establish fidelity; a green build/full map alone cannot pass. Fresh roles/resume retain source context and shared repair count. |
| AT-23 | Missing Pen evidence or exhausted design repair | Missing/failed gates remain partial/blocked independently of optional UI review. Only an explicit scoped exception permits proceeding; approval/fast mode cannot imply one. |

At M3, prove AT-01, AT-04, AT-07 through AT-10, AT-12 through AT-15, and the relevant installation/contract checks. Before claiming full current-feature parity, prove the remaining workflow scenarios. Before advertising an adapter as supported, execute its adapter-specific checks and a small real feature through approval.

Use a disposable repository for publication acceptance. Ordinary adapter validation should stop at the approver, matching the current design's validation plan. Keep the branch revision, harness configuration, command results, and acceptance record together so a later maintainer can reproduce the result.

## 18. Operational requirements and risks

| Requirement or risk | Product response |
|---|---|
| Harness formats and tools change | Keep adapters small; validate against the actual installed harness; rerun conformance before advertising support. |
| Prompts report success without successful checks | Require structured output and independent command results tied to the reviewed revision. |
| Reviewers share blind spots | Use separate contexts where supported, complementary lenses, an accountable judge, and disclosed capability limits. |
| Automatic answers introduce unwanted assumptions | Restrict eligibility, retain the original recommendation and accepted answer, and expose them at approval. |
| State corruption or simultaneous resume | Atomic writes, schema validation, checkpoint recovery, and a single active writer per run. |
| Repeated processing increases cost | Limit retries, analysis loops, and automatic fix rounds; record invocation counts and causes. |
| Local paths or configuration prevent portability | Validate paths, re-resolve logical skills, display effective settings, and restore/rebind deliberately. |
| Generated files diverge from source | Render canonically and check both modified and untracked distribution files. |
| Instructions claim access restrictions the harness cannot enforce | State whether permissions are enforced or instructed; never imply an isolation guarantee that is absent. |
| Logs or checkpoints contain sensitive data | Keep credentials out of run artifacts and PR content; retain only task-relevant diagnostics. |

Operational requirements are local-first storage, actionable errors, bounded retries, preserved work, inspectable configuration, and explicit publication authority. Remote services beyond the chosen harness and GitHub are not required by the product architecture.

## 19. Reusable build brief for a developer or coding agent

The following can serve as the opening instruction when recreating the factory. Supply this document with it; the paragraph is an index into the requirements, not a substitute for them.

> Build a local-first software factory that turns a feature request into an isolated, specified, implemented, independently verified, reviewed change with human approval before push and PR creation. Follow this product brief's P0 scope and M0–M3 order first. Use one orchestrator, stateless bounded roles, versioned file-based run state, git worktrees, SpecKit artifacts, structured role envelopes, three core review lenses, a separate judge, bounded repair, and idempotent publication. Keep workflow policy harness neutral behind SPAWN, SPAWN_PARALLEL, ASK, NOTIFY, RESOLVE, and SHELL, starting with one adapter. Preserve explicit and automatic decisions across checkpoints and resume. Keep documented repository rules authoritative. Implement and demonstrate the relevant acceptance scenarios before adding the full planning chain, fast-mode automation, UI/UX and delta review, or a second adapter. Use Markdown, JSON, and small standard-library helpers until a concrete requirement justifies more infrastructure. Report which requirements are implemented, which acceptance scenarios passed, and which limitations remain.

### Handover package for a successful recreation

- Product brief and agreed design decisions.
- Working orchestrator, roles, protocol references, and one or more tested adapters.
- Renderer/installer and a reproducible distribution.
- State schema, resume instructions, and effective configuration documentation.
- One completed sample feature with its brief, spec, plan, tasks, check results, findings, verdict, and approval evidence.
- Acceptance results tied to repository revisions and harness configurations.
- A concise list of unsupported capabilities and deliberate differences from the baseline.

## 20. Source map and requirement traceability

| Source | Use in this brief |
|---|---|
| [README](../README.md) | User-facing installation, entry points, modes, resume, requirements, and repository layout. FR-01, FR-05, FR-14–FR-16. |
| [Harness-agnostic design and plan](<Harness-agnostic factory design and plan.md>) | Portable-core rationale, stateless stages, neutral verbs, capability tiers, historical migration sequence. FR-14–FR-15. |
| [DESIGN](../DESIGN.md) | Authoritative current workflow, gates, review/repair limits, approval, PR policy, telemetry, and validation plan. FR-01–FR-16. |
| [CONTEXT](../CONTEXT.md) | Domain vocabulary and engineering concepts. |
| [Repository constitution](../.specify/memory/constitution.md) | Design precedence, portable core, stateless roles, generated-distribution policy, simplicity. |
| [Orchestrator skill](../core/skills/factory/SKILL.md) | Concrete routing, preflight, stage order, escalation, verification, review, approval, and failure instructions. FR-01–FR-16. |
| [State reference](../core/skills/factory/references/state.md) | Versioned state, checkpoints, discovery, resume, relay lifecycle, metrics. FR-14, FR-16; informs recommended FR-17. |
| [Protocol reference](../core/skills/factory/references/protocol.md) | Role envelopes, question batching, answer semantics, fast-mode exceptions, user-wait timeline. FR-02, FR-06, FR-17. |
| [Findings reference](../core/skills/factory/references/findings.md) | Reviewer evidence, finding accounting, severity ceilings, delta/full escalation. FR-09–FR-12. |
| [Engineering reference](../core/skills/factory/references/engineering.md) | ENG-1–ENG-31: factory process plus the 34-practice quality checklist, proportionate application, exemptions and repository precedence. FR-04, FR-07–FR-10. |
| [Portable verbs](../core/skills/factory/references/verbs.md) | Adapter interface and capability tiers. FR-14–FR-15. |
| [Role definitions](../core/roles/) | Role boundaries, artifact budgets, implementation handover, review and fixing expectations. FR-04–FR-11. |
| [Adapters](../adapters/), [renderer](../tools/render.py), [installer](../install.sh) | Present integration/configuration formats, generated files, model mappings, and link handling. FR-15. |
| [State CLI](../core/skills/factory/bin/factory) | Actual read-only discovery, digests, and current totals calculation. FR-16. |
| [Tracked distribution decision](../docs/adr/0005-the-rendered-distribution-is-tracked-in-git.md) | Canonical render environment and distribution drift gate. AT-19. |

FR-17, atomic mutation/locking, corrected elapsed-time accounting, explicit unresolved-blocker acknowledgement, and the proposed build priorities are recommendations in this brief. They must not be mistaken for completed changes to the existing factory.
