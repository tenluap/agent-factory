# Existing installer outcomes

No public contract changes.

- Success: an existing explicit FACTORY_HOME permits OpenCode installation; exit status is zero; skill and every expected role-agent path are symlinks; stdout includes fresh-session guidance.
- Conflict: an existing explicit FACTORY_HOME plus a regular file at the skill destination yields nonzero exit status and `resolve any existing file` in stderr; the file contents remain unchanged.
- Missing explicit home: existing home-policy tests continue to require failure naming the path, without linking agents or emitting a traceback.

Correct the test setup to satisfy success/conflict prerequisites without changing these outputs. See [spec.md](../spec.md).
