# OpenCode factory startup reliability

**Date:** 26 October 2026  
**Status:** Implemented; runtime OpenCode discovery still requires a live-session check.

## Problem

Users can reach an OpenCode session where `/factory` cannot start because the factory orchestrator or required OpenCode capabilities are unavailable. The resulting generic message does not explain how to restore the flow. The factory already has an OpenCode adapter and installer, but an installed skill and role agents are only loaded in a newly started session.

## Decisions

- Keep `/factory` as the installed factory skill. Do not add a separate orchestrator service or launcher.
- Make the OpenCode installation path and verification outcome explicit: the factory skill and all required `factory-*` role agents must be linked, and the user must start a fresh session for OpenCode to discover them.
- When the factory skill is loaded but a required orchestration capability (notably `subagent`) is unavailable, fail before creating pending state or a worktree and show concise, actionable recovery guidance. Do not claim that the factory can repair a session in which its own skill is not loaded.
- Preserve uncommitted work by using the existing isolated-worktree flow; never require a clean checkout merely to initiate the factory.
- Keep changes scoped to OpenCode startup/install guidance and capability preflight; do not alter the factory's harness-neutral workflow or other adapters.

## Approaches considered

1. **Improve install and verification plus runtime capability preflight (recommended).** Covers both stale/missing installation and sessions that lack required tools, with no new service.
2. Improve installation instructions only. Smallest change, but a loaded skill can still fail without explaining the missing capability.
3. Add a separate launcher/orchestrator. Adds another entrypoint and still cannot help when unavailable in the active session.

## Behavior

The documented OpenCode setup names the install command, the installed skill/agent locations, and the required fresh-session reload. The factory's loaded startup instructions check that the current session can perform its required orchestration before beginning intake. If a capability is absent, the message names the missing capability and the recovery step (install or reload OpenCode configuration, then start a new session). The check does not mutate the repository, create a run, or create a worktree.

Once preflight succeeds, existing behavior remains: a rough idea can enter the factory's intake flow, and work proceeds in its isolated worktree. Existing uncommitted checkout changes remain untouched.

## Validation

- Verify installer output/links for the OpenCode skill and every factory role using a throwaway `HOME`.
- Verify startup instructions cover available and unavailable orchestration capability, with a useful recovery message and no worktree creation on failure.
- Re-render tracked distributions and run the existing test suite, installer syntax check, and distribution drift check.
- A real OpenCode session check is needed to prove runtime discovery; static rendering alone cannot prove the host loaded the skill or exposes `subagent`.
