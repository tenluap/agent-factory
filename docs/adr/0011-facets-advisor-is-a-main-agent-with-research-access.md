# FACETS advisor is a main agent with research access

The user wants help deciding which projects and income options to pursue, using the FACETS checklist (Face, Advantage, Capital, Expertise, Time, Scale), in a conversation they start themselves. We add one role, `facets-advisor`, rendered for every harness like the others but marked `mode: primary`: the user starts it as their session's agent, and the `/factory` orchestrator never spawns it. It talks to the user directly, so it breaks two conventions: every role is a run stage, and agents never talk to the user. To keep that contained, it adds no stage, route, state field, envelope field or CLI change. The only file it writes is the user's profile in the factory home, and only after confirmation.

`mode` is neutral role metadata. An adapter's `modes` map turns it into native fields, replacing same-named extras: OpenCode renders `mode: all`. Claude Code (`--agent`) and Copilot (`--agent`, `/agent`) already start any custom agent as the main agent, so they need no field. Codex custom agents are subagents only, and ZCode's support is unverified; there the agent stays a subagent and `harness.md` says so.

Scoring needs evidence, so the agent does read-only web research. No access level allowed that: `read` on Claude Code, ZCode and Copilot has no web tools. We add a third access level, `research` (`read` plus web search and fetch, no file edits), and two verbs, `WEB_SEARCH` and `WEB_FETCH`, so the core still names no harness tool. Reviewers keep `read`, so their tool surface does not grow.

## Considered options

- **A subagent the main session calls** (first agreed): rejected; the user wants to talk to the advisor directly, and the relay added round trips and a protocol field nothing else used.
- **A `/facets` skill** that turns any session into the advisor: rejected for now; it works on Codex too, but loses the agent's own model and tool limits. Add it if the Codex gap matters.
- **A gate before spec-builder in every run**: rejected; most runs build what the user already decided to build.
- **Web tools added to `read`**: rejected; it widens all six reviewers for one role.
- **`write` access so it can save the profile**: rejected; one confirmed shell write of one file in the factory home is narrower than edit access to the repository.
