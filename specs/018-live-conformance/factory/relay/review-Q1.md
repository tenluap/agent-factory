# Review round 1 relay Q1 (requires_user) — tree_digest test seam

Answer: A (accepted explicitly by the user on 2026-11-04; not auto).

Raised by verdict round-1 confirmed blocking finding (SPEC-1, ENG-4): `bench.tree_digest` was under direct test without a confirmed seam.

Added seam (extends the accepted scope in plan-Q1.md; seams 1-3 unchanged):
4. `bench.tree_digest(root)` function. Failure paths:
   - root missing (not a directory) -> recorded `unavailable`, never the empty-tree sha256;
   - unreadable subdirectory under root -> recorded `unavailable`, never silently skipped;
   - symlink cycle under root -> walk is bounded (no hang) and records `unavailable`.

Overridden: none.
