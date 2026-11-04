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
A prompt the orchestrator spawns an agent from, named by its job (spec-builder, code-build, design-to-code, fixer, reviewers, judge). `facets-advisor` and `design-to-code` are the roles the user can also start directly as main agents.
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
One reviewable defect a reviewer or analyze reports, with a severity and the rule or artefact it rests on.
_Avoid_: issue, comment, violation

**Verdict**:
The judge's merged, deduplicated, verified ruling over a review round's findings.
_Avoid_: report, summary

**Time budget**:
The seconds one spawned role may work before it must stop: 300 by default, overridable per role.
_Avoid_: timeout, quota, limit

**Deadline**:
The absolute UTC instant one spawn receives as the end of its role's time budget.
_Avoid_: due time, expiry, cutoff

**Overrun report**:
A role's own account of running past its deadline: a cause from a closed list plus free-text detail carrying the overshoot.
_Avoid_: timeout report, late report, overrun note

**Partial return**:
A file-writing role's stopped-but-committed result, resuming its stage from a fresh spawn over the work on disk.
_Avoid_: truncated return, partial output

**Unit of work**:
The piece of work a role commits as one piece — the task/commit granularity the roles already use — and the boundary at which a stopped role stops.
_Avoid_: step, chunk, iteration

**Stall cap**:
The halt rule on resumption: three consecutive `partial` returns of one stage with no new commit between them halt the run; every partial return counts whatever its stop reason, and neither a failure-policy retry (not a partial return; issue records carry a `partial_return` mark that tells the two apart) nor the overrun records of never-stopped roles ever count.
_Avoid_: retry cap, resume limit

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

**Session issue**:
One append-only record of a single thing that went wrong in a factory run: an overrun, agent failure, retry, halt or red verify. Not a review finding.
_Avoid_: finding, bug, incident

**Improvement backlog**:
The factory home's set of `ready` or claimed improvement entries, of two kinds: Run exports and Retro entries.
_Avoid_: issue list, pending improvements

**Run export**:
The run-end improvement backlog entry of one factory run's issues, totals and factory version; its appearance is what gates improvement work on that run.
_Avoid_: backlog file, issue export

**Retro**:
The read-only review of an ended run, between `pr-open` and the drop, that mines the run for improvement signals and proposes at most three improvement candidates.
_Avoid_: retrospective, post-mortem, run review

**Improvement signal**:
One measured pattern in an ended run that suggests a factory improvement, such as a reviewer the judge keeps rejecting or a stage that keeps halting.
_Avoid_: metric, finding, issue

**Signal key**:
The stable identity of an improvement signal: its kind plus its subject, such as a reviewer or role name; two entries with one signal key cover the same signal.
_Avoid_: signal id, fingerprint

**Improvement candidate**:
A proposed improvement the retro returns: signal key, evidence, impact rank and suggested feature text; not yet in the backlog.
_Avoid_: suggestion, recommendation

**Retro entry**:
An improvement candidate accepted into the improvement backlog, carrying its signal key, evidence, suggested feature and source run.
_Avoid_: retro export, retro backlog

**Run folder**:
The `specs/<branch>/factory/` directory of run artifacts (state, brief, reports, findings and design evidence), committed on the feature branch while the run is in progress.
_Avoid_: factory dir, run dir

**Run archive**:
The verified, byte-identical copy of the run folder at `${FACTORY_HOME:-~/.factory}/archive/<repo-name>-<branch>/`, excluding transient `lock.json`; written once and never overwritten.
_Avoid_: backup, export

**Drop**:
The single end-of-run step after the PR opens that archives the run folder and produces the `factory: drop run artifacts` commit removing it from the branch, rehoming any design evidence first.
_Avoid_: cleanup, purge

**Permanent design evidence**:
Pen design evidence after the drop, living at `docs/design/<branch>/` and referenced by `docs/design-code-map.json`.
_Avoid_: design archive, design folder

## Analyze loop

**Baseline analysis**:
A run's first completed analysis, whose severity counts every later recheck is measured against; it changes only when the user explicitly chooses a fresh baseline.
_Avoid_: first pass, original report, initial analysis

**Recheck**:
Any analysis after the baseline analysis, run against the artifacts as remediation left them; the most recent one is what the implement gate judges.
_Avoid_: fresh analysis, re-analysis, verification loop

**Acceptance targets**:
The baseline-relative conditions a recheck must meet before implementation: no CRITICAL or HIGH findings, and the total and LOW counts each strictly below half their baseline counts, with a zero baseline count staying zero.
_Avoid_: thresholds, exit criteria, quality bar

**Repair cycle**:
One remediation of the spec artifacts in place followed by its recheck; at most two run automatically per run, and lite-to-full escalation is not one.
_Avoid_: loop, remediation pass, retry

**Implement gate**:
The check before implementation that refuses while any acceptance target is unmet, a protected question is open or no trustworthy baseline analysis exists, unless the user recorded a gate override.
_Avoid_: implementation checkpoint, transition gate, analyze gate

**Exhaustion question**:
The protected question asked when acceptance targets are still unmet after the automatic repair cycles: one more guided pass, a recorded gate override, or abort.
_Avoid_: halt question, escalation question, cap prompt

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

## UI design

**UI design run**:
A factory run whose saved design context records a design source and a UI scope; its UI design tasks are implemented by the `design-to-code` role instead of `code-build`.
_Avoid_: design mode, Pen run, UI run

**UI design task**:
A task the tasks stage marks `[UI]`, routed to `design-to-code` by that marker alone.
_Avoid_: design task, UI ticket

**Design source**:
What a UI design run implements from, one of four kinds with fixed authority: Pen file and Figma node (mapped), image or screenshot (visual reference only), text-only restyle (existing code is the baseline).
_Avoid_: design input, mockup, reference

**Text-only restyle**:
A design source classified at plan for a brief asking a purely visual change with no behaviour change; it has no design reference, so mapping and fidelity are not applicable and build/runtime evidence is still required.
_Avoid_: restyle mode, visual tweak

**Quality pass**:
The single quality pass (critique, audit, typeset, polish, re-verify, the skill's fidelity-locked `qa` mode) run once per UI design run by the spawn completing the last UI design task, over the whole changed UI surface.
_Avoid_: polish loop, UI review

**Framework reference**:
The per-framework guidance document `design-to-code` loads for the UI framework detected at plan; a framework without one is unsupported and stops the run.
_Avoid_: framework adapter, framework plugin

**UI scope**:
The files a UI design run may change: a named target file with its component dependencies, or the user-accepted whole-surface file list.
_Avoid_: blast radius, target set

**Dependency batch**:
One layer of a UI scope (tokens and assets, then shared components, then views) implemented and committed as one unit of work.
_Avoid_: wave, tier, chunk

## Skill library

**Skill library**:
The skills the factory installs into every selected harness from one place, in two layers: the repo layer and the per-user layer.
_Avoid_: skill store, skill registry, skill pack

**Library skill**:
One folder in a library layer holding a `SKILL.md` whose frontmatter `name` equals the folder's name; dot-prefixed folders and a folder named `factory` (reserved for the factory skill) are never library skills.
_Avoid_: plugin, package, module

**Repo layer**:
The committed library layer shipping verbatim, attributed copies of the skills the factory itself requires.
_Avoid_: bundled skills, core skills, vendor dir

**Per-user layer**:
The library layer under one user's factory home holding the skills that user added; never committed, kept on disk by uninstall, and it wins a name clash with the repo layer.
_Avoid_: local skills, custom skills, overrides

**Skills root**:
The directory a harness loads skills from, declared by that harness's adapter and moving with the harness home override where the harness has one; one root may serve more than one harness.
_Avoid_: skills dir, install target

**Library link**:
A symlink in a skills root pointing into a library layer: the only thing the installer creates or removes for the library, including removal on re-run once its source folder is gone. Anything else at that path is user-owned and skipped.
_Avoid_: install, copy, managed skill

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

## Benchmark

**Benchmark**:
The replay of a pre-settled fixture feature against one factory version, stopped at the approver gate, so factory versions can be compared.
_Avoid_: perf run, regression suite, test run

**Benchmark score**:
One run's measured outcome — time, spawns, overruns, issues by kind, token estimates, review rounds and a pass verdict — comparable against another score.
_Avoid_: metrics dump, report, summary

## FACETS

**FACETS checklist**:
Six yes/no questions (Face, Advantage, Capital, Expertise, Time, Scale) that score a project or income option out of 6; text in `references/facets.md`.
_Avoid_: facets score card, framework quiz

**FACETS profile**:
The user's constraints (`hours_per_week`, `capital_at_risk`, `skills`, `face_comfort`, `income_goal`, `current_assets`) in `${FACTORY_HOME}/facets-profile.md`, against which Capital, Expertise and Time are judged.
_Avoid_: user settings, preferences

**Research access**:
The `research` access level: `read` plus web search and fetch, no file writes; only `facets-advisor` uses it.
_Avoid_: web access, online mode

**Main agent**:
A role with `mode: primary` that the user starts as their session's agent instead of the orchestrator spawning it; today only `facets-advisor`.
_Avoid_: primary role, top-level agent
