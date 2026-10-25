# Pen design-code mapping implementation plan

Approved contract: [design](../specs/2026-10-25-pen-design-code-mapping-design.md).

## Tasks

- [x] Record the approved contract in `DESIGN.md` before changing core behavior.
- [x] Add the conditional shared mapping reference and Avalonia-specific guidance; wire skill resolution and fresh-role inputs.
- [x] Align verification, shared repair budget, explicit exceptions, approval/publication, and resume/state/result contracts.
- [x] Align README/product documentation and render all five harnesses canonically.
- [x] Verify links, JSON examples, core/distribution parity, native agent formats, legacy/new state digests, and whitespace; review instructions against the approved acceptance scenarios.

## Test seams and exemptions

Exempt: instruction Markdown, illustrative JSON, and generated agent/skill distributions — no executable behavior is introduced or changed. Existing renderer and state CLI are reused without modification. Packaging checks and throwaway state fixtures establish compatibility; they do not prove a real Pen-to-application conversion.

Overridden: none.

## New files, abstractions, and dependencies

| Path/name | Kind | Reason |
|---|---|---|
| This plan | file | Track the accepted instruction change and its checks. |
| `core/skills/factory/references/design-code-mapping.md` | file | Own the common contract once, loaded only for Pen reference work. |
| `core/skills/factory/references/design-code-mapping-avalonia.md` | file | Isolate Avalonia translation and runtime evidence from other frameworks. |
| New abstractions/dependencies | none | Existing roles, adapter resolution, state CLI, renderer, and review rounds cover the work. |

## Verification commands

Canonical render: run `python3 tools/render.py <harness>` for every name from `--list`, with `CLAUDE_HOME`, `CODEX_HOME`, `COPILOT_HOME`, `ZCODE_HOME`, and `XDG_CONFIG_HOME` unset and `FACTORY_HOME=/nonexistent`.

Check relative Markdown links, JSON examples in changed references, the existing under-60-line skill-integration reference, byte parity of shared skill trees and core files, and parsing of generated TOML/Markdown agent metadata. Run the read-only state CLI against scratch pending fixtures for versions 1/2 and version 3 with design context and protected decisions. Re-render once more and compare content fingerprints to establish reproducibility. Finish with `git diff --check`.

Real supported Pen inspection, Avalonia/application launch, and matching screenshot comparison need an actual target design/application and are outside these packaging checks. Record that limit in the handoff.

## Validation record — 25 October 2026

- Relative-link check: 52 existing/new local Markdown links resolve; the shared skill-integration reference remains under 60 lines and contains no restated engineering rule.
- Eight reference/README JSON examples parse. All six affected specialist roles point to the shared design contract.
- All five canonical skill trees are byte-identical and match core references/role bodies; all 45 native agent files retain their previous metadata/settings, with TOML parsed successfully.
- Six throwaway state-CLI fixtures pass: version-1 relay, version-2 string answers, protected design decisions with consumed repair count, interrupted reserved design fix, design-only context, and ordinary brainstorming. Optional context and pending reservation pass through without changing CLI code.
- A second canonical render reproduces every distribution byte. Whitespace checks pass.
- Instruction review traced accepted Q1–Q14 through activation/stack scope, reference authority/update direction, persistent exhaustive scoped mapping, bootstrap/shared/removal behavior, identity/freshness, real fidelity criteria, explicit exceptions, evidence retention, and shared bounded repair/resume. Static desktop review and optional impeccable skips cannot replace the required rendered gate.
- No actual Pen design or target application was supplied for execution. Live backend/node inspection, application runtime, real screenshot fidelity, and agent-driven interrupted-resume/exception trials remain unexercised; packaging checks do not claim those outcomes.
