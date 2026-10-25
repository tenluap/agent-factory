# Validation guide

Use Python 3, Git and Bash in the feature worktree on branch `006-opencode-v2-adapter`. No credentials or user config edits are needed.

1. Before production adoption, copy only saved tests from state.prior_work.handoff. Run `python3 -m unittest discover -s tools -p 'test_*.py'`. Observe baseline failures for native permissions and record precise names in the implementation commit body. Existing legacy-format assertions should pass.
2. After implementation, rerun unittest. Cover model overrides and empty-model inheritance through render() if absent from saved tests.
3. Render all harnesses canonically with no override config and default homes:

```bash
python3 - <<'PY'
import os
import subprocess
import tempfile
from pathlib import Path
with tempfile.TemporaryDirectory() as tmp:
    env = os.environ.copy()
    env['FACTORY_HOME'] = str(Path(tmp) / 'factory-home')
    for key in ('CLAUDE_HOME', 'CODEX_HOME', 'COPILOT_HOME', 'XDG_CONFIG_HOME', 'ZCODE_HOME'):
        env.pop(key, None)
    names = subprocess.check_output(['python3', 'tools/render.py', '--list'], env=env, text=True).splitlines()
    for name in names:
        subprocess.run(['python3', 'tools/render.py', name], env=env, check=True)
PY
```

Retain canonical baseline bytes outside tracked output before changes. Compare final output: other native agents stay identical; other skill trees change only their bundled OpenCode reference. Inspect all nine roles against [the contract](contracts/opencode.md). Never copy saved dist output.

4. Run `bash -n install.sh`, `git diff --check`, and changed local-link checks. Commit source plus generated output. Rerun canonical generation, then require:

```bash
test -z "$(git status --porcelain -- dist/)"
```

This post-commit gate includes untracked additions. Repeated generation must reproduce identical bytes.

Record static, discovery, model-backed dispatch and runtime enforcement separately. Prior v2.1.4 discovery loaded nine symlinked agents and the factory skill with expected configuration. Dispatch/enforcement are unverified; no new model calls are required. Optional discovery bounds asynchronous registration waits and records version/errors. Observed permission/dispatch conflicts block delivery without weakening policy.

## Performed checks (2026-10-25)

- T002: Canonical baseline for all five harnesses retained outside tracked output at `/var/folders/jf/7n12j8rx31q29v6v_gd380wc0000gn/T/factory-v2-canonical-baseline-w1ul62yb/dist` (160 files). Generation introduced no tracked drift. The invoking checkout's status and diff digest were captured alongside it for the final preservation check.
- Inspected the saved six-case test module and selected serializer/adapter/instruction diffs; imported no production changes, historical plan, or generated files. Standard-library unittest is runnable (zero tests before adopting the saved module).

- T003/T004: Fresh baseline run executed six tests: `RenderAgentTests.test_ordered_permission_rules_are_valid_yaml_sequences` raised `TypeError: sequence item 0: expected str instance, dict found`; `test_opencode_roles_preserve_access_and_models` failed for all nine roles (missing native `permissions`); `test_complete_opencode_distribution` failed (legacy `permission` output). Legacy Markdown, TOML output and TOML structured-field rejection passed. After the minimal serializer extension and native adapter update, all six tests passed. Regenerated all five harnesses canonically from maintained source.

- T005: Eight tests pass, including nonempty deep/standard overrides mapped to all nine named roles and empty values omitting model fields for session inheritance. Temporary FACTORY_HOME configs and patched render output roots are cleaned/restored by context managers. Existing production model logic was unchanged; these are green regression checks, not new behavior.

- T006: Fresh canonical generation compared all 160 final files against T002: 146 byte-identical, exactly 14 changed (nine OpenCode native agents and the OpenCode reference in all five bundles), no additions/deletions. Every non-OpenCode native agent and unrelated skill file stayed byte-identical. Each bundled OpenCode reference equals maintained `adapters/opencode/harness.md` byte-for-byte. No unexpected differences were accepted.

- T007: Evidence recorded in the four categories below. Optional fresh runtime discovery performed read-only against the installed tree; no model calls, no user configuration or service changes. No observed mismatch.

## Verification evidence categories (T007, 2026-10-25)

The four evidence categories are recorded separately; zero unexecuted checks are reported as passed.

- **Static checks — performed.** Unit tests and byte comparisons under T002–T006 above: saved six-case suite observed red at baseline, green after implementation; model override/inheritance regression cases green; canonical five-harness generation byte-compared against the retained baseline with only the 14 expected file changes. Contract inspection covered all nine rendered roles and both instruction files (T004). `bash -n install.sh`, `git diff --check` and changed local-link outcomes are recorded under T008 below.

- **Runtime discovery — performed as loading evidence only.** Historical evidence (recorded before this run, OpenCode v2.1.4): nine global symlinked roles discovered with expected loaded policy and the factory skill discovered. It proves loading only. Fresh discovery (2026-10-25, OpenCode v2.1.4, read-only): `opencode debug agents` returned an empty list on first invocation before the background registry settled; within a bounded wait it listed 58 agents including all nine `factory-*` agents, each `mode: subagent`. Loaded policy matched the contract: read roles (`factory-security-reviewer`, `factory-code-standards`, `factory-review-judge`) loaded `edit: * deny` then `subagent: * deny`; write roles (`factory-spec-builder`, `factory-code-build`) loaded `subagent: * deny` without an edit denial. The installed symlinks point into the invoking checkout's `dist/opencode`, byte-identical to this worktree's rendered agents, so the loaded definitions are this feature's output. v2.1.4 has no skill-listing debug command; the `~/.config/opencode/skills/factory` symlink resolves, and factory skill discovery evidence remains the historical v2.1.4 observation. Discovery establishes loading, not enforcement.

- **Model-backed dispatch — unverified.** No model calls were made; this task requires none. An actual orchestrator spawn invoking a named `factory-<role>` subagent through V2's foreground `subagent` capability has not been observed.

- **Runtime permission enforcement — unverified.** No runtime trial observed a tool call allowed or denied by the loaded rules. Loaded policy is configuration, not enforcement proof (DESIGN.md, "OpenCode V2 adapter").

No discovery or policy mismatch was observed, so delivery is not blocked by a runtime conflict. An observed permission or dispatch mismatch would be recorded here as a blocker with the version and mismatch, without weakening the rules.

## Supported V1 compatibility

This feature is native V2 adoption. Supported V1 agent and skill definitions remain intended to work through OpenCode's compatibility translation; the update does not claim former V1 factory definitions broke, and it implies no repair of them. The factory uses neither OpenCode's plugin nor server API; those interfaces are out of scope. Existing global and project install locations, skill resolution, question relays and model defaults/overrides carry over with no operator migration.

## Installer and rollback

`./install.sh --harness <name>|all` renders the named harness(es) and symlinks the skill and nine agent files into that harness's directories; re-run it after pulling. `./install.sh --harness <name> --uninstall` removes only symlinks that point into this tree and skips paths that are not symlinks. Rollback is by restoring the prior adapter/source and regenerating the distributions; no user configuration migration is involved on install, uninstall or rollback. Publication remains gated by factory approval.
