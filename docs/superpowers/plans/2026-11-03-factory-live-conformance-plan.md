# Factory live conformance plan

**Priority 1.** Prove that a real coding-agent session can take a feature request through an interruption, resume, and one approved pull request.

## Tasks

- [ ] Record the checkout revision, any local source changes under test, and the installed factory and harness versions. Render the checkout into an isolated installation for acceptance trials. An installed-version baseline is a separate result.
- [ ] Use the disposable greeting fixture for a headless smoke test. It starts from a settled brief and stops before approval. Check the resulting state, independent acceptance test, and review verdict with the benchmark scorer.
- [ ] Start a separate golden run from a fresh request in a disposable repository. Confirm requirements and any protected decisions as the run asks for them. Observe the actual worktree, spec, task commits, and verification.
- [ ] Pause before review. Resume, interrupt the active review, then resume in a fresh session on a second supported harness. Verify that the same worktree, settled answers, and completed task commits are reused.
- [ ] Present the actual result for approval. After approval, publish against a throwaway GitHub repository and verify that exactly one PR exists. Verify the final run archive and cleanup push.
- [ ] Repeat with a small UI fixture after the [UI handoff repairs](2026-11-03-factory-ui-handoffs-plan.md). Record the outcome and any evidence limits in the [golden-run results](../../../conformance/golden-run-results.md).

## Acceptance

The fixture passes its independent acceptance test. Resume preserves completed work and does not repeat settled questions or create a second worktree. The approved run creates exactly one PR and produces an inspectable archive. Record the evidence for each leg separately. A passing headless smoke test covers the seeded path through review only.

Both installed-version smoke tests stopped before factory preflight. OpenCode’s default server returned an internal error, and its private server reached the model provider, which rejected the request because it lacked an end-user identifier. Claude Code reached the model but its headless session lacked permission to read the factory references or invoke the state CLI. The Claude fixture still had only its initial checkout and an empty run history. The next smoke test needs a compatible OpenCode model configuration or a Claude Code session with scoped permission for the fixture and installed factory. The complete workflow remains unverified.

[Benchmark procedure](../../benchmark.md) · [OpenCode golden-run checklist](../../../conformance/golden-run/opencode.md)
