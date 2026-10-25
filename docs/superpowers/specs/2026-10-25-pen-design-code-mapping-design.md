# Pen design-code mapping in the factory

**Date:** 25 October 2026

**Status:** Decisions Q1–Q14 and written specification approved by the user on 25 October 2026.

## Purpose

Whenever a factory run uses a pen.dev design as an implementation reference, preserve the relationship between that design and its code, implement the reference faithfully, and carry enough evidence for a fresh agent to update the correct screen later. Mapping establishes traceability; rendered comparison establishes fidelity. Both are required for verified completion.

The starting reference was the user's `pen-to-avalonia` agent. Its mapping, scoped survey, canonical component, and bounded validation concepts become a portable factory contract. Its local installation path, assumed Pen APIs, and Avalonia-only implementation choices do not become universal prerequisites.

## Approaches considered

| Approach | Benefit | Limitation |
|---|---|---|
| Factory-owned mapping and fidelity contract, with framework-specific implementation guidance — selected | Applies across frameworks and survives fresh agents, fixes, and later runs. Existing roles enforce it. | Requires lifecycle handoffs and explicit evidence gates. |
| Route only to the existing Avalonia agent | Reuses a detailed conversion workflow. | Couples the factory to a personal installation and one framework; does not govern every factory role. |
| Add a map without fidelity verification | Makes source lookup easier. | Cannot establish that the rendered implementation follows the reference. |

## Activation, scope, and authority

- Activate automatically when a factory run creates, references, or updates a Pen design intended as an implementation reference, on every framework. This contract governs factory runs; it does not intercept unrelated standalone Pen invocations.
- A design-only task records source identity and intended targets. Code coverage becomes mandatory when implementation begins; absence of code is expected in a design-only task.
- Use one shared contract and framework-specific translation/capture guidance. Start with the supplied Avalonia practices while preserving support for other stacks.
- The referenced design governs visual decisions, including layout, typography, spacing, composition, icons, and visibility. Review suggestions must respect that authority. Record unsupported properties, accessibility conflicts, and proposed departures; obtain agreement before intentional visual departures.
- The implementation scope is the requested screen/component and its dependencies. Existing projects bootstrap verified mappings for that scope before updating; a whole-application migration is not required.

## Source and target resolution

Resolve from an explicit reference, the active feature's saved target, or a uniquely matching canonical map entry. If multiple candidates remain, relay a question through the orchestrator. An open design application alone does not establish the intended target.

Discover the permitted Pen backend and its actual capabilities before assuming inspection, export, identifiers, or revision support. The installed Pen skill documents exports but does not establish stable node IDs, node inspection, or immutable revision APIs. The supplied agent describes a richer access model. Follow supported tools and their documentation; do not assume a file format or invent backend capabilities.

Record repository-relative source paths or external source references, observed target identifiers, and reliable freshness evidence. A local content fingerprint may identify a source snapshot; it does not supply missing design-node identifiers. If supported inspection cannot establish required coverage, report that limitation and block verified implementation completion.

## Canonical map

Use one repository-owned `docs/design-code-map.json` by default. Extend an existing canonical map instead of creating a competing inventory. Preserve unrelated entries and existing schema information; any necessary migration must retain source associations and explain its changes.

The map supports multiple sources and contains these logical records:

| Record | Required information |
|---|---|
| Source | Source reference, target scope, observed identity/freshness evidence, relevant capture configuration, and evidence references. |
| Component | Source-qualified design ID, name/path, canonical code file/symbol/resource anchor, dependencies, tokens, instances, overrides, and status. |
| Instance | Source-qualified instance and component IDs, parent, actual overrides, code anchor, and status. |
| Node coverage | Every scoped node's source-qualified design ID, parent, owning component or code anchor, and status. |
| Exception/removal | Affected source/node/code association, reason, disposition, and any explicit approval. |

IDs are qualified by source so two design files cannot collide. Reverse lookup uses the same records. Stable file/symbol/resource anchors are authoritative; line numbers are optional hints. A primitive can be covered by a parent component: exhaustive coverage does not require a separate control for every design node.

Statuses distinguish `planned`, `implemented`, `validated`, `stale`, and `unmapped`. Keep unexplained unmapped design nodes and orphaned code visible. Intentional exclusions and removals carry reasons. `validated` requires current successful evidence, never merely a populated map.

Reuse existing matching controls/resources. Explicit design components have one canonical implementation; instances retain their real differences. Use the smallest abstraction consistent with project conventions and the surveyed design.

## Survey and freshness

Survey the complete requested subtree and referenced component definitions, relevant instances, variables, tokens, and assets. Record layout/sizing, child order, typography, visibility, styles, geometry, and overrides sufficiently to implement and compare the reference. Resolve theme-dependent values and capture a reference at the comparison configuration.

Each new or resumed run checks source freshness and current code anchors. Reuse a survey only when reliable source evidence establishes it is unchanged; otherwise refresh affected targets and dependencies. A timestamp alone is not freshness evidence. Code-only changes do not invalidate an unchanged design survey, but can invalidate code anchors and rendered evidence.

Mark affected records stale before modifying previously validated design/code. Missing identifiers are not silently reassigned by similar names. Refresh changed design evidence and validate affected scope before restoring validated status. Reuse valid evidence within a run instead of repeatedly surveying or capturing unchanged inputs.

## Update and removal behavior

- Default implementation updates to design → code. Editing the Pen source requires an explicit request; mapping does not authorize automatic code → design synchronization.
- If both source and implementation have changed, surface conflicting changes before choosing which wins. Preserve unrelated application work.
- Inspect shared-component consumers automatically. Apply and validate changes within agreed scope; relay a scope decision before a shared change requires visual changes elsewhere.
- Remove presentation exclusively owned by a removed design element within scope. Before removal, check shared consumers and application behavior. Discarding behavior, changing other screens, or contradicting feature requirements requires a conflict decision.
- Record deliberate removals so future runs do not recreate them from stale coverage.

## Evidence and completion

Keep design and runtime captures scoped. By default, commit the map, the local design source used, reference/runtime captures, and comparison metadata. Place run evidence under `specs/<branch>/factory/design/`; the permanent map references it. For externally hosted sources, retain the source reference and an exported baseline. Artifact references use repository-relative paths rather than machine-specific absolute paths.

Record source identity/fingerprint, current code identity, target state, viewport, theme, DPI/zoom/scale as applicable, actual checks/results, and deviations or evidence gaps. Identity must distinguish captures of different code states without requiring a self-referential commit hash. These artifacts let a later agent understand and reproduce the comparison.

Required implementation gates are separate:

1. **Build/runtime:** the affected project builds, relevant existing tests pass, and the target runs without relevant binding/resource/runtime errors.
2. **Mapping:** required node coverage is accounted for; anchors resolve; canonical components, instance counts/overrides, and dependencies agree; stale/unmapped/orphaned entries have explicit dispositions.
3. **Fidelity:** supported design values are implemented and the current target is compared with the reference at matching capture settings. Check composition, spacing, typography, content, icons, visibility, clipping, and overflow. Platform rasterization differences are acceptable; other departures require an explicit disposition. There is no universal pixel-difference threshold.

These checks are mandatory independently of optional impeccable review or polish. Static desktop review can contribute findings but cannot establish observed rendered fidelity. Missing screenshots, design access, inspection, runtime capability, or failed required checks prevent verified completion.

After bounded repair, preserve work and report partial/blocked when required checks are missing or fail. The user may explicitly accept an exception to proceed. Keep the missing/failed checks and exception in the map, state, evidence, and handoff; never relabel the result as verified fidelity. Fast mode cannot infer such an exception, authorize a design departure, or settle a scope/conflict decision that requires the user.

## Repair and review

Use one deduplicated findings queue for mapping, visual, and other review findings. Design fidelity violations cite the approved requirement and evidence; they are not downgraded merely because style guidance is ordinarily advisory. Compatible polish recommendations retain the existing severity/approval policy.

Share the existing two automatic fix rounds with other review findings. Combine independent fixes into each batch and rerun only invalidated checks. Agents, backends, phase changes, and renamed findings cannot reset this budget. Missing or failed mandatory checks still require the exception policy after the budget is exhausted. User-requested further work follows the factory's existing user-directed repair policy.

## Factory integration

Use existing roles, neutral verbs, and pending/worktree boundaries. Add no new agent role, parallel planning chain, or independently resetting repair loop.

| Stage/role | Responsibility |
|---|---|
| Intake/orchestrator | Detect the trigger; resolve source/target/scope; persist settled design authority and decisions in the pending brief/state without repository writes before worktree creation. |
| Spec-builder | Carry the reference through spec/plan/tasks; establish coverage, framework guidance, commands, capture settings, permitted deviations, and verification criteria. |
| Code-build | Read the canonical map and scoped survey, implement dependency batches, maintain mapping/evidence, and report actual gate status. |
| Orchestrator verification | Independently check build/tests and required mapping/fidelity evidence for the current state. Route failures through the shared review/repair budget. |
| Spec-conformance | Check mapping coverage and the explicit design requirements against current implementation and evidence. |
| UI reviewer | Compare the reference and current rendered target when reviewing mapped UI; retain read-only, evidence-based review and respect design authority. |
| Judge | Verify/deduplicate concrete requirement violations and preserve verification gaps and accepted exceptions. |
| Fixer | Receive the same source/map/evidence context, invalidate affected records, update mapping with fixes, and return current check results. |
| Approver/PR | Show target/source, map path/status, comparison evidence, gaps, and explicit exceptions. Publication approval does not silently waive fidelity requirements. |
| Resume | Read saved map/evidence references; check freshness and anchors; resolve skills for the current harness; continue from invalid checks with the original repair counter. |

The portable core owns the contract through a conditional reference. Resolve external Pen guidance through the adapter's `RESOLVE` operation when needed; pass resolved paths and design context to fresh roles. Persist framework and source/map/evidence references as additive run-state data; absent data in older states preserves ordinary non-Pen behavior. On a resumed run that actually encounters a Pen reference, activate the contract and bootstrap its scoped mapping.

## Implementation sequence and rationale

1. Amend `DESIGN.md` deliberately before changing core behavior; link this accepted contract.
2. Add a conditional `references/design-code-mapping.md` so non-Pen runs do not load the detailed workflow. Link it from routing and the affected role entry points instead of duplicating its rules.
3. Align orchestrator intake, role inputs, verify/review/approver behavior, and state/resume references. Extend existing envelopes additively where design results need persistence; retain their required shape.
4. Add scoped framework guidance for Avalonia where translation/runtime capture differs, reusing existing project conventions and available skills. Other frameworks follow the same shared requirements using their available supported tooling.
5. Align README/product documentation and the relevant findings/severity rules so ordinary optional UI review cannot bypass this contract.
6. Render all five harness distributions through the canonical renderer. Preserve adapter model/access settings.

No new package or service is required for this instruction feature. If mechanical validation needs new logic, settle its public seam in the implementation plan before writing tests; reuse existing renderer, state CLI, and repository checks where they cover the change.

## Acceptance scenarios

- A non-Pen run keeps its current routing, optional UI policy, state compatibility, and review budget.
- A design-only Pen run records source/targets without claiming missing code is a fidelity failure.
- A Pen implementation on Avalonia or another framework activates the common contract automatically.
- A new or existing screen obtains scoped, source-qualified coverage with stable code anchors; unrelated screens are not migrated.
- A map resolves both design → code and code → design lookups from the same records; reverse lookup does not authorize design edits.
- Multiple sources and ambiguous screen names require a unique recorded target or a user decision; an open design is not chosen silently.
- A fresh agent or different harness resumes using persisted design/map/evidence references, then checks freshness before reusing them.
- A changed source, moved code anchor, deleted node, or changed capture invalidates only affected evidence. Missing IDs are not matched by name without confirmation.
- A shared-component update inspects other consumers and requests scope agreement before changing out-of-scope screens.
- A design removal preserves application behavior unless the user settles the conflict, and records intentional removal.
- A clean build and complete map with visibly incorrect composition fail fidelity verification.
- Missing design inspection/runtime/capture capability, or declined impeccable installation, cannot produce an unsupported verified-fidelity claim.
- A concrete departure from the approved reference is evaluated as a requirement violation with evidence, independently of advisory styling opinions.
- Two consolidated automatic repair rounds exhaust the shared budget. Restarting agents or moving between phases does not grant more rounds.
- An explicit exception permits proceeding while preserving failed/missing checks; ordinary Approve or fast mode does not manufacture the exception.
- Scoped committed sources/exports/captures and metadata let a fresh agent reconstruct what was compared, using repository-relative artifact references.

Validate packaging with canonical renders, relative-link integrity, and backward-compatible state/role contracts. Distinguish those checks from real Pen-to-application trials: only actual supported inspection and rendered comparison can demonstrate end-to-end fidelity.
