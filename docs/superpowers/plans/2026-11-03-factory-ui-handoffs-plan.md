# Repair the factory UI handoffs

**Priority 3.** Make UI implementation dispatch reliably and define how the factory reviewer handles Impeccable when nested agents are denied.

## Tasks

- [ ] Use the registered `design-to-code` role throughout dispatch, resume, relay, and budget instructions. Resolve saved assignments that use the old name to the registered role while preserving their task range and verification status.
- [ ] Define the factory-specific Impeccable review path. Specify how the reviewer performs permitted checks directly and discloses incomplete evidence when it cannot start child agents. Keep the technical and visual audit with UI review, and give UX review ownership of journey findings against the spec.
- [ ] Verify the role name against generated agent definitions. Then use a small UI fixture to exercise writer dispatch, an interrupted assignment, build and test verification, UI and UX findings, and the judge.
- [ ] Exercise OpenCode with nested delegation denied. Record which rendered interactions were observed and which findings relied on source inspection or saved captures.

## Acceptance

- The orchestrator starts the registered UI writer. A saved assignment under the old name resumes the same range.
- The UI review reaches the judge without relying on a denied child-agent call. The report accurately identifies what it could observe.
- Required design evidence still goes through spec conformance and the publication gate.

Both instruction mismatches are confirmed in the source. Their live impact remains unverified.
