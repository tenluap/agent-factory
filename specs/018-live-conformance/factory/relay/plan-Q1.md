# Plan relay Q1 (requires_user) — accepted test scope

Answer: A (accepted explicitly by the user on 2026-11-04; not auto).

Seams and required injected failure paths:
1. `bench.py run` CLI (subprocess; stub `claude` and `opencode` first on PATH; sandboxed HOME, CLAUDE_HOME, XDG_CONFIG_HOME, FACTORY_HOME). Failure paths: isolated install fails (stub `bash` exits non-zero) -> exit 1, no harness launch; harness exits non-zero -> exit 1 with provenance.json already written; harness `--version` fails -> recorded unavailable; installed factory absent -> recorded unavailable; selected harness executable missing -> manual-fallback error, no output dir; `--from-checkout` with `--home` -> argparse error exit 2.
2. `bench.py score` CLI. Failure paths: no provenance.json -> missing marker, pass unchanged; malformed provenance.json -> missing marker; provenance repo mismatch -> missing marker; unreadable state -> missing marker.
3. `bench.checkout_provenance(path)` function (throwaway git repos). Failure path: not a git repository -> revision/changed_paths/diff_sha256 unavailable, no exception.

Exempt (documentation only): conformance/golden-run/claude-code.md, conformance/golden-run/opencode.md, conformance/golden-run-results.md, DESIGN.md benchmark bullet. Overridden: none.
