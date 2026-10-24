# The rendered distribution is tracked in git

`dist/` was gitignored, which left the repository with no way to prove that the committed skill and agent trees match a fresh render: `git diff --exit-code -- dist/` on an ignored, untracked directory always passes. From the ZCode adapter onwards the rendered output of every harness is tracked and committed with its source, so that difference check is a gate that can actually fail.

## Considered options

- **Keep `dist/` ignored and force-stage it** (`git add -f dist/` plus `git diff --cached --exit-code`): keeps the tree smaller, but the gate depends on a step a contributor can forget, and the ignore rule still fights every normal git command.
- **Re-render into a scratch tree and compare**: proves the same thing without committing generated files, but leaves consumers with no installable distribution in the repository, which is what `install.sh` reads.
- **Track `dist/`** (chosen): generated files appear in diffs and reviews, which is the cost, but the distribution is installable straight from a clone and any divergence between source and render shows up as a dirty tree.
