# Post-PR outcomes live beside the run archive and feed the backlog per run

2026-11-04: a factory run ends at the open PR, so the factory never learned whether CI or a reviewer rejected what it produced. The feedback refresh (`factory feedback`, `/factory feedback`) now reads a published run's PR state, failed checks and change requests from GitHub, read-only and only when the user asks; nothing refreshes automatically and nothing is written to GitHub, merged or deployed. Each run's PR outcomes go into a sidecar outcome file in the factory home, keyed like the run archive, and each actionable outcome becomes a `ready` `feedback` entry in the improvement backlog, one per source run and signal key, with no per-run cap and no skip when another run already covers the signal key.

## Considered options

- **Store outcomes inside the run archive**: keeps everything about a run in one folder, but the archive is a verified, byte-identical, write-once copy (ADR 0008), and a later refresh would have to rewrite it.
- **Store outcomes beside the archive** (chosen): the archive stays untouched; the sidecar is the only file a refresh rewrites, atomically and under a lock.
- **Route outcomes through the retro's candidates**: reuses the retro's ranking, but the retro runs once per ended run, keeps at most three candidates and skips a signal key another run's entry already covers, so a check that fails on every run would surface once and then disappear.
- **Per-run feedback entries without cap or cross-run skip** (chosen): every run that hits a failure shows it, and repeat sightings append evidence to that run's `ready` entry instead of creating duplicates.

## Consequences

Runs are matched to the repository by their archived repository path against the resolved main repository, as Run exports and Retro entries are, so the runs of a checkout that has since moved are not found. A run whose PR is already merged or closed is not fetched again, so a reopened PR is missed. A refresh that cannot read or write a run reports a refresh gap with its class and reason rather than guessing an outcome.
