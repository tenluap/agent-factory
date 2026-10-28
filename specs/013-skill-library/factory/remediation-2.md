# Remediation log — 013-skill-library, pass 2

- C1: spec.md Assumptions gains a line stating that the `~/.claude`, `~/.zcode` and `~/.config` prefixes in each `RESOLVE` search order denote the harness home, so home overrides are honoured by the harness and SC-001 holds without a `RESOLVE` edit (FR-012 kept).
- U1: tasks.md T011 now induces the failed-copy case with a failing `cp` shim first on the sandbox `PATH` instead of an unreadable file, so it also works when run as root.
- U2: research.md R3 documents the prefix-match limitation (links from another checkout/worktree or a moved checkout count as user-owned); tasks.md T001 (DESIGN.md) and T015 (README.md) now document it with the fix "remove the old link and re-run". No code change.
- I1: tasks.md T006 now states that a skill whose LICENSE or upstream cannot be obtained stops implementation and is escalated, rather than completing with fewer than six skills.
