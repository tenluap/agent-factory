# OpenCode V2 adapter design

## Context

OpenCode V2 intends to preserve supported V1 agent, skill, and command behavior, so most of the factory should continue to work without migration. The factory does not use OpenCode's server API or plugin API, the two breaking integration surfaces. However, its OpenCode adapter still emits V1-style permission metadata and describes spawning agents through the `task` tool/action. V2 documents native agent permissions as ordered `permissions` rules and uses `subagent` as the permission action and child-agent tool.

Sources: [V1-to-V2 migration guide](https://opencode.ai/v2/docs/migrate-v1), [Agents](https://opencode.ai/v2/docs/agents), [Permissions](https://opencode.ai/v2/docs/permissions).

## Goal and scope

Make the OpenCode adapter explicitly native to V2, without changing the harness-neutral factory flow or other harnesses. Preserve existing role access intent and installation locations.

In scope:

- Update OpenCode harness instructions to describe V2's `subagent` tool and permission action.
- Render OpenCode agent files with V2-native `permissions` arrays and retain each role's existing read/write access restrictions.
- Extend renderer serialization only as needed for nested permission rules; preserve output for existing adapters.
- Add automated checks for rendered OpenCode frontmatter and permission rules, regenerate canonical `dist/opencode`, and verify other harness outputs remain unchanged.
- Document that OpenCode V2 runtime behavior must be verified in an installed V2 session if that environment is available; static rendering alone does not prove runtime behavior.

Out of scope:

- Rewriting the shared factory core, migrating other adapters, changing user/global OpenCode configuration, or adopting unrelated V2 settings.
- OpenCode server API or plugin migration; factory does not use either integration.
- Claiming runtime verification when no V2 OpenCode session is available.

## Design

Keep `adapters/opencode/` as the sole source of OpenCode-specific behavior. Its agent definitions should use V2 Markdown frontmatter: `mode: subagent` and ordered `permissions` entries. Read-only roles deny `edit` and `subagent`; write roles deny `subagent`, matching current access intent. Permission entries use `action`, `resource`, and `effect`; legacy `permission` maps and `task` action are not emitted.

Update `adapters/opencode/harness.md` so `SPAWN` and `SPAWN_PARALLEL` invoke named factory agents with V2's `subagent` tool. Keep skill resolution, question relays, shell usage, install paths, model inheritance, and all neutral verbs unchanged unless V2 evidence requires a focused correction.

The renderer should serialize the new list-of-mappings shape without changing the rendered syntax of other adapters. Tests should exercise representative read-only and write agent outputs and verify the complete OpenCode render. Canonical rendering updates only `dist/opencode`.

## Compatibility and failure handling

The V2 migration guide says supported V1 definitions remain compatible. This change is an explicit native-format adoption, not a claim that every OpenCode V2 release has been runtime-tested. Keep factory core behavior stable. If the V2 subagent tool or permission behavior differs from the documented contract, treat that as a blocker and report the observed version and behavior rather than silently weakening access controls.

## Validation

1. Run renderer tests for native V2 `mode` and ordered `permissions` output, including read-only and write access cases.
2. Render OpenCode and verify all generated agents contain native V2 permission fields and expected restrictions.
3. Render every harness and verify non-OpenCode distributions are unchanged.
4. Run repository checks and inspect the final diff, ensuring no unrelated or user-owned files are modified.
5. If an OpenCode V2 runtime is available, install the rendered adapter and verify `/factory` resolution, named subagent dispatch, and agent-specific edit/child-agent restrictions. Report this separately from static checks.
