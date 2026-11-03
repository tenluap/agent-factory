# Bind publication to verified work

**Priority 2.** Make the factory check that it publishes the same deliverable changes that passed verification, received a review verdict, and were approved.

## Tasks

- [ ] Define a reproducible identity for the work and its comparison base. Enumerate the generated factory bookkeeping paths that may change without changing that identity. Treat application code, tests, configuration, and deliverable design evidence as material.
- [ ] Save that identity with independent build and test results, each review verdict, and the approval decision through the existing state writer. Validate it when reading saved runs. Older records without matching evidence require a fresh check and approval before publication.
- [ ] Recheck the deliverable immediately before publishing, including on resume. Route changed work back through affected verification and review, then back to approval. Check for an existing PR before retrying an interrupted publication.
- [ ] Check the planned archive cleanup against the same identity. Account explicitly for any deliverable changes it makes before the final push.

## Acceptance

- A source, test, or required configuration edit after approval prevents publication with the old records, including after resume.
- An expected bookkeeping-only checkpoint preserves the validity of unchanged deliverable evidence.
- The first and final pushes preserve the approved deliverable identity. An interrupted retry finds the existing PR and avoids duplication.

[State writer and verification](../../../core/skills/factory/bin/factory_cli/commands.py) · [Current PR stage](../../../core/skills/factory/SKILL.md)
