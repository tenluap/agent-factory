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
