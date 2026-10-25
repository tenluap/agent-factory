# Data model: Factory skill routing

The "data" of this product is the run state, the relay question shape and the skill map. Every change below
is additive within `state.version: 3`; nothing existing is renamed, removed or re-interpreted (FR-006,
FR-017, SC-008). Prose contracts live in `DESIGN.md` and `<F>/references/skills.md`.

## Intake intent

Not persisted as its own field. It is decided in `SKILL.md` step 0 from the request text and, when
ambiguous, by exactly one relay question, and it is then visible in the run's first `stage` value
(`brainstorm` on the idea path, `grill` on the feature path) and in that question's saved relay answer
(FR-001, FR-002).

| Value | Trigger | First stage |
|---|---|---|
| exploration | open-ended idea wording, no settled solution | `brainstorm` |
| delivery | concrete feature/change wording, or a named existing spec | `grill` |
| ambiguous | neither set of cues, or both | one question decides, then as above |

## `state.stage`: one new value

`grill`, `worktree`, `specify`, ... gains **`brainstorm`**, placed before `grill`:

```json
{ "stage": "brainstorm", "status": "waiting_user" }
```

- Written in the **pending state** only (`${FACTORY_HOME:-~/.factory}/pending/<repo-name>-<slug>.json`):
  brainstorming runs before the worktree exists, so its artifacts and relay rounds live there and move into
  the worktree at step 3, unchanged from today's grilling (FR-004).
- `brief.md` beside the pending state carries the confirmed direction: the alternatives considered, the
  chosen direction and every decision already settled, so `grill` treats them as inputs (FR-003, FR-005).
- Resume of a pending `brainstorm` re-runs brainstorming with the existing brief and saved relay answers as
  its starting point, then continues into `grill`; any stage value an older run recorded still resumes
  exactly as before (FR-006, SC-008).

## Relay question: one new optional field

```json
{ "id": "Q12", "title": "...", "options": [], "recommended": "...", "requires_user": true }
```

| Field | Type | Default when absent | Meaning |
|---|---|---|---|
| `requires_user` | boolean | `false` (current behaviour) | Fast mode MUST NOT auto-answer this question; it is shown and waited on even when `mode.fast` is true. |

- The existing `state.analyze.pending_clarify` exclusion is unchanged and keeps working for questions that
  carry no `requires_user` field (FR-017).
- An answer to a `requires_user` question is stored like any other answer and never carries `"auto": true`.
- `bin/factory show` passes the field through verbatim (research.md, R2), so no CLI or schema version change
  is needed.

## Skill map entries

`state.skills` keeps its shape (logical name → absolute path, valid only on the harness that resolved them).
What changes is which names it may hold and when (FR-007, FR-008, FR-009, FR-010):

| Logical name | Resolved | Required |
|---|---|---|
| `speckit-*`, `grilling`, `domain-modeling`, `pr` | preflight | yes (unchanged) |
| `ponytail`, `tdd` | preflight, before the run commits to delivery | yes - a code-delivery run cannot start without them |
| `brainstorming` | preflight, only when intake intent is exploration | yes on the idea path; never resolved on the feature path |
| `impeccable` | step 6, only on a UI diff | no - the existing install offer, with a disclosed skip |

A missing required skill stops the affected work with setup guidance naming the logical name and the
directories searched; nothing is installed beyond the existing authorised `impeccable` offer (FR-011).
On resume, names absent from the map are resolved and, when `harness` differs, every path is re-resolved
before any role is spawned - the existing "Resume" step 1 behaviour, now also covering the conditional
names (FR-010).

## Seam confirmation

Persisted in `plan.md`, inside the "Test seams" section, as one line (research.md, R7):

```text
Confirmed: 2026-10-25 - Q12 accepted - seams: Seam 1, Seam 2, Seam 3
```

- Valid only while the plan's seam names match the list on that line; any added, removed or renamed seam
  invalidates it and a new `requires_user` question is relayed (FR-018).
- A plan whose every part is exempt lists no seam and carries no confirmation line: the question is skipped
  (FR-018).
- `code-build` and `fixer` read the seams, never the confirmation, and never ask the user: an unlisted seam
  is `ENG-4`'s stop-and-report failure (FR-019).

## UI change signal

`state.review.ui_diff` (boolean, unchanged) and `state.review.ui_reviewer_skipped` (unchanged) now record
the result of a widened classification of `git diff <base>...HEAD` (FR-020):

| Class | Examples |
|---|---|
| view markup and styles | `*.axaml`, `*.xaml`, `*.html`, `*.tsx`, `*.jsx`, `*.vue`, `*.svelte`, `*.css`, `*.scss`, SwiftUI/Compose views, `Views/`, `ViewModels/`, `components/`, `pages/` |
| design tokens and themes | token/theme/style resource files, token JSON, `Themes/` |
| UI assets | icons, images, fonts shipped to the interface |
| locale and string files | `*.resx`, `*.strings`, `*.arb`, locale JSON/YAML catalogues |
| user-visible copy in UI code | a diff whose only change is literal text a user reads in a view or view model |
| not a UI change | no user-visible surface touched - UI passes skipped |
