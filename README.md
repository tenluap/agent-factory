# claude-factory

A software factory for Claude Code. Run `/factory <feature>` in any repo with [SpecKit](https://github.com/github/spec-kit) installed, and the session becomes an orchestrator that takes the feature through grilling, the SpecKit spec flow, implementation, parallel reviews and your approval to a pull request. Runs are resumable: run `/factory` with no arguments to list unfinished runs.

## Install

```bash
./install.sh
```

This symlinks `skills/factory` into `~/.claude/skills/` and every `agents/factory-*.md` into `~/.claude/agents/`. Start a new Claude Code session afterwards so it picks them up. `./install.sh --uninstall` removes the links.

## Requirements

- Claude Code with subagents.
- In the target repo: git, SpecKit (`.specify/` plus the `speckit-*` skills), and `gh` authenticated for the PR step.
- In `~/.claude/skills` (or the repo): `grilling`, `domain-modeling`, `pr`.
- `impeccable` for UI reviews; the factory offers to install it the first time a run touches UI files.

## Layout

- `DESIGN.md`: every decision behind the flow. Change it first, then the files built from it.
- `skills/factory/SKILL.md`: the orchestrator loop.
- `skills/factory/references/`: run state and resume, the agent protocol, the findings shapes.
- `agents/`: spec-builder, code-build, five reviewers, review-judge, fixer.
