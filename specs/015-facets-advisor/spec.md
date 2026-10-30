# Feature Specification: FACETS Advisor Role

**Branch**: `015-facets-advisor` | **Date**: 2026-10-30 | **Status**: Implemented

## Summary

A main agent, `factory-facets-advisor`, that the user starts and talks to directly, scores one or more projects or income options against the FACETS checklist (Face, Advantage, Capital, Expertise, Time, Scale), backed by cited web research and judged against the user's profile, then ranks them with a verdict each. Decisions were settled in a grilling session on 2026-10-30; a later round changed it from a subagent to a main agent.

## User stories

1. **Score one option.** As a user, I start the advisor and give it with an idea and get six yes/no answers, each with a reason and sources, a total out of 6 and a verdict.
2. **Compare options.** As a user, I pass several ideas and get them ranked, with ties broken by Capital, Time, then Scale.
3. **First use.** As a user without a profile, the advisor asks for the missing fields in chat and saves them after I confirm.
4. **Follow-up.** As a user, I change a constraint and see only the affected facets rescored.

## Functional requirements

- **FR-001** `DESIGN.md` records the role, the `research` access level and the research verbs before core changes.
- **FR-002** One role prompt `core/roles/facets-advisor.md`, tier `deep`, access `research`, `mode: primary`, rendered for all five harnesses.
- **FR-003** The orchestrator never spawns the role; no stage, route, state field, envelope field or CLI change. Main-agent start per harness is documented in `harness.md`; Codex and ZCode fall back to a subagent.
- **FR-004** The six checklist questions are verbatim from the source; Advantage keeps the audience question and treats a borrowed edge as evidence for yes.
- **FR-005** Capital, Expertise and Time are judged against the profile `${FACTORY_HOME:-~/.factory}/facets-profile.md`; missing fields are asked in chat; the profile is saved only after confirmation and is the only file the agent writes.
- **FR-006** Research uses `WEB_SEARCH` and `WEB_FETCH` only, at most 3 searches and 5 fetches per option; a facet without evidence scores 0 with `unverified: true`.
- **FR-007** Verdict: 6 pursue, 4-5 investigate, 3 or less drop; a Capital 0 whose loss exceeds `capital_at_risk` caps at investigate.
- **FR-008** Output is Markdown in chat: a checklist table per option, a ranking table and source caveats. Follow-ups rescore only what changed.
- **FR-009** `research` access is `read` plus web search and fetch with no edit access, in every adapter's own terms.
- **FR-010** The core role names no harness tool.
- **FR-011** A role's `mode` maps through an adapter's `modes`; OpenCode renders `mode: all` for `primary`, other roles keep `mode: subagent`.

## Success criteria

- **SC-001** Every harness renders the agent with tier `deep` and research tools, and no edit access (automated).
- **SC-002** The core role names no harness tool, and every `harness.md` maps both research verbs (automated).
- **SC-003** OpenCode renders the advisor `mode: all` and every other role `mode: subagent` (automated).
- **SC-004** Manual: no profile triggers the profile questions and a confirmed save; the source's four worked methods reproduce or justify the calibration; three options rank by the tie-break order; a changed constraint rescores only affected facets.

## Out of scope

A `/facets` skill, Codex main-agent support, orchestrator integration, saving results, and committing the source checklist image.
