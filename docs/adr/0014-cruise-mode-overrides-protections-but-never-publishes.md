# Cruise mode overrides protected decisions but never publishes

2026-11-04: fast mode already auto-accepts ordinary relay answers, but it deliberately never answers protected questions (`requires_user: true`, such as the plan's seam confirmation), `analyze.pending_clarify` questions, decision halts or one-off setup offers. That keeps an unattended run stopping many times before it has anything to show. Opt-in cruise mode (`--cruise`, stored as `mode.cruise`, implies fast) now answers all of them with their recommended answers. Each one is recorded with a `cruise_override` marker kept apart from the ordinary `auto` flag and listed first in the approver's veto list. The one boundary cruise never crosses is publishing. It stops at the existing approver gate, never records an approval, and the `pr` gate ignores any record carrying the marker, so nothing is pushed and no PR is opened until the user picks Approve.

Failures are not decisions. A red build after the retry, a second failure of the same agent, the stall cap, a missing or stale test seam found at implement or fix (`ENG-4`), and the other hard stops still halt and notify under cruise. A question with no usable recommendation is still put to the user.

## Considered options

- **Extend fast mode**: no new flag, but it would silently remove fast mode's protections from every existing run that relies on them.
- **New decision kind `cruise-override`**: the marker would be visible in the kind, but `kind` carries gate meaning (`answer`, `approved`, `gate-override`). A new kind would need new gate logic for analyze exhaustion and would collide with `answer` for protected relay answers.
- **Auto-approve the approver gate as well (full YOLO)**: no user input at all, but unreviewed overrides could then leave the machine. Rejected. Publishing stays the user's call.
- **Separate opt-in mode with an additive boolean marker** (chosen): runs without cruise behave exactly as before, older state files stay valid, and the user's Approve remains the only thing that can publish.

## Consequences

Setup offers and the ambiguous-intake choice are recorded as fixed-id decisions under the existing `grill` stage, and the `impeccable` install under `review`; the stage vocabulary is unchanged. A cruise override counts as accepted seam or design-exception scope only for the exact scope it answered, and a scope change still invalidates it. Harness permission prompts stay outside the factory: each adapter documents its no-prompt launch option, and cruise only tells the user about it.
