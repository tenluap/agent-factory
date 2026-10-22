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
The agent product a run executes in (Claude Code, OpenCode, Codex, Copilot).
_Avoid_: platform, client, host

**Adapter**:
The per-harness translation of the neutral verbs and install locations into that harness's mechanisms.
_Avoid_: plugin, backend

**Relay**:
The orchestrator carrying a role's whole question batch to the user and the answers back to a fresh agent for the same stage.
_Avoid_: round trip, handoff, callback

**Envelope**:
The single fenced JSON block a role ends every turn with, carrying its status, files, questions and counts.
_Avoid_: result, payload, response

**Finding**:
One reviewable defect a reviewer reports, with a severity and the rule or artefact it rests on.
_Avoid_: issue, comment, violation

**Verdict**:
The judge's merged, deduplicated, verified ruling over a review round's findings.
_Avoid_: report, summary

## Engineering discipline

**Engineering rules reference**:
The factory's single harness-neutral statement of its coding discipline (test-first, clean code, SOLID, functional preference, reuse), pointed at by every role that writes, plans, reviews or judges code.
_Avoid_: coding standards, style guide, TDD doc

**Rule id**:
The stable `ENG-n` label of one rule in that reference; the token findings, verdicts and plan overrides use to name a rule.
_Avoid_: rule number, rule name

**Test seam**:
A public entry point of a change that is put under test, agreed in the plan and named by the tasks that test and implement it.
_Avoid_: interface, boundary, hook, test point

**Red proof**:
The line in a task's commit body recording the test that was seen failing before the implementation existed.
_Avoid_: red commit, evidence, test log

**Test-first exemption**:
A documentation- or configuration-only part of a change that the plan declares, with its reason, as not requiring a test.
_Avoid_: skip, waiver, opt-out

**Rule override**:
A consuming repository's own documented rule winning over a factory rule, recorded in `plan.md` as `Overridden: ENG-n - <repo rule that wins>`.
_Avoid_: exception, opt-out, local rule

**Reuse search**:
The bounded look for an existing function to reuse or extend before writing a new one: the module being changed plus the repository's shared utility locations.
_Avoid_: duplication check, grep
