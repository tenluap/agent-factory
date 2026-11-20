# Golden run: copilot

Evidence for FR-013/S14 on `copilot`. Run it against `conformance/fixture-repo/`
(initialised per its README, with a throwaway remote). Record each step
pass/fail in `conformance/golden-run-results.md`. Work only inside the fixture
and its worktrees; never the user's checkout.

## Checklist

Run of 2026-11-04: Copilot CLI 1.0.105 (runtime log: 1.0.102-1), model
`claude-sonnet-5.5`, isolated `HOME`/`COPILOT_HOME`/`FACTORY_HOME`, every leg
driven non-interactively (`copilot -p`, answers relayed with `--resume <id> -p`).
Second harness: Claude Code. Throwaway remote: private
`tenluap/factory-golden-run-2026-11-04`; evidence on its
`evidence/copilot-2026-11-04` branch. The interactive `/factory` slash path was
not exercised.

- [x] **Start**: run the factory on the fixture with a small feature
      ("greet accepts a greeting word"). Record the invoke command used.
      *Passed only with a workaround.* `/factory …` sent through `-p` is not
      expanded: the skill's `disable-model-invocation: true` hides it from the
      model, so the model did the task directly on `main` and skipped every
      role (headless leg 1). The prompt that worked is "Read
      `<skill>/SKILL.md` and follow it exactly as the /factory command, with
      `$ARGUMENTS = …`".
- [ ] **Preflight**: every resolved skill named; a missing `.specify/` or
      speckit skill names the exact `specify init` command and offers to run it.
      *Failed as shipped.* `speckit_init` (`--ai copilot --ai-skills`) is
      rejected by specify 1.1.0 ("No such option: --ai"). With the working
      form, `--integration copilot --integration-options="--skills"`, patched
      into the scratch render, preflight ran `specify init` and resolved all
      skills. Headless runs also need `--add-dir` for every skill root and its
      symlink target, or path checks deny the reads (headless leg 2).
- [ ] **Grill**: the relay presents, accepts replies, and fast mode marks
      `auto` answers (visible later in the approver veto list).
      *Failed under `-p`.* No relay was presented. The orchestrator answered
      the plan's `requires_user` test-scope question itself (`auto: true`),
      then recorded its own `gate-override` when analyze flagged that as HIGH.
      The Claude Code reviewers caught it as a blocking finding (ENG-4). A
      plain `ASK` probe, by contrast, printed the question and exited 0 with a
      resume id. Interactive behaviour is untested.
- [x] **Stages**: worktree, spec chain, implement each checkpoint-commit;
      `factory show <branch>` reports the digest at every step.
- [x] **Pause at `review`**: stop the session cleanly before the review stage
      (`--stop-at review`), state `paused`.
- [x] **Kill**: kill the session mid-`review` (no clean stop).
      `kill -9` eight seconds after `reviews/round-1/` appeared, before the
      reviewer spawns; state left `running` at `review`.
- [ ] **Resume on a second harness**: `factory resume <branch>` on harness
      `claude-code`; the `resumed` entry lands, the recorded stage restarts, no
      question re-asked, no duplicate branch/worktree.
      *Partial.* The `resumed` entry landed, `review` restarted, and there was
      no duplicate branch or worktree. But `harness` stayed `copilot`:
      `cmd_resume` copies the stored value and no command sets it, so Claude
      Code's spawns are attributed to Copilot. The Claude Code leg used the
      maintainer's installed agents, which are older than this checkout.
- [x] **Approve**: the approver screen lists the veto list (auto answers,
      gate overrides); approve.
- [x] **PR against the throwaway remote**: one PR, `pr-open` recorded once,
      `ended_at` set. Read-only roles stayed read-only where this harness
      enforces it.
      PR #1. Read-only is not enforced on this harness (see below).

## Capability notes for this harness

- Invoke: `/factory <args>` interactively (untested). Headless: `copilot -p "Read <skill>/SKILL.md and follow it exactly as the /factory command, with $ARGUMENTS = <args>"`.
- Read-only enforcement: disclosed limitation. The agent `tools:` list is
  honoured (read roles get no edit/create tool), but `execute` is a full
  shell; a read-only role declined to write only because its instructions
  say so.
- Extra setup arguments: `specify init --here --integration copilot --integration-options="--skills"` (the adapter's `--ai` form fails on specify 1.1.0).

## Headless procedure

`tools/bench.py run` refuses `copilot`; until it gains a launcher, the 2026-11-04
run used a scratch driver that reuses bench's fixture preparation and swaps the
launch command (kept on the evidence branch as `golden-run/copilot_bench.py`).

- **Isolation**: override `HOME` as well as `COPILOT_HOME`, because
  `skills_root` is `~/.agents/skills`. Create `FACTORY_HOME` before
  `install.sh`. Authenticate with `COPILOT_GITHUB_TOKEN` (and `GH_TOKEN` for
  `gh`/git) from `gh auth token`; the isolated home has no stored login.
- **Launch**: `copilot -p <prompt> --model <m> --allow-all-tools
  --deny-tool 'shell(git push:*)' --deny-tool 'write(<factory checkout>/**)'
  --add-dir <out> --add-dir <factory home> --add-dir <skill dir>
  --add-dir ~/.agents/skills --add-dir ~/.copilot/skills
  --add-dir <checkout>/skills --log-dir <out>/copilot-logs
  --usage-output-file <out>/usage.json --share <out>/transcript.md`.
  `--allow-all-tools` grants tools, not paths. Set `TMPDIR` inside a granted
  directory: the orchestrator writes scratch files to `/tmp`.
- **Prompt**: drop `--stop-at` from `resume` (the command rejects it; the
  seeded state already carries `stop_at`).
- **Questions**: an `ASK` ends the `-p` turn with exit 0 and a resume id;
  answer with `copilot --resume=<id> -p "<answer>"`. Exit 0 is not success:
  score the state.
- **Usage**: `--usage-output-file` reports premium requests, AI credits and
  tokens for the whole session; the ledger's per-spawn `reported` stays null.
- **Scoring**: `python3 tools/bench.py score <state.json>`. Leg 3 scored
  `pass` (reached-approver, last-verify-green, no-blocking-findings,
  fixture-acceptance) with 9 delegated role spawns, the three reviewers in
  parallel, for 1 premium request.
