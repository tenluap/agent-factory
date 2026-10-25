# OpenCode V2 adapter implementation plan

Approved contract: [design](../specs/2026-10-25-opencode-v2-adapter-design.md).

## Tasks

- [x] Add renderer tests for YAML permission rules, OpenCode read-only/write agents, and unchanged legacy adapter output.
- [x] Update `adapters/opencode/adapter.json` to emit V2-native ordered `permissions` rules (`edit`/`subagent`) while preserving role access intent.
- [x] Extend Markdown frontmatter serialization in `tools/render.py` for list-of-mapping values; preserve existing dict, scalar, and TOML output.
- [x] Update `adapters/opencode/harness.md` for V2 `subagent` dispatch, parallel dispatch, and `shell`, preserving model defaults and overrides.
- [x] Render all harnesses canonically; verify OpenCode agents and unchanged native agents for every other harness. Each distribution also receives the shared OpenCode reference.
- [x] Run tests, link/format checks, and `git diff --check`; inspect the diff for accidental changes, including pre-existing untracked files.

## Test seams and exemptions

Test public seam: `render_agent()` with adapter metadata and role access values. Tests must assert emitted OpenCode frontmatter, including ordered `permissions` mappings and `mode: subagent`, plus representative legacy Markdown/TOML output. Exercise deny-edit and deny-subagent rules for read-only roles, and deny-subagent for write roles.

Exempt: live OpenCode dispatch and permission enforcement cannot be established by renderer tests. Verify these only if an OpenCode V2 runtime is available; report static and runtime evidence separately. No behavior-changing implementation begins until the tests demonstrate expected failing output.

Overridden: none.

## New files, abstractions, and dependencies

| Path/name | Kind | Reason |
|---|---|---|
| `tools/test_render.py` | test file | Protect renderer output for nested V2 permissions and prevent regressions in other native agent formats. |
| This plan | file | Track the approved adapter migration and verification boundary. |
| New abstractions/dependencies | none | Extend existing renderer serialization and use Python's standard `unittest`. |

## Verification commands

Run renderer tests with `python3 -m unittest discover -s tools -p 'test_*.py'`. Render each harness listed by `python3 tools/render.py --list`, using isolated home variables and a nonexistent `FACTORY_HOME`; compare non-OpenCode generated agent and skill contents against the pre-change baseline. Inspect every generated OpenCode agent for native `mode: subagent` and V2 `permissions` entries, with expected actions/effects. Parse YAML in tests if an existing dependency is already available; otherwise assert the exact generated frontmatter without adding a dependency.

Check changed Markdown links, run `git diff --check`, rerender to verify reproducibility, and confirm final `git status` contains no unexpected generated or user-owned files. If V2 OpenCode is installed, separately verify `/factory` discovery, named subagent dispatch, and agent-specific edit/child-agent restrictions.

## Validation record

- Red proof: `python3 -m unittest discover -s tools -p 'test_*.py'` failed before implementation with missing native `permissions` output and `TypeError: sequence item 0: expected str instance, dict found` when rendering ordered permission rules.
- After implementation, all six tests pass. The tests cover all nine OpenCode roles, a complete temporary distribution, and legacy Markdown/TOML output.
- Canonical rendering uses no user model overrides. All other harnesses' native agents are byte-identical to the baseline. Their only changes are the bundled OpenCode reference. A second render produces identical distribution bytes.
- `git diff --check` passes, and changed local Markdown links resolve. Existing Finder metadata is preserved.
- OpenCode `v2.1.4` runtime discovery passes using an isolated configuration and private server. All nine global symlinked factory agents load as subagents with the expected model references and native deny rules. The global symlinked factory skill is discovered. Configuration discovery is asynchronous, so checks wait for registration to settle.
- Runtime scope: agent and skill discovery plus loaded permission configuration. Model-backed subagent dispatch, interactive `/factory` selection, and enforcement during model tool calls were not exercised. No end-to-end factory run is claimed.
- The later `/factory` invocation halted at Codex preflight because `speckit-specify`, `speckit-clarify`, `speckit-plan`, `speckit-tasks`, `speckit-analyze`, and `speckit-implement` are absent from Codex's configured skill/prompt search paths. Existing Claude Code SpecKit files remain untouched. Factory review and PR publication have not run.
