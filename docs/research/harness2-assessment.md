# Harness² assessment for the software factory

Checked: **2026-10-24**. Upstream source pinned to [commit `1cfe254`](https://github.com/google-research/harness2/tree/1cfe254e8d25b15f37048c3730134686abe60335), committed 2026-10-14. This is source and documentation research; no Harness² installation, model calls, benchmarks, or factory integration were performed.

## Recommendation

**Trial Harness² as an optional optimizer for selected factory prompts and skills before considering integration into normal runs.** It offers a plausible route to better results on repeated, difficult work. It spends substantially more inference to find those improvements, so it should not be adopted as a speed optimization. Whether it improves this factory's quality, total cost, or elapsed time remains unmeasured.

## What it changes

Harness² evolves the configuration around a model while leaving model weights fixed. Its editable surface includes prompts, guardrails, memory, tool instructions, skills, scripts, subagent definitions, and plugins. It combines task-specific adaptation with retained experience that can guide later tasks. These are the project's stated capabilities, rather than evidence of benefits on our factory. [Upstream overview](https://github.com/google-research/harness2/blob/1cfe254e8d25b15f37048c3730134686abe60335/README.md)

The implementation first runs the unchanged harness. Separate editors propose general workflow changes and domain-specific changes; each proposal executes the same task. A composer examines the resulting artifacts and trajectories, then produces a harness that is executed again. Parallel recursion explores a wider candidate pool; sequential recursion builds on prior compositions. Validation can reject invalid proposals and retry them before reverting to the starting configuration. [Recursion implementation](https://github.com/google-research/harness2/blob/1cfe254e8d25b15f37048c3730134686abe60335/harness2/core/recursion.py)

For budgets above one, a model chooses among anonymized composed outputs. It has no ground-truth score, and the original reference outputs are excluded from the normal selection pool. At `k=1`, the sole composed output is adopted without a selector. Reflection subsequently extracts evidence-supported lessons; this is model judgment rather than a correctness guarantee. [Selection and reflection](https://github.com/google-research/harness2/blob/1cfe254e8d25b15f37048c3730134686abe60335/harness2/core/selection.py)

## Evidence for better results

The paper reports these WorkBuddy **Code scores** for one improvement step:

| Executor / harness | Base | Harness² | Gain |
| --- | ---: | ---: | ---: |
| Gemini 3.5 Flash / OpenCode | 73.4 | 76.5 | +3.1 |
| Gemini 3.5 Flash / Codex | 74.0 | 79.4 | +5.4 |
| GLM-5 / OpenCode | 58.4 | 77.1 | +18.7 |
| GLM-5 / Codex | 56.8 | 74.9 | +18.1 |

These average verifier scores across three streams of 40 held-out code tasks, not factory PR success rates. Meta-Harness scores 76.8 for GLM-5/Codex. Starting harnesses were sparse. Figure 6 counts execution/improvement tokens and reports a favorable quality/compute frontier for Gemini/OpenCode; factory wall-clock gains remain unestablished. `#Steps` count executor-session turns, excluding refinement. [Paper, Table 1, Figure 6, Appendices B–D](https://arxiv.org/html/2610.14224v1)

## Actual work and performance costs

The source explicitly budgets **`4k` task executions plus `3k` improvement sessions per task, per recursion mode**:

| Budget | Reference executions | Candidate executions | Final executions | Editor/composer sessions |
| --- | ---: | ---: | ---: | ---: |
| `k=1` | 1 | 2 | 1 | 3 |
| `k=5` | 5 | 10 | 5 | 15 |

Selection, reflection, transport retries, and invalid-edit retries are additional. An “improvement session” is an agent session containing multiple model turns, not necessarily one API request. Therefore four task executions do not imply a precise fourfold token or dollar bill. [Budget ledger](https://github.com/google-research/harness2/blob/1cfe254e8d25b15f37048c3730134686abe60335/harness2/core/ledger.py), [Agentic improver](https://github.com/google-research/harness2/blob/1cfe254e8d25b15f37048c3730134686abe60335/harness2/core/proposer.py)

Default phase width and improver concurrency are both two, limiting how much work overlaps. Parallel execution can reduce elapsed time relative to sequential exploration, but the implementation still has dependent phases and adds work relative to a baseline run. Exact time and dollar multipliers require measurement with our task distribution, providers, quotas, and model choices. [Configuration](https://github.com/google-research/harness2/blob/1cfe254e8d25b15f37048c3730134686abe60335/harness2/config.py)

The report command's printed dollar figure covers **improver work**, including selection and reflection. It does not represent the complete executor, judge, and infrastructure bill. A factory experiment needs independent end-to-end usage and time accounting. [Report implementation](https://github.com/google-research/harness2/blob/1cfe254e8d25b15f37048c3730134686abe60335/harness2/cli/report.py)

## Integration, models, and operation

The shipped CLI accepts only JobBench, LAB, and WorkBuddy, with OpenCode or Codex execution. It has no built-in factory-task mode. [CLI adapter construction](https://github.com/google-research/harness2/blob/1cfe254e8d25b15f37048c3730134686abe60335/harness2/cli/_common.py)

A Python `BenchmarkAdapter` interface provides a real extension seam: enumerate tasks, group domains, launch an execution, expose its trajectory and deliverables, supply a baseline harness, validate edits, and optionally judge results. Connecting factory work requires implementing that seam and its launcher, plus reproducible isolated repository snapshots for repeated attempts. This is engineering work, rather than adding another model identifier. [Adapter contract](https://github.com/google-research/harness2/blob/1cfe254e8d25b15f37048c3730134686abe60335/harness2/core/spec.py)

Documented benchmark setup uses Linux, Python 3.12, Node 20+, `uv`, and Google Cloud CLI; LAB additionally needs Pandoc/Poppler, and WorkBuddy needs Docker. Python package metadata permits 3.12–3.13. The provided model configuration uses Vertex Gemini executors/judges and Gemini or Claude improvers. Codex connects to a Responses API endpoint, with a LiteLLM bridge provided for Gemini on Vertex; another compatible endpoint can be configured. Existing ChatGPT or Claude subscription access is not the documented billing route. [Setup guide](https://github.com/google-research/harness2/blob/1cfe254e8d25b15f37048c3730134686abe60335/docs/SETUP.md), [Package metadata](https://github.com/google-research/harness2/blob/1cfe254e8d25b15f37048c3730134686abe60335/pyproject.toml)

The `claude_cli` channel is an improver channel, not a shipped Claude Code task executor; its implementation sets Vertex authentication variables. Provider/model syntax is configurable, but paper support does not imply every published benchmark adapter supports every model. In particular, WorkBuddy setup requires Gemini/Vertex solver and judge IDs. [Improver implementation](https://github.com/google-research/harness2/blob/1cfe254e8d25b15f37048c3730134686abe60335/harness2/core/proposer.py), [Benchmark guide](https://github.com/google-research/harness2/blob/1cfe254e8d25b15f37048c3730134686abe60335/docs/BENCHMARKS.md)

## Limitations and controls

The release leaves executor networking unrestricted and runs Codex without its sandbox. The maintainers observed a validation rollout retrieving a public task rubric. These defaults require isolation for a trustworthy experiment. Public rubric access can invalidate a comparison; mutable generated scripts and hooks also need separation from the factory's trusted rules and credentials. [Experiment guide](https://github.com/google-research/harness2/blob/1cfe254e8d25b15f37048c3730134686abe60335/docs/EXPERIMENTS.md), [Codex execution flags](https://github.com/google-research/harness2/blob/1cfe254e8d25b15f37048c3730134686abe60335/harness2/substrate/codex.py)

This is an early research release, with package version 0.1.0 and no published GitHub releases/tags when checked. It is Apache-2.0 and explicitly not an officially supported Google product. Upstream benchmark and third-party licenses remain separate. [Package metadata](https://github.com/google-research/harness2/blob/1cfe254e8d25b15f37048c3730134686abe60335/pyproject.toml), [Releases](https://github.com/google-research/harness2/releases), [Tags](https://github.com/google-research/harness2/tags), [License/disclaimer](https://github.com/google-research/harness2/blob/1cfe254e8d25b15f37048c3730134686abe60335/README.md#license)

## Fit with this factory

Our factory already specifies tests, independent parallel reviews, a review judge, bounded fix rounds, and approval before pushing or creating a PR. Its harness adapters describe host-specific installation and role/model formats; they are a different abstraction from Harness²'s optimization loop. Existing token/duration records are useful starting points but do not establish quality improvements. [Factory design](../../DESIGN.md), [Engineering rules](../../core/skills/factory/references/engineering.md), [Factory workflow](../../core/skills/factory/SKILL.md)

**Assessment:** the strongest potential benefit is turning recurring execution failures into reusable prompt/skill improvements. The main disadvantages are repeated execution cost, integration and maintenance, uncertain transfer, and self-evaluation errors. Our existing engineering discipline may reduce the available improvement compared with sparse research baselines.

A useful first experiment would compare the current code-build role, the same role with equal-budget ordinary retries, and Harness² at `k=1`, on representative held-out tasks in isolated repository snapshots. Keep models and task sets fixed, preserve factory hard rules and approval gates outside editable files, and measure independently accepted correctness, rework, total usage/cost, and elapsed time. Adopt only improvements that repeat on held-out work. This experiment is a recommendation, not work already performed.
