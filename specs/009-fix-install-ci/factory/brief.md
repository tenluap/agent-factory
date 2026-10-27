# Fix installer CI

Fix the two OpenCode installer tests that supply a nonexistent explicit FACTORY_HOME, preserving the documented requirement that explicitly configured homes already exist.

- User accepted Q1: fix test setup and retain installer validation.
- Chain: lite, fast enabled.
- Create each affected test sandbox factory home before invoking install.sh.
- Preserve verification of installed skill and all role-agent symlinks, conflict diagnostics, and preservation of a conflicting user file.
- Existing public test seam: install.sh subprocess in a disposable HOME/XDG_CONFIG_HOME/FACTORY_HOME. Existing failing tests provide red proof; no new seam or product behavior is requested.
- Validate full unittest suite, all five harness renders, dist drift and bash syntax.
- Main moved to e743f2a since intake; dist is now ignored and generated on demand. Account for that in test expectations without changing installer policy.
