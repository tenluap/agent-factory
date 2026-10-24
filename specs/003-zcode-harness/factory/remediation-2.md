# Remediation log — pass 2

Every finding in `factory/analyze-2.md` was fixed in place; nothing was regenerated and no finding was
deferred to clarify. `pending_clarify` is empty.

| ID | Severity | Disposition |
|----|----------|-------------|
| B1 | HIGH (blocking) | fixed |
| B2 | HIGH (blocking) | fixed |
| B3 | HIGH (blocking) | fixed |
| M1 | MEDIUM | fixed |
| M2 | MEDIUM | fixed |
| L1 | LOW | fixed |

## B1 — `adapter.json` without `harness.md` breaks every harness's render

Confirmed against `tools/render.py:97-98` (`for other in known(): shutil.copy(ADAPTERS/other/"harness.md", …)`).

- `tasks.md`: **T008 moved from Phase 4 into Phase 3**, immediately after T004 (ID unchanged, per the
  existing "IDs are not renumbered" convention). T004 now states it turns T003 green for **Seam 1 only**,
  names the `FileNotFoundError` that follows if `harness.md` is missing, and requires T004+T008 to be one
  commit. Phase 4 carries a pointer note where T008 used to be; T009/T010 continue to extend the same file.
- `tasks.md`: Phase 3 Goal and Independent Test now say both adapter files are created there; dependency
  list reads `T003 → T004 → T008 → T005 → T006` for US1 and `T007 → T009 → T010 → T011` for US2, with
  US2 depending on T004 + T008; the Notes commit rule says T004 and T008 share one commit.
- `plan.md`: Seam 2 now states that `known()` counts any folder holding `adapter.json` and that `render()`
  copies every known adapter's `harness.md` into every skill tree, so Seam 2 goes green only once both
  files exist and no ordered step may leave the folder half-built.

## B2 — recognition line dropped the checkable signal

- `tasks.md` T008 now quotes `data-model.md` §2 verbatim: "you are ZCode (Z.ai's coding agent, desktop app
  or CLI): `ZCODE_HOME` is set or `~/.zcode` exists, and you have the Agent, Bash, Read, Edit and Skill
  tools." — with an explicit note that FR-012 and clarification 8 require the checkable signal, so
  self-description plus a tool list is not enough.

## B3 — environment-dependent render vs. the tracked-`dist/` gate

Canonicalised exactly as the report's recommendation proposed (no user decision needed; the settled
"track and commit `dist/`" answer is preserved, not overturned).

- `spec.md` FR-018: adds the **canonical render environment** — every harness home variable and the
  factory configuration-home variable unset — as a requirement on the committed distribution, plus the
  rule that any render/install run with those set must be reverted before the check is trusted.
- `spec.md` SC-003: the difference check is stated against a canonical render and therefore holds on any
  contributor's machine. SC-006: "fresh canonical render".
- `plan.md`: new **Canonical render environment** paragraph in Constraints naming
  `env -u CLAUDE_HOME -u CODEX_HOME -u ZCODE_HOME -u XDG_CONFIG_HOME -u FACTORY_HOME …` and the
  `git checkout -- dist/` recovery; Testing line, Seam 3 (the `model:` key risk from a `models.zcode`
  override) and Seam 4 updated to the canonical form.
- `tasks.md`: T001 and T011 run the render inside the `env -u …` wrapper; T001 adds a canonical-render
  confirmation; T007 asserts after a canonical render; T011 requires `git checkout -- dist/` and a
  canonical re-render if an earlier local run dirtied the tree; T017 adds the non-canonical-render
  sensitivity check; T018 requires `git checkout -- dist/` plus a clean gate after the plain install and
  after the `ZCODE_HOME=/tmp/zc` override (because `install.sh` renders). A Notes bullet records the rule.
- `quickstart.md`: step 2 defines `$CANON`/`$RENDER` and explains the failure mode; step 4 restores the
  canonical render after each install.

## M1 — README line mixing `--ai` with `--integration`

`tasks.md` T012 now requires ZCode's setup as **its own sentence** after the existing requirement line
(`README.md:72`), explicitly **not** as another value of the `--ai <...>` enumeration (a flag family
specify-cli 1.1.0 no longer has), and carries research R4's note that the other harnesses' recorded form
is out of scope for this feature.

## M2 — T003's ambiguous deliverable

`tasks.md` T003 reworded to "run the Seam 1 and Seam 2 commands already written in quickstart.md steps 2-3
and record their failure output", matching T005's wording.

## L1 — ADR 0005 and the CONTEXT.md line already exist

`plan.md` gains a note under "New files, abstractions and dependencies (ENG-10)": both were written on
this branch by the domain-modeling step, so no task creates them — T001 implements the ADR's decision and
T014 verifies the `CONTEXT.md` line.

## Word budgets after the edits

`wc -w`: `spec.md` 2451/3000, `plan.md` 1767/2000, `tasks.md` 2499/2500. The tasks additions were offset
by trimming redundant prose (Phase notes, T002/T005/T006/T009/T010/T013/T014/T018 wording, Implementation
Strategy, Parallel Opportunities); no requirement, task, seam, exemption or FR/SC reference was dropped.
