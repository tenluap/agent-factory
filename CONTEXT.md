# Software Factory

This repository builds `/factory`: one orchestrator skill plus the role prompts and per-harness adapters it runs on. The language below is the vocabulary of a factory run and of the engineering discipline its roles follow.

## Language

**Factory run**:
One pass of the orchestrator loop over a single feature, from grilling to an open PR, on its own branch and worktree.
_Avoid_: session, job, pipeline

**Orchestrator**:
The agent session running the `/factory` skill: it owns the run's state, spawns every role and is the only participant that talks to the user.
_Avoid_: driver, coordinator, main agent

**Role**:
A prompt the orchestrator spawns an agent from, named by its job (spec-builder, code-build, fixer, reviewers, judge).
_Avoid_: agent type, persona, worker

**Stage**:
One named step of the run that a role performs in a single spawn (specify, clarify, grill-with-docs, plan, tasks, analyze, remediate, implement, review, fix).
_Avoid_: step, phase, task

**Harness**:
The agent product a run executes in (Claude Code, OpenCode, Codex, Copilot, ZCode).
_Avoid_: platform, client, host

**Adapter**:
The per-harness translation of the neutral verbs and install locations into that harness's mechanisms.
_Avoid_: plugin, backend

**Rendered distribution**:
The per-harness skill and agent files produced from the core and the adapters, tracked in the repository and installed from it.
_Avoid_: build output, artifacts, dist

**Per-user render**:
A harness tree rendered for one user's factory home with their personal model overrides merged, distinct from the tracked rendered distribution; what their harness directories link to.
_Avoid_: personal dist, user build, local copy

**Effective model report**:
The per-role list of model ids the installed agents will actually use, resolved for one user's factory home.
_Avoid_: models dump, config summary, model list

**Relay**:
The orchestrator carrying a role's whole question batch to the user and the answers back to a fresh agent for the same stage.
_Avoid_: round trip, handoff, callback

**Open relay round**:
A relay round holding at least one unanswered question, awaiting the user's answers.
_Avoid_: pending round, active round

**Envelope**:
The single fenced JSON block a role ends every turn with, carrying its status, files, questions and counts.
_Avoid_: result, payload, response

**Finding**:
One reviewable defect a reviewer reports, with a severity and the rule or artefact it rests on.
_Avoid_: issue, comment, violation

**Verdict**:
The judge's merged, deduplicated, verified ruling over a review round's findings.
_Avoid_: report, summary

## Run state

**State writer**:
The single CLI interface that mutates run state: it stamps the time, validates, writes atomically and commits. There is no manual-write fallback; if it cannot run, the run halts.
_Avoid_: state editor, manual path, hand edit

**History event**:
The vocabulary-checked event a transition record carries, from the closed list `complete`, `verify-pass`, `verify-fail`, `approved`, `gate-override`, `aborted`, `pr-open`, `resumed`.
_Avoid_: event type, status flag

**Verify record**:
The latest `verify` history entry: build and test re-run by the orchestrator itself, its commands and pass/fail carried in the entry. Review reads it and refuses unless it passes.
_Avoid_: verification note, green build

**Run lock**:
One run's guard against concurrent writers, recording owner, host, harness and time; it covers the worktree state and, before that, the pending file beside which it lives.
_Avoid_: mutex, lock file

**Stale pending file**:
A pending file whose run has a worktree state or has ended; the file that is still the run's only state is never stale.
_Avoid_: orphan state, old run

## Skill routing

**Intake intent**:
Exploration or delivery, decided from the request's wording or, when ambiguous, by exactly one relay question; it decides whether a run's first stage is `brainstorm` or `grill`.
_Avoid_: mode, category, request type

**Exploration stage (`brainstorm`)**:
The idea path's first stage, settling into `grill`: its confirmed direction lands in the pending brief and resumes from pending storage like any other pending stage.
_Avoid_: idea stage, ideation

**Skill map entry**:
A logical skill name plus the path the active harness's adapter resolved for it, stored in `state.skills` and re-resolved when the harness changes.
_Avoid_: skill reference, dependency

**Protected question**:
A relay question carrying `requires_user: true`, which fast mode must never auto-accept; the plan's seam confirmation is one.
_Avoid_: manual question, forced question

**Seam confirmation**:
The user's agreement to a plan's proposed public test seams, persisted with the plan and invalidated when the seams or scope it names change.
_Avoid_: test approval, sign-off

**UI change signal**:
A diff's classification as touching a user-visible surface: view markup and styles, design tokens and themes, UI assets, locale and string files, or user-visible copy inside UI code.
_Avoid_: UI flag, frontend change

**Shared integration reference**:
The one compact document (`core/skills/factory/references/skills.md`) holding skill precedence and loading rules for the orchestrator and both code-writing roles, linked rather than restated.
_Avoid_: skills doc, integration guide

## Engineering discipline

**Engineering rules reference**:
The factory's single harness-neutral statement of its coding discipline: test-first delivery and proportionate practices for correctness, readability, maintainability, security and performance, pointed at by every role that writes, plans, reviews or judges code.
_Avoid_: coding standards, style guide, TDD doc

**Rule id**:
The stable `ENG-n` label of one rule in that reference; the token findings, verdicts and plan overrides use to name a rule.
_Avoid_: rule number, rule name

**Test seam**:
A public entry point of a change that is put under test, agreed in the plan and named by the tasks that test and implement it.
_Avoid_: interface, boundary, hook, test point

**Red proof**:
The line in a task's commit body recording the test that was seen failing before the implementation existed (`Red: <test name> failed as expected`) or, where an existing passing test already covers the behaviour, the line naming that test instead (`Red: not applicable - <existing test> already covers this`). Both lines are red proofs; no other wording is.
_Avoid_: red commit, evidence, test log

**Behaviour-changing**:
What makes a unit of work (a task or a fix) need a red proof: it changes what an entry point returns or does. A change confined to documentation, configuration or generated output is not behaviour-changing.
_Avoid_: functional change, real change

**Test-first exemption**:
A documentation- or configuration-only part of a change that the plan declares, with its reason, as not requiring a test.
_Avoid_: skip, waiver, opt-out

**Rule override**:
A consuming repository's own documented rule winning over a factory rule, recorded in `plan.md` as `Overridden: ENG-n - <repo rule that wins>`.
_Avoid_: exception, opt-out, local rule

**Advisory finding**:
An engineering finding based only on a design or style judgement, including `ENG-7`..`ENG-10`, rated at most MEDIUM and never blocking. A concrete requirement or safety defect is rated by its consequence instead. A fix round driven by a verdict performs no fix work on an advisory finding; it reaches the user in the verdict's advisory list (keeping its `ENG-n` id in that entry's `summary`) and on the approver screen, and the user sends it back into the run with the approver's "Request changes", which is implemented exactly as asked.
_Avoid_: nit, suggestion, soft finding, warning

**Verdict-driven fix round**:
A fix round the orchestrator runs to answer a judge verdict: its work is that verdict's confirmed blocking findings, and its commit's red proofs are matched against them.
_Avoid_: review fix, blocking fix round

**User-changes fix round**:
A fix round the orchestrator runs to answer the user's "Request changes" at the approver gate: its work is the request's own text, including any advisory finding the request names, and its commit's red proofs are matched against neither the task list nor a verdict.
_Avoid_: manual fix, approver fix, rework

**Reason line**:
The sentence a plan carries for each new file, new abstraction or new dependency it introduces, saying why it is needed (`ENG-10`); a missing one is a MEDIUM, non-blocking analyze finding.
_Avoid_: justification, rationale note

**Reuse search**:
The bounded look for an existing function to reuse or extend before writing a new one: the module being changed plus the repository's shared utility locations, by the concept's keywords, once per new function.
_Avoid_: duplication check, grep

**Shared utility locations**:
The bound of a reuse search beyond the module being changed: the directories the repository's own conventions name as shared (`helpers/`, `utils/`, `util/`, `common/`, `lib/`, `shared/` and the like), plus any module the module being changed already imports for helpers. The search over them is keyword-level text matching, not a review of the whole repository.
_Avoid_: helpers, common code, the codebase
