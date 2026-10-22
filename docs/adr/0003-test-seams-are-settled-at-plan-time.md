# Test seams are settled at plan time; implementation never invents one

The plan names the public seams the change puts under test, the task list puts a failing-test task in front of each implementation task, and analyze reports a HIGH blocking finding for any non-exempt implementation task with no mapped seam or no preceding test task. When implementation nevertheless meets a task needing an unlisted seam, the implementing role returns a failure naming it and the run halts for the user rather than inventing a seam. Letting the implementing role choose seams on the fly was rejected: the role is stateless and cannot agree seams with the user mid-loop, and invented seams quietly turn test-first into test-after.

## Consequences

- A missing seam costs a halt and a user decision, which is deliberate: it surfaces a planning gap instead of hiding it.
- This behaviour is carried in the planning role's own stage instructions inside the factory. A run never edits the consuming repository's SpecKit templates, skills or commands, so the discipline survives any repo's SpecKit version.
