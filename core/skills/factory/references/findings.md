# Findings

## Reviewing

Every factory reviewer works the same way; only its lens differs.

- Inputs: `worktree`, `spec_dir`, `base` (the default branch), `round`.
- Scope: the change set, `cd <worktree> && git diff <base>...HEAD`. Read surrounding code as needed; report only defects the change introduces or exposes.
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
- `blocking`: the reviewer's call; `critical` and `high` are blocking unless the reviewer says why not.
- `id` prefixes: `SEC` security, `STD` code-standards, `SPEC` spec-conformance, `UI` ui-reviewer, `UX` ux-reviewer.
- No findings: `"findings": []`.

## Judge verdict

```json
{
  "round": 1,
  "verdict": "fix",
  "confirmed_blocking": [ { "severity": "high", "file": "...", "line": 42, "summary": "...", "evidence": "...", "fix": "...", "sources": ["SEC-1", "STD-3"] } ],
  "advisory": [ { "severity": "low", "file": "...", "line": 7, "summary": "...", "fix": "...", "sources": ["UX-1"] } ],
  "rejected": [ { "id": "UX-2", "reason": "why it is not real" } ]
}
```

- `verdict`: `pass` (no confirmed blocking findings) or `fix`.
- Every reviewer finding id appears exactly once across `confirmed_blocking[].sources`, `advisory[].sources`, and `rejected[].id`.
