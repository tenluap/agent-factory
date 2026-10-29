# Design-code mapping

Load for a UI design run or when a factory run creates, references, or updates a Pen implementation reference, including a relevant mapped target encountered on resume. Apply on every supported framework. Standalone design work outside the factory is outside this contract.

## Source kinds and authority

Record `source_kind` in the design context: `pen`, `figma`, `image`, or `text`. Pen is authoritative under this contract. Figma is authoritative and mapped by observed node identity like Pen, after its capability resolves. Image or screenshot is a visual reference only: record its reference in the context and canonical map source record, create no node records, and judge fidelity against that image. For text-only restyles the existing code is the baseline; use `impeccable` guidance, require build/runtime evidence, and create no map records. Record mapping and fidelity as `not_applicable` with reason "no design reference"; attach before/after captures when capture is available. Apply node survey, coverage and identity requirements below only to node-based sources; image fidelity still requires a matching rendered comparison.

## 1. Resolve and persist the target

The orchestrator owns user decisions. For Pen resolve `pen-design` through the adapter and persist its path in `state.skills`; for Figma resolve its capability. Missing guidance stops affected work with setup guidance, without installing it automatically. Read the applicable backend documentation once. Discover supported inspection/export/identity capabilities instead of assuming a file format, node API, or revision API. A source content hash identifies a snapshot, not otherwise unavailable node IDs. Missing required inspection capability blocks verified implementation.

Resolve source, target, framework/project, existing map, and launch/capture commands from the request, saved active-feature context, or a uniquely matching map entry. Relay ambiguity; an open design application is not authority to choose a target. Use observed source-qualified node IDs and stable code file/symbol/resource anchors. Names and line numbers alone cannot establish identity.

Before the worktree exists, keep design context in the pending brief/state; write nothing to the invoking checkout. After worktree creation, save `<spec_dir>/factory/design/context.json` and pass its repository-relative path through `state.design.context` to every fresh role. Keep the pending context reference pointing to the pending brief until that move. Context holds source references, target scope, framework guidance, survey/reference paths, launch/capture commands, capture configuration, approved departures, and unresolved decisions. Inventory lives in the canonical map, not in state or a second map.

Use this small additive state field (artifact paths are repository-relative after worktree creation):

```json
{
  "design": {
    "mode": "implementation",
    "context": "specs/016-feature/factory/design/context.json",
    "map": "docs/design-code-map.json",
    "evidence": "specs/016-feature/factory/design/comparison.json",
    "status": "unverified"
  }
}
```

`mode` is `design-only` or `implementation`. `status` is `planned`, `unverified`, `verified`, `blocked`, or `exception-accepted`. Paths can be `null` until the corresponding artifact exists. Absence of `design` in an older state means no recorded activation; activate if a Pen implementation reference is actually encountered. Design-only work records source and targets; code coverage, app runtime, and app fidelity are not applicable until implementation starts. Run other applicable repository checks and use existing plan exemptions for design-only artifacts.

Done when the target is unique, scope/authority are settled, and context is persisted or a specific missing prerequisite is recorded.

## 2. Survey and plan coverage

Survey the complete requested subtree and referenced component definitions, relevant instances, active-theme variables/tokens, and assets. Cover child order, geometry, layout/sizing, gaps/padding, typography/wrapping, visibility, styles/effects, exact icons, dependencies, and overrides. Capture the reference at the planned application viewport, state, theme, DPI/zoom/scale. Save the scoped survey and capture settings in `factory/design/`.

Reuse a survey only when reliable source evidence establishes it is unchanged; otherwise refresh affected targets/dependencies on new runs, resume, or suspected external change. A timestamp alone is insufficient. Check anchors against current code. Code changes can invalidate rendered evidence without invalidating an unchanged design survey. Mark affected previously validated records stale before editing. Missing IDs require an identity decision; never silently reassign by name.

The spec/plan/tasks make coverage, capture settings, permitted departures, and the three gates below explicit acceptance requirements. Bootstrap an existing implementation's mapping for requested scope/dependencies before updating it. Reuse matching project controls/resources, one canonical implementation per explicit design component, and actual per-instance overrides. A primitive can map to its containing component. Select the smallest correct abstraction; avoid requiring one control per node. For Avalonia, also read [framework guidance](design-code-mapping-avalonia.md); other stacks use their available documented framework/capture guidance under these same gates.

Done when all scoped nodes/dependencies and exact supported values are surveyed, or gaps are explicitly blocked, and the plan records verification and component ownership.

## 3. Maintain one canonical map

Extend the repository's existing canonical map; otherwise create `docs/design-code-map.json`. Preserve unrelated entries and schema fields. New maps use this version-2 shape (version 2 distinguishes multi-source maps from the supplied agent's single-source version 1):

```json
{
  "version": 2,
  "sources": [],
  "components": [],
  "instances": [],
  "nodeMap": [],
  "removals": [],
  "exceptions": [],
  "unmappedDesignNodes": [],
  "orphanedCode": []
}
```

- Sources: local map key `sourceId`, repository-relative file or external reference, observed document/target IDs, reliable revision/fingerprint (or an explicit unavailable value), survey/reference/evidence paths, and capture settings. A locally assigned `sourceId` distinguishes sources; it is never a fabricated backend node/revision ID.
- Components: `sourceId`, observed `designId`, `designName`, `designPath`, `kind`, `code` (`project`, `file`, `symbol`, `anchor`), instance IDs/count, overrides, tokens, dependencies, and status.
- Instances: `sourceId`, observed `designId`, `componentId`, `parentDesignId`, overrides, code anchor, and status.
- Node coverage: `sourceId`, observed `designId`, parent, `coveredBy` component or code anchor, and status. Every scoped node is covered or explicitly accounted for; reverse lookup uses these same records.
- Removals/exceptions: source/node/code association, reason, disposition, evidence reference, and explicit user decision when required. Preserve unexplained unmapped nodes and orphaned code as outstanding gaps.
- Record status: `planned`, `implemented`, `validated`, `stale`, or `unmapped`. Only current passing evidence earns `validated`; an accepted exception retains failed/missing gate information and does not earn that status.

Keep an existing version-1 schema where possible. If migration to version 2 is necessary, preserve all `designSource` data in its authoritative `sources` record and associate old entries with that actual source; record the migration in context. Preserve unknown fields and unrelated inventory. Do not maintain two live source inventories, guess missing node identities, or discard a map because it uses another schema.

Write planned records after survey and update once per dependency batch: tokens/assets → canonical components → parent composition. Inspect affected shared consumers before editing; relay a scope decision before visual changes outside agreed scope. Capture runtime evidence after coherent runnable batches instead of per primitive. Initial validation is not permission for unbounded visual repair; feed mismatches into the shared queue below.

Default updates to design → code. An explicit request is required to edit the source design. If both design and code changed, relay conflicting changes before choosing authority. Remove only in-scope presentation exclusively owned by a removed design element; shared impact, discarded application behavior, or feature conflicts require a decision. Record deliberate removals to prevent stale entries from recreating them.

Done when current implementation, instances/overrides, coverage, removals, and exceptions are accurately represented, even when their recorded status is blocked/unverified.

## 4. Gather and verify evidence

Commit the canonical map, the local design snapshot used, scoped reference/runtime captures, and metadata under `<spec_dir>/factory/design/`. Copy an external local source into this evidence directory when necessary; retain its origin in context. An externally hosted design keeps its external source reference plus an exported baseline. Use repository-relative artifact paths. Limit captures/surveys to requested scope and impacted dependencies.

During the run, Pen design evidence lives under `specs/<branch>/factory/design/`. At run end, `factory drop` moves it to `docs/design/<branch>/` and rewrites its references in `docs/design-code-map.json` in the drop commit.

`comparison.json` records each target, current source revision/fingerprint, code identity (relevant file content fingerprints, or commit plus dirty-file fingerprints), survey/capture paths and configuration, each gate's result/evidence, actual mismatches, exceptions, and remaining gaps. Capture settings include viewport, UI state, theme, and applicable DPI/zoom/scale. Final identity must describe the compared code, not require a self-referential commit hash. Reject stale or missing artifacts as current proof. Code/source/configuration changes invalidate affected evidence and previously scoped exceptions.

| Gate | Required result for verified implementation |
|---|---|
| Build/runtime | Affected project builds, relevant tests pass, target runs without relevant binding/resource/runtime errors. Reuse still-current successful checks. |
| Mapping | Complete scoped coverage or explicit approved exclusions; anchors resolve; canonical components/instances/overrides agree; no unexplained stale/unmapped/orphaned records. |
| Fidelity | Exact supported values plus current rendered comparison against the reference at matching settings. Check composition, spacing, typography, content, icons, visibility, clipping/overflow, and relevant sizing behavior. Platform rasterization differences are acceptable; other departures require explicit disposition. No universal pixel threshold. |

For each gate record `passed`, `failed`, `unavailable`, or `stale`, and a concrete evidence path or gap. `not-applicable` is allowed with a reason for a design-only task; text-only mapping and fidelity use `not_applicable` with the reason above. A populated map, green build, static desktop review, optional impeccable skip, or visual preference alone cannot establish fidelity. The orchestrator independently checks identities, required fields, artifact/anchor existence, and results, and inspects the actual reference/runtime images against the fidelity criteria; repeat invalid/unsupported checks with supported tooling. Reviewers inspect the same evidence against the requirement; do not treat a role's success envelope or metadata alone as independent proof.

Report design results in the existing envelope's optional `design` field (protocol.md). A well-formed failed/unavailable design gate is a product verification result, not an agent crash to retry blindly. Preserve task/role failures and unfinished task boxes; an exception never pretends an unfinished task was implemented.

Done when each required gate has current passing evidence or an explicit failed/unavailable/stale result, and each legitimately not-applicable gate has its required reason. Set implementation status `verified` only when every applicable gate passes and every legitimately not-applicable gate carries its required reason; a text-only run needs no waiver for its mapping and fidelity gates.

## 5. Repair, exceptions, and handoff

Deduplicate map, visual, and other review findings by target/anchor and observed defect. Spec-conformance checks the mandatory gates even if impeccable/UI review is unavailable; UI review adds rendered comparison where available. A concrete approved-reference violation cites its requirement and evidence and is not capped as a styling opinion. A judge `pass` cannot override missing mandatory evidence.

All automatic mapping/visual repairs share `review.fix_rounds` (maximum two) with ordinary fixes. Before each active-design automatic fix, increment it, save `review.pending_design_fix` as `{ "attempt": <counter>, "round": <review round>, "verdict": <relative path> }`, set `stage: fix`, and persist before spawning. After a completed attempt clear the pending marker before verification/re-review. Resume an interrupted pending attempt with its saved verdict and current uncommitted work; do not reserve another attempt or reset the counter. Agent-crash retries keep the same reservation and existing failure limit. A blocked/failed attempt preserves precise gaps and stops for the contract's disposition; never treat uncommitted work as reviewed by a committed diff.

Fresh roles, tool/backend changes, escalation to full review, or renamed findings do not reset the limit. Reuse this queue for pre-review visual mismatches; route them through review/fixer rather than granting extra code-build visual repair attempts. Combine independent repairs, fix layout before typography/style detail, and rerun only invalidated checks. Build/test failures keep the existing build-failure policy; that retry cannot be used to smuggle in additional visual repair rounds.

Missing prerequisite, no progress, or exhausted rounds leaves the affected work partial/blocked with precise remaining gaps. The orchestrator relays any exception request through the normal halt/approver path with `requires_user: true`. Record the explicit answer, time/question reference, source/code/configuration identity, affected target/gates, and reason in evidence/map/context. Reuse it only while that scope and identity match. Fast mode, ordinary Approve, and agent recommendations cannot infer acceptance. Decisions about intentional departures, shared scope, ambiguous identity/target, and conflicting source/code changes also require protected user answers.

An explicit scoped exception permits proceeding past named design gates, retaining `exception-accepted` and failed/missing gate results rather than `verified`/`validated`. Record waived verification tasks explicitly with their decision; unfinished implementation tasks and unrelated mandatory build/test requirements still apply. Without that exception, halt publication; allow user-directed changes or abort while preserving work. User-requested further repairs follow the existing user-directed policy, without rewriting the automatic counter.

Approval and PR handoff report source/target, map path/status, gate results, evidence links, actual mismatches, shared impact, and explicit exceptions. Before publication and on resume recheck identity/freshness; return to invalid checks when context changed. Source edits remain explicitly authorized; review and implementation do not silently redesign the reference.

## 6. Accounted stage rules

These rules live here and only here; the orchestrator SKILL.md and `references/state.md` point at them instead of restating them.

- [x] On active Pen implementation the orchestrator verifies the gates itself — current source/code/capture identity, map/anchor coverage, runtime/fidelity evidence — and persists actual results (§4).
- [x] A stage result never by itself claims verified product fidelity (§4).
- [x] Design-only work runs the applicable repository checks; application gates are `not-applicable` only with a reason (§1, §4).
- [x] Missing prerequisites halt for a protected decision; repairable design failures join step 7's shared repair queue even while implementation is not yet verified (§5).
- [x] A valid design failure result is never retried as extra code-build visual repair; all repairs share `review.fix_rounds` (§5).
- [x] Ordinary Approve, fast mode, and agent recommendations never infer exception acceptance; only an explicit scoped exception permits proceeding past named gates, recorded with its evidence (§5).
- [x] The approval screen shows source/target, canonical map path/status, gate results, evidence links, remaining mismatches and shared impact, and explicit exceptions; protected decisions are persisted in context/map/evidence as well as relay, because checkpoints clear relay (§5).
- [x] Before publication (and on resume) recheck source/code/capture identity and gate/exception status; changed evidence returns the affected checks to invalid, and unwaived missing/failed gates halt publication (§5).
- [x] Design context uses pending storage before the worktree exists and moves to `<spec_dir>/factory/design/context.json` at creation, with every returned `design` result persisted before the checkpoint (§1).
