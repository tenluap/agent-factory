# Research: Close Orchestrator Bookkeeping Gaps

No NEEDS CLARIFICATION remained in the Technical Context. Each entry records one design choice.

## R1. Where the review counters are written

- **Decision**: `checkpoint review` sets `review.round`; `checkpoint fix` increments `review.fix_rounds`.
- **Rationale**: Constitution V (extend an existing writer); the `remediate` counters already use the same stage-guarded pattern (ADR 0006), which gives retry idempotency for free.
- **Alternatives considered**: a separate `review-record` command (new verb, rejected by the spec's Assumptions); an explicit `--round` flag on checkpoint (duplicates the verdict folders, which are already the source of truth).

## R2. Interaction with the design-run reservation

- **Decision**: skip the increment when `review.pending_design_fix.attempt == review.fix_rounds`. SKILL.md step 7 tells active design runs to checkpoint `fix` before clearing the reservation.
- **Rationale**: design-code-mapping.md §5 increments the counter before spawning; counting again at checkpoint would double-count. Ordering the checkpoint before the clear keeps the guard observable.
- **Alternatives considered**: always skip for design runs (breaks when no reservation exists); move the reservation increment into the CLI (out of scope; reservation writer unchanged).

## R3. How a verdict-raised question reaches the writer

- **Decision**: `answer --question '<json>'` with the full protocol question shape; `id` must equal `<qid>`.
- **Rationale**: matches `ledger-add --overrun '<json>'`; review-stage questions come from a verdict, not a spec-builder envelope, so the relay may hold no stored question.
- **Alternatives considered**: a `--question-file` path (adds a file to manage); a new `relay-add` command (new verb).

## R4. Relay record layout

- **Decision**: follows run 018's hand-written records:

  ```markdown
  # <stage>-<qid> (requires_user)

  - Stage: <stage>
  - Question: <qid>
  - Answer: <answer>
  - Origin: explicit | auto | cruise_override
  - Answered at: <ISO UTC>

  ## <title or text>

  <text, when title and text both present>

  ### Options
  - **A** · <label> - <description>
  ```

- **Rationale**: plans and fixers already cite this shape; options as a list keep legacy string options renderable verbatim.
- **Immutability**: the `- Answer:` line is compared on re-record: equal → no-op; different → exit 1.

## R5. File-name safety

- **Decision**: refuse `<stage>` or `<qid>` outside `[A-Za-z0-9_-]+` with exit 1 before any write.
- **Rationale**: both values form a path; stages are vocabulary words and qids are `Q7` / `R2-Q1`, so the rule rejects nothing legitimate.

## R6. Overrun excess rounding

- **Decision**: ceiling for both the excess and the total (`math.ceil`).
- **Rationale**: FR-011 and acceptance scenario 2 (300 001 ms → 1 s). A detected overrun never reads 0 s.

## R7. Round-1 reviewer budget key and flags

- **Decision**: config `budget.review_full_s` (default 600); CLI `--round <n>` or `--full` on `budget` and `ledger-add`. `full = (--full) or round == 1`. Result `max(normal, full_value)` for `REVIEWER_ROLES` only.
- **Rationale**: "full" names a full-diff review, covering round 1 and an escalated re-run with one flag; `max` honours a larger per-role value (FR-013 acceptance 3).
- **Alternatives considered**: per-round table in config (YAGNI); diff-size scaling (out of scope per spec).
