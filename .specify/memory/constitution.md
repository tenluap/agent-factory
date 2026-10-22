<!--
Sync Impact Report
- Version change: template → 1.0.0
- Principles added: I. Design First; II. Harness-Neutral Core; III. Generated Dist;
  IV. Stateless Agents; V. Simplicity and Reuse
- Sections added: Writing Standards; Development Workflow; Governance
- Removed sections: none
- Deferred TODOs: none
-->
# Agent Factory Constitution

## Core Principles

### I. Design First
`DESIGN.md` is the source of truth for how `/factory` behaves. A behaviour change MUST be
recorded in `DESIGN.md` first, then carried into `core/` and `adapters/`. When a core or
adapter file disagrees with `DESIGN.md`, the file is wrong unless `DESIGN.md` is changed
deliberately in the same change.

### II. Harness-Neutral Core
Files under `core/` MUST NOT name a harness tool, path or command. They use only the
neutral verbs in `core/skills/factory/references/verbs.md` (`SPAWN`, `SPAWN_PARALLEL`,
`ASK`, `NOTIFY`, `RESOLVE`, `SHELL`). Anything harness-specific lives in
`adapters/<harness>/`. Rationale: one core must run unchanged on every harness.

### III. Generated Dist (NON-NEGOTIABLE)
`dist/` is build output of `tools/render.py`. Nobody edits `dist/` by hand. Every change to
`core/` or `adapters/` MUST be followed by a render of every harness, and the rendered
`dist/` MUST be committed with the source change so `dist/` never drifts from its source.

### IV. Stateless Agents
Every agent turn is a fresh spawn. An agent MUST NOT rely on memory of an earlier turn.
Anything a later turn needs lives in `state.json` or on disk. Agents never talk to the user;
their questions reach the user through the orchestrator's relay.

### V. Simplicity and Reuse
Add the smallest change that meets the need (YAGNI). Before adding a rule, reference,
script or role, look for an existing one and extend or reference it instead of duplicating
it. A new file, field or verb needs a stated reason in the plan.

## Writing Standards

Role prompts, skills and references are instructions for agents. They MUST be short,
imperative and unambiguous: one idea per sentence, one term for one concept everywhere,
no filler. Each role states its inputs, its work and its done condition, and ends with the
envelope or report shape defined in `references/protocol.md` or `references/findings.md`.

## Development Workflow

- Build: render every harness with `tools/render.py` (`python3 tools/render.py --list`
  names them).
- Test: after the build, `git diff --exit-code -- dist/` MUST pass, proving the committed
  `dist/` matches its source.
- A change to the flow is validated end to end per the "Validation plan" in `DESIGN.md`
  before it is relied on.

## Governance

This constitution supersedes other practices in this repo. Amendments are made with
`/speckit-constitution`, recorded with a version bump (MAJOR: principle removed or redefined;
MINOR: principle or section added or materially expanded; PATCH: wording), and committed
together with any `DESIGN.md` change they imply. Every review checks a change against these
principles; a violation needs a written justification in the plan.

**Version**: 1.0.0 | **Ratified**: 2026-10-21 | **Last Amended**: 2026-10-22
