# Remediation — pass 3

Base: `specs/003-zcode-harness/factory/analyze-3.md`. All edits in place; no artifact regenerated.
Canonical wrapper, now written once in `plan.md` and quoted character-for-character everywhere:

```
env -u CLAUDE_HOME -u CODEX_HOME -u COPILOT_HOME -u ZCODE_HOME -u XDG_CONFIG_HOME FACTORY_HOME=/nonexistent
```

| ID | Severity | Resolution |
|----|----------|------------|
| C1 | HIGH (blocking) | **Fixed.** `-u FACTORY_HOME` replaced by `FACTORY_HOME=/nonexistent` in every command: `plan.md` (Constraints → Canonical render environment, Seam 4), `tasks.md` (T001, T007, T011, T017, Notes bullet), `quickstart.md` step 2 `$CANON`. Prose follows: spec.md FR-018 now reads "every harness home variable unset … and the factory configuration-home variable pointed at a location holding no configuration file", with the reason stated (the renderer falls back to `~/.factory/config.json` when the variable is unset and still merges `models.<harness>`); SC-003's parenthetical matches. plan.md Seam 3 now says the committed render "points `FACTORY_HOME` at a configuration-free path" instead of "unsets" it; the Constraints paragraph cites `os.environ.get("FACTORY_HOME", "~/.factory")` as the reason. quickstart step 2 carries the same note. Verified against `tools/render.py:41-43`: `config.exists()` is false for `/nonexistent/config.json`, so no override is merged; a full canonical render of all harnesses was run and succeeded. |
| C2 | HIGH (blocking) | **Fixed.** `-u COPILOT_HOME` added to the wrapper in all eight places listed above. plan.md's Canonical render environment paragraph states why (`adapters/copilot/adapter.json` resolves `{home}` from `COPILOT_HOME`, default `~/.copilot`, so a contributor with it set rewrites every `dist/copilot/agents/factory-*.agent.md` body). quickstart's "Without `$CANON`" paragraph now lists `COPILOT_HOME`; spec.md FR-018 says "all of them, including the one the Copilot adapter reads". plan.md Seam 4's failure sentence reworded to "any harness home variable set, or any `models.<harness>` entry in their own factory config". Not edited here: `factory/state.json` `commands.build` (orchestrator-owned, already corrected). |
| C3 | LOW | **Fixed.** tasks.md T012 citation changed from `` `README.md:72` `` to `` (`README.md:71`, the "SpecKit set up" bullet) `` so the reference survives line drift. |
| C4 | LOW | **Fixed.** `docs/adr/0005-the-rendered-distribution-is-tracked-in-git.md`, chosen option, gains a sentence recording that the gate is conditional on the render environment: the tracked distribution is the one produced in FR-018's canonical environment, and a non-canonical local render must be reverted with `git checkout -- dist/` or re-rendered canonically before the check is trusted. |

Deferred to clarify: none. No finding needed a user decision.

## Word budgets after remediation (`wc -w`)

| Artifact | Before | After | Budget |
|---|---|---|---|
| `spec.md` | 2451 | 2508 | 3000 |
| `plan.md` | 1767 | 1861 | 2000 |
| `tasks.md` | 2499 | 2493 | 2500 |

`tasks.md` had 1 word of headroom and the wrapper edits cost +1 word per occurrence (5) plus the T012
citation, so three offsets were taken inside the same tasks, with no loss of a checkable signal:

- T011: "If an earlier local render or install ran with a harness home or `FACTORY_HOME` set" → "… ran
  outside the canonical environment".
- T017: the inline `grep -c '^/dist/$' .gitignore` / `git ls-files dist/ | wc -l` restatement → "quickstart
  step 2's tracking checks still hold" (both commands are still spelled out in T001 and quickstart step 2,
  which T017 runs).
- Notes: "Any render or `install.sh` run with those set" → "Any non-canonical render or `install.sh` run".
