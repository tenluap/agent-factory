# Remediation pass 1 (analyze-1.md)

- C1: spec.md Quality "Isolation" and plan.md Constraints narrowed to the factory home and harness configuration (SC-004 wording), stating OpenCode's data directory (auth, sessions, logs) is shared by design; research.md R4 "Credentials" and T008 isolation item say the same.
- U1: T003 Implement and a new plan.md quality bullet derive the isolated skill directory from the adapter's raw `skill_dir` template (`render.ADAPTERS`) formatted with `home=<out>/harness-config`; no `os.environ` mutation, no `tools/render.py` change.
- G1: T007/T008 name all four placeholders (Invoke, Read-only enforcement, Extra setup arguments, `<second>`); done check is `grep -nE "<(fill|enforced|second)" <file>` empty.
- G2: T003 Red adds a Claude Code checkout run with `--model sonnet` asserting the model option and isolated env.
- U2: T002 sandbox makes `CLAUDE_HOME/skills/factory` a symlink to a directory outside `<out>` and asserts two distinct `--add-dir` entries; contracts/bench-cli.md states an absent skill directory is not granted; T002 Implement and T005 (existing "installed factory absent" path) carry it. Seams and failure paths unchanged.
- S1: T007 states the residual risk of `Bash(python3:*)`/`Bash(git:*)` and that the grant is for disposable bench runs only.
- R1: research.md R2 trial-time check extended to checkout mode (repo-layer skill links resolve into the checkout); T007 smoke step records it for both modes.
- I1: T009 states the per-leg table is the record for claude-code and opencode live trials; the per-adapter table stays the capability-tier summary and its two rows reference the per-leg table.
