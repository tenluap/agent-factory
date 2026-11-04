# Golden run: claude-code

Evidence for FR-013/S14 on `claude-code`. Run it against `conformance/fixture-repo/`
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
      `opencode` (the Codex fallback is in `golden-run/codex.md`, see T008); the `resumed` entry lands, the recorded stage restarts, no
      question re-asked, no duplicate branch/worktree.
- [ ] **Approve**: the approver screen lists the veto list (auto answers,
      gate overrides); approve.
- [ ] **PR against the throwaway remote**: one PR, `pr-open` recorded once,
      `ended_at` set. Read-only roles stayed read-only where this harness
      enforces it.

## Headless procedure

- **Invoke**: `python3 tools/bench.py run --harness claude-code --from-checkout [--model <m>] --out <dir>`
  (the factory's own entry is `/factory <args>`; the driver sends `/factory resume <pending> --stop-at approver`).
- **Isolation**: `--from-checkout` renders this checkout under `<out>/home` and `<out>/harness-config`
  (`CLAUDE_CONFIG_DIR` and `CLAUDE_HOME` point there). Log in once with `claude` inside that config, or put
  `ANTHROPIC_API_KEY` there. The driver never copies credentials from your home directory.
- **Scoped permissions**: the launch is `claude -p <prompt> --add-dir <out> [--add-dir <skill dir>] --allowedTools Read Edit Write Agent Skill Bash(git:*) Bash(python3:*) Bash(<skill dir>/bin/factory:*)`. There is no bypass mode and no bare `Bash` entry.
  Residual risk: `Bash(python3:*)` and `Bash(git:*)` permit arbitrary code (for example `python3 -c` or git config hooks), so the grant is for disposable bench runs only; confinement to the throwaway fixture is the control.
- **Headless smoke**: run the invoke command, then record in `golden-run-results.md` the exit status, `<out>/provenance.json` path and whether the run reached `reached-approver`.
  Record separately, for checkout mode and the installed baseline, whether library skills outside the grant (checkout mode: repo-layer skill links that resolve into the checkout) were readable under the bare `Read` rule (research R2).
- **Pause, kill, resume**: pause with `--stop-at review`; kill the session mid-`review`; resume with `factory resume <branch>` on the second harness (above).
- **Installed baseline**: a separate run without `--from-checkout` (the maintainer's installed factory). Record it as its own result row; it is never mixed with checkout results.
- **PR leg**: against a private `tenluap/factory-golden-run-<date>` created at trial time and kept as evidence.
- **Provenance**: every result row names its `provenance.json` path; `bench.py score` reads it beside the fixture.

## Capability notes for this harness

- Invoke: `/factory <args>` from an installed session; headless: the `bench.py run` command above (from `adapters/claude-code/harness.md`).
- Read-only enforcement: disclosed limitation. The headless grant is run-wide (`Edit` and `Write` are allowed for the session), so read-only roles are constrained only by their rendered agent tool lists; check `<out>/home/dist/claude-code/agents/` before recording this as enforced.
- Extra setup arguments: `--from-checkout`, `--out <dir>`, optional `--model <m>`; `--home <dir>` only without `--from-checkout`.
