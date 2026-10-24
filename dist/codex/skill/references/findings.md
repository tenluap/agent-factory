# Findings

## Reviewing

Every factory reviewer works the same way; only its lens differs.

- Inputs: `worktree`, `spec_dir`, `base` (the default branch), `round`; on every round after the first also `delta_base` (the previous round's checkpoint commit) and the previous round's `verdict.json` path.
- Scope: the change set. Without `delta_base`: `cd <worktree> && git diff <base>...HEAD`. With `delta_base` (a **delta review**): `cd <worktree> && git diff <delta_base>...HEAD`, reviewed together with the prior verdict — check that the fixes remove the verdict's `confirmed_blocking` findings and that the touched code introduces no new defect; findings from the prior round do not carry forward. Read surrounding code as needed; report only defects the in-scope change introduces or exposes.
- Commit metadata: a reviewer whose lens needs commit messages reads the run's commit log as well as the diff — `cd <worktree> && git log --format='%H%n%s%n%b%n--' <base>..HEAD` — because the diff carries no commit messages.
- Read-only: you edit nothing and commit nothing.
- Each finding carries evidence from the code: a finding you cannot point at is not reported.
- Exhaustive: every changed file is checked against every item of your lens before you finish.
- End with the report below as your final fenced `json` block.

## Reviewer report

Every reviewer ends with one fenced `json` block:

```json
{
  "reviewer": "security",
  "round": 1,
  "summary": "one sentence",
  "findings": [
    {
      "id": "SEC-1",
      "severity": "high",
      "blocking": true,
      "file": "src/Services/Foo.cs",
      "line": 42,
      "summary": "one sentence defect statement",
      "evidence": "the code or behaviour that proves it",
      "fix": "the concrete change"
    }
  ]
}
```

- `severity`: `critical` | `high` | `medium` | `low`.
- `blocking`: the reviewer's call; `critical` and `high` are blocking unless the reviewer says why not. **Override — the judgement-call severity ceiling**: a finding based only on design or style guidance, including `ENG-7`..`ENG-10`, is at most MEDIUM and never blocking, for both reviewer and judge. Lower an overrated preference to MEDIUM rather than dropping it. Similar-looking code, a preferred architecture, a missing speculative interface or a coverage percentage alone does not prove a defect. A demonstrated correctness, security, integrity, resource-limit or stated-performance failure is rated by consequence and cites its concrete requirement or applicable rule, such as `ENG-23`..`ENG-26`; a design preference does not lower that defect's severity. The existing test, red-proof and seam requirements (`ENG-1`..`ENG-5`) keep their enforcement. An `ENG-6` reuse finding establishes that the code represents the same knowledge and explains the consequence of duplicating it; duplication alone is not automatically HIGH or blocking.
- A finding resting on an engineering rule names that rule's `ENG-n` id from `<F>/references/engineering.md` in its `evidence`.
- A finding about a commit has no file and no line: `file` holds the commit sha, followed by the task id or finding id where one applies (for example `a1b2c3d (T007)`), and `line` is omitted or `0`.
- `id` prefixes: `SEC` security, `STD` code-standards, `SPEC` spec-conformance, `UI` ui-reviewer, `UX` ux-reviewer.
- No findings: `"findings": []`.

## Judge verdict

```json
{
  "round": 1,
  "verdict": "fix",
  "confirmed_blocking": [ { "severity": "high", "file": "...", "line": 42, "summary": "...", "evidence": "...", "fix": "...", "sources": ["SEC-1", "STD-3"] } ],
  "advisory": [ { "severity": "low", "file": "...", "line": 7, "summary": "...", "fix": "...", "sources": ["UX-1"] } ],
  "rejected": [ { "id": "UX-2", "reason": "why it is not real" } ],
  "escalate": { "reason": "the fix diff touches src/X.cs, named by no finding or Adjacent line" }
}
```

- `verdict`: `pass` (no confirmed blocking findings) or `fix`.
- `escalate` (optional, delta reviews only): present when the fix diff touches a file named by no prior `confirmed_blocking[].file` and no fix commit's `Adjacent:` line. The orchestrator re-runs the round once in full review; a full review never carries `escalate`.
- Every reviewer finding id appears exactly once across `confirmed_blocking[].sources`, `advisory[].sources`, and `rejected[].id`.
- An `advisory[]` entry derived from an engineering finding keeps its `ENG-n` citation without any shape change: the id is named in the entry's existing `summary` (one token) and the reviewer finding carrying the full evidence is linked through its existing `sources`; no field is added to the verdict.
- A finding capped at the ceiling is **advisory**: no **verdict-driven fix round** acts on it. It reaches the user in the verdict's `advisory[]` list with its `ENG-n` citation, and the user's route to having it fixed is the approver's existing "Request changes" — the fixing role implements such a request exactly as asked, like any other change request.
