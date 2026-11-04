# Quickstart: validating the live-conformance unblockers

## Offline (this feature's acceptance)

```sh
for h in claude-code opencode codex copilot zcode; do python3 tools/render.py "$h"; done && bash -n install.sh
python3 -m unittest discover -s tools
test -z "$(git ls-files -- dist/)"
```

Expected: every harness renders, the full suite passes including `tools/tests/test_bench.py`, no `dist/` file is tracked. No test runs a real `claude` or `opencode` binary; the bench tests put stubs for both first on `PATH`.

Focused: `python3 -m unittest discover -s tools -p test_bench.py`.

## Manual spot check (no tokens)

Put a stub `claude` that prints its arguments first on `PATH`, then:

```sh
python3 tools/bench.py run --harness claude-code --from-checkout --model sonnet --out /tmp/bench-check
cat /tmp/bench-check/provenance.json /tmp/bench-check/harness.log
```

Expected: `harness.log` shows the prompt after `-p`, the `--add-dir` grants and the scoped `--allowedTools`; `provenance.json` matches data-model.md with `render.mode: checkout`.

## Live legs (after merge, token-spending)

Follow `conformance/golden-run/claude-code.md` and `conformance/golden-run/opencode.md`; record one row per leg in `conformance/golden-run-results.md`. See [contracts/bench-cli.md](contracts/bench-cli.md) for options.
