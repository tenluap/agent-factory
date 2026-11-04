# Research: Assign factory PRs to the signed-in GitHub account

No `NEEDS CLARIFICATION` remained after grilling (Q1-Q7). The decisions below fix the mechanics the spec leaves open.

## R1 - Assignment in the creation request

- **Decision**: Append `--assignee @me` to the existing `gh pr create` call in step 9 item 3. No `gh pr edit`.
- **Rationale**: `gh pr create` resolves `@me` to the signed-in account server-side, so no username is read or asked (FR-001, FR-003). When the assignment part fails after GitHub created the PR, `gh` exits non-zero with the PR already present; the after-error lookup (R2) then finds and reuses it.
- **Alternatives**: separate `gh pr edit --add-assignee @me` (rejected by Q1: a second request with its own failure mode); asking for a login (forbidden by FR-003).

## R2 - Branch PR lookup command

- **Decision**: `gh pr list --head <branch> --state open --json url,assignees`. Exit 0 with `[]` means no open Branch PR; exit 0 with entries means reuse the first entry; a non-zero exit is a lookup failure.
- **Rationale**: The brief named `gh pr view <branch> --json url,assignees`. `gh pr view <branch>` exits non-zero both when no PR exists and when GitHub is unreachable, so it cannot satisfy FR-007 (never treat an unanswered lookup as "no PR"), and it can return a closed or merged PR, which the spec's edge case says must not be reused. `gh pr list ... --state open` separates the three outcomes by exit code and output and returns open PRs only. The intent of the settled answer (look up URL and assignees before and after creation) is unchanged.
- **Alternatives**: `gh pr view` plus stderr parsing (brittle, locale- and version-dependent); `gh api` GraphQL query (more text, same result).

## R3 - Retry bound and halt

- **Decision**: After a creation error, repeat the lookup; if it finds no PR, retry creation once; after a second creation error and a final lookup finding no PR, halt with the creation error as `--halt-reason`. Any failed lookup halts with the lookup error.
- **Rationale**: Mirrors step 9's existing "retry once" rule for the final push (ENG-24: bounded retries, duplicate-effect protection). Halts go through the existing halt policy; resume repeats lookup-then-create (FR-010).

## R4 - Assignment check

- **Decision**: After the run's PR is known, read the signed-in login with `gh api user --jq .login` and compare it with the Branch PR's `assignees[].login`. After a successful creation, the assignees come from one more Branch PR lookup. A missing login, a failed call or an absent assignee is an assignment problem: noted in-turn for item 8's `NOTIFY`, never persisted (FR-008, FR-009).
- **Rationale**: Uses the already-signed-in CLI; no credentials read or stored (ENG-25). In-turn noting matches how step 9 already carries a skipped retro to the final notice.

## R5 - Resume

- **Decision**: state.md Resume `pr` restarts step 9 from item 1; item 3's Branch PR lookup makes it idempotent. `git push -u` of an already-pushed branch is a no-op.
- **Rationale**: One path for first run, retry and resume (FR-010); replaces the old `gh pr view <branch>` rule, which could reuse a closed PR.

## R6 - Verification

- **Decision**: A text-contract unittest module `tools/tests/test_pr_publication.py` reads the core files; live GitHub behaviour is a manual runbook in `quickstart.md` (Q5).
- **Rationale**: `tools/tests/test_render_models.py` already reads core role text (`core/roles/design-to-code.md`, `core/roles/facets-advisor.md`), but those checks cover harness neutrality and rendering of role files. The publication contract is a separate concept with its own injected-failure fixtures, so it gets its own module. The suite already runs under `python3 -m unittest discover -s tools` with no new dependency.
