# Implementation Plan: OpenCode V2 adapter

**Branch**: `006-opencode-v2-adapter` | **Date**: 2026-10-25 | **Spec**: [spec.md](spec.md)

## Summary and technical context

Adopt native OpenCode V2 subagent/shell instructions and ordered permission rules. Extend the existing Python 3 renderer only for list-of-mapping Markdown metadata; keep JSON adapters, Markdown/TOML agent formats, installed paths, model defaults/overrides and harness-neutral flow. Five harnesses and nine roles are in scope. Reuse Python standard-library `unittest`; no third-party dependency, new production abstraction, database, service, or runtime model-call requirement.

## Constitution check

Pre-design: pass with the sequencing below. Post-design: pass; protected seam confirmation recorded below.

- Commit the native contract in `DESIGN.md` before adapter behavior changes.
- Keep native tools/policy in `adapters/opencode/`; leave `core/` unchanged.
- Render all five distributions after source changes and commit generated output with its source. Never edit or import saved generated output manually.
- Persist task evidence and role handoffs on disk. Preserve the invoking checkout, its existing source edits, and local Codex SpecKit setup.
- Extend current functions and inspect/adopt the saved tests; no unnecessary layer or dependency.

## Structure and implementation sequence

Change `DESIGN.md`, `tools/render.py`, `adapters/opencode/adapter.json`, `adapters/opencode/harness.md`; add `tools/test_render.py`; regenerate `dist/`. Feature artifacts stay in this directory.

1. Record the V2 adapter contract in `DESIGN.md` and commit it first.
2. Inspect `state.prior_work.handoff`. Adopt only its six saved tests initially, without applying production changes. Run them against this worktree's baseline and observe actual native permission serialization/access failures. Prior red claims are context, not fresh proof. If tests cannot run, stop rather than importing code.
3. Extend existing `yaml_value()` for lists of mappings using JSON flow mappings inside ordered YAML sequences. Preserve scalar, flat-map, string-list, TOML output and TOML structured-field rejection. Exercise through `render_agent()`.
4. Convert OpenCode configuration to native ordered permissions. Through `agent_fields()`, verify all nine roles, mode, permission ordering and tier model mapping. Read roles deny edit then subagent; write roles deny subagent without gaining edit denial. Through `render()`, verify complete temporary output, copied references and model behavior; add isolated override/empty-model inheritance cases if absent from saved tests.
5. Update harness instructions for named foreground subagent calls, parallel dispatch and shell. Retain question relay, skill resolution, paths, defaults and overrides; correct the outdated claim that models are unset by default.
6. Canonically render every harness and commit generated output with adapter source. Compare other harness native agents and unrelated skill contents against a canonical baseline: only their bundled OpenCode reference may change.
7. Run checks, record the four evidence categories, and retain explicit limits. Existing v2.1.4 discovery covers loading only. Model-backed dispatch and runtime permission enforcement stay unverified unless actually exercised; no new model calls are required. Observed runtime contract conflicts block delivery without relaxing access rules.

Every behavior implementation task has its mapped failing-test task immediately before it. Commit test and implementation together, with `Red: <test name> failed as expected`, or `Red: not applicable - <existing test> already covers this` only where a precise existing test applies. No separate red commit.

## Test seams

- `render_agent()` — native ordered-rule output, unchanged legacy Markdown/TOML, structured-field rejection for TOML.
- `agent_fields()` — all roles' permissions/order, mode and tier-to-model mapping.
- `render()` — isolated complete distribution, copied references, model overrides/inheritance and canonical compatibility.

Test runner: Python standard-library `unittest` - repository currently has no test suite; this is Python's conventional default without a dependency. Run `python3 -m unittest discover -s tools -p 'test_*.py'`.

Exempt: `DESIGN.md` and maintained compatibility/evidence Markdown - documentation only; check scope, claims and links.

Exempt: `adapters/opencode/adapter.json` - configuration only; validate consumed output through listed seams.

Exempt: `adapters/opencode/harness.md` - instructions/documentation only; inspect native verbs, unchanged paths and accurate model statements.

Exempt: `dist/` - generated output only; canonical build, byte comparison and post-commit parity verify it.

Exempt: feature planning/validation artifacts - documentation only; check consistency and links.

Overridden: none.

Confirmed: 2026-10-25 - Q1 accepted - seams: render_agent(), agent_fields(), render()

## Validation and applicable quality constraints

- Run unittest, `bash -n install.sh`, `git diff --check`, and changed Markdown local-link checks.
- Canonical build renders all names from `python3 tools/render.py --list`, with absent FACTORY_HOME config and default adapter home settings. Commands are in [quickstart.md](quickstart.md). Preserve baseline bytes outside tracked output before changes.
- Require unchanged non-OpenCode agent bytes and no unrelated skill changes. After committing source/output, rerender and run the constitution gate `test -z "$(git status --porcelain -- dist/)"`; it must catch untracked additions too.
- Security/integrity: retain each deny rule's order, wildcard resource and effect; inspect every role. Do not broaden policy, modify user config, or log credentials.
- Failure/resources: use temporary directories with cleanup on success/failure; preserve diagnostic test output. No runtime server lifecycle is introduced. Optional discovery waits are bounded and report version/errors precisely.
- Performance/dependencies: no changed latency or scale requirement; reuse bounded existing generation and stdlib rather than add benchmarks, caches or telemetry.
- Observability: distinguish static checks, discovery, model-backed dispatch and runtime enforcement. Loaded policy alone is not enforcement proof.
- Delivery: use existing installer after approval; no operator migration. Roll back by restoring prior source/adapter and regenerating distributions. Factory approval remains the publication gate.

## New files, abstractions and dependencies

- `tools/test_render.py` - file - prevent native-permission regressions while protecting legacy formats through existing public seams.
- `specs/006-opencode-v2-adapter/plan.md` - file - record sequencing, gates and confirmed test scope.
- `specs/006-opencode-v2-adapter/research.md` - file - retain primary-source decisions and evidence limits.
- `specs/006-opencode-v2-adapter/data-model.md` - file - capture existing adapter/role/rule invariants without a production model layer.
- `specs/006-opencode-v2-adapter/contracts/opencode.md` - file - state generated metadata and instruction contract.
- `specs/006-opencode-v2-adapter/quickstart.md` - file - provide reproducible isolated validation commands.
- New abstractions: none; extend the internal serializer without another public seam.
- New dependencies: none; use standard-library JSON, temporary directories and unittest.
