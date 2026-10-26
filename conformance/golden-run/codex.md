# Golden run: codex

Evidence for FR-013/S14 on `codex`. Run it against `conformance/fixture-repo/`
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
      `<second>`; the `resumed` entry lands, the recorded stage restarts, no
      question re-asked, no duplicate branch/worktree.
- [ ] **Approve**: the approver screen lists the veto list (auto answers,
      gate overrides); approve.
- [ ] **PR against the throwaway remote**: one PR, `pr-open` recorded once,
      `ended_at` set. Read-only roles stayed read-only where this harness
      enforces it.

## Capability notes for this harness

- Invoke: <fill from `adapters/codex/harness.md`>
- Read-only enforcement: <enforced | disclosed limitation>
- Extra setup arguments: <fill from `harness.md`, or "none">
