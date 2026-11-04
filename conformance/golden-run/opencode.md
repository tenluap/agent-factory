# Golden run: opencode

Evidence for FR-013/S14 on `opencode`. Run it against `conformance/fixture-repo/`
(initialised per its README, with a throwaway remote). Record each step
pass/fail in `conformance/golden-run-results.md`. Work only inside the fixture
and its worktrees; never the user's checkout.

## Checklist

- [ ] **Start**: run the factory on the fixture with a small feature
      ("greet accepts a greeting word"). Record the invoke command used.
- [ ] **Preflight**: every resolved skill named; a missing `.specify/` or
      speckit skill names the exact `specify init` command and offers to run it.
- [ ] **Grill**: the relay presents, accepts replies, and fast mode marks
      `auto` answers (visible later in the approver veto list).
- [ ] **Stages**: worktree, spec chain, implement each checkpoint-commit;
      `factory show <branch>` reports the digest at every step.
- [ ] **Pause at `review`**: stop the session cleanly before the review stage
      (`--stop-at review`), state `paused`.
- [ ] **Kill**: kill the session mid-`review` (no clean stop).
- [ ] **Resume on a second harness**: `factory resume <branch>` on harness
      `claude-code` (cross-harness leg; the Codex fallback is in `golden-run/codex.md`, see T008); the `resumed` entry lands, the recorded stage restarts, no
      question re-asked, no duplicate branch/worktree.
- [ ] **Approve**: the approver screen lists the veto list (auto answers,
      gate overrides); approve.
- [ ] **PR against the throwaway remote**: one PR, `pr-open` recorded once,
      `ended_at` set. Read-only roles stayed read-only where this harness
      enforces it.

## Headless procedure

- **Invoke**: `python3 tools/bench.py run --harness opencode --from-checkout [--model <provider/model>] --out <dir>`
  (the factory's own entry is `/factory <args>`; the driver runs `opencode run <prompt>`, with `-m` only when `--model` is given).
- **Isolation**: `--from-checkout` sets `XDG_CONFIG_HOME` to `<out>/harness-config` and renders under `<out>/home`.
  OpenCode's data directory (provider auth, session storage and logs) is not isolated and is shared by design; the driver never copies it.
- **Compatible model**: list models with `opencode models`, then pass `--model <provider/model>`. The default model has been rejected for the headless run, which is why an explicit model is required; record the rejection diagnostic if it recurs.
- **Scoped permissions**: OpenCode receives no Claude Code grant flags; read-only and shell rules come from the rendered agent `permissions`. The residual risk is the same as Claude Code's (shell access under the fixture) and the fixture is the control.
- **Headless smoke, pause, kill, resume, installed baseline, PR leg**: follow the same steps as `claude-code.md`, recording each as its own row in `golden-run-results.md`.
- **Cross-harness leg**: resume on `claude-code`; if that harness cannot take the run, use the Codex fallback in `golden-run/codex.md` and record the reason in the results document.
- **Provenance**: every result row names its `provenance.json` path.

## Capability notes for this harness

- Invoke: `/factory <args>` from an OpenCode V2 session; headless: the `bench.py run` command above (from `adapters/opencode/harness.md`).
- Read-only enforcement: enforced by the rendered agent `permissions` (read-only roles deny `edit`, every role denies `subagent`), per `adapters/opencode/harness.md`; confirm in the golden run before recording it.
- Extra setup arguments: `--from-checkout`, `--out <dir>`, `--model <provider/model>`; `--home <dir>` only without `--from-checkout`.
