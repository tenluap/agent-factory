# OpenCode V2 adapter

Check whether the existing OpenCode harness works with V2 and make the smallest update needed for native V2 operation. Continue the already implemented adapter update through the factory workflow. The user explicitly said "continue" after the changes, runtime discovery result, and missing Codex SpecKit setup were reported.

- Use the lite chain with fast relay handling. The existing design settles the scope.
- Supported V1 definitions are intended to remain compatible; adopt V2 subagent/shell tools and ordered permissions without claiming V1 is wholly broken.
- Preserve role access intent, installed paths, configured models and all other harnesses' native agent output.
- Extend only the existing renderer; use Python standard-library unittest and no new dependency.
- Canonically render every harness. Every skill bundles the shared OpenCode reference.
- Keep core flow unchanged. Document the changed OpenCode contract in DESIGN.md, as required by the constitution.
- The prior implementation is saved externally under state.prior_work.handoff and remains in the invoking checkout. Do not edit that checkout. Apply the handoff only during implementation.
- Prior evidence: six renderer tests went red before implementation and now pass. OpenCode v2.1.4 loaded all nine global symlinked agents with native deny rules and discovered the global symlinked factory skill, using an isolated configuration and private server. Model-backed dispatch and runtime permission enforcement have not been exercised.
- The constitution documents build as rendering every harness and the post-commit distribution parity check as test -z "$(git status --porcelain -- dist/)". Also run python3 -m unittest discover -s tools -p 'test_*.py', bash -n install.sh, and git diff --check.
- The initial renderer test seam is render_agent(); the prior tests also exercise complete render() and adapter field mapping. Plan must name the actual public seams, and request the protected seam confirmation before new implementation.
- No UI or Pen reference work. No server/plugin integration in the product.
