# Research

## Existing home policy

Decision: create each affected test's explicitly configured factory home before invoking install.sh.
Rationale: `InstallHomePolicyTests` already verifies rejection of nonexistent explicit homes; the two old fixtures fail before their intended installation paths.
Alternatives considered: relaxing installer validation would violate accepted scope; a shared helper would add unnecessary abstraction for two lines of setup.

## Meaningful expected roles in a clean checkout

Decision: compute expected OpenCode role filenames from `core/roles/*.md`, with an explicit nonempty assertion.
Rationale: `tools/render.py:roles` renders each source role and `adapters/opencode/adapter.json` declares `factory-{role}.md`. Checkout dist is ignored and can be absent, so its glob is not a reliable oracle. Source roles are independent of the installed output under test.
Alternatives considered: rendering checkout dist first creates an unrelated prerequisite; using installed output as expectations cannot detect missing roles; hardcoding all role names duplicates the role inventory.

## Verification

Decision: reuse existing subprocess tests and full repository checks.
Rationale: orchestrator reproduced the two failures with the focused unittest command; no new product behavior or test seam is introduced.
Alternatives considered: adding another regression suite would duplicate existing behavioral coverage.

No unresolved technical questions. Sources: `tools/tests/test_install.py`, `install.sh`, `tools/render.py`, `adapters/opencode/adapter.json`, `.gitignore`, and the accepted brief.
