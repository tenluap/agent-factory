# Brief: ui-designer role

Add a new factory role `ui-designer` (agent `factory-ui-designer`, tier standard, access write). The orchestrator spawns it in the implement step on UI design runs. It detects the project's UI framework, maps the design source to the codebase, and updates the targeted file (plus its component dependencies) or, with no target, the whole UI surface (components and views) in dependency batches. Reviews, shared fix rounds and approver gate are unchanged.

## Decisions
- Placement: write role spawned in step 6 (implement) for UI design runs, alongside/instead of code-build. No `/factory design` route.
- Frameworks: detect from project files; per-framework reference loaded. Ship Avalonia (reuse design-code-mapping-avalonia.md) and web (html/css/tsx/vue/svelte). Others: report unsupported, never guess.
- Design sources: Pen file (pen-design, authoritative, mapped), Figma nodes, images/screenshots (visual reference, no node mapping), or text-only restyle (existing code is baseline, impeccable guides).
- Figma: resolve a `figma` skill/MCP via RESOLVE like `pen-design`; missing capability = disclosed blocker with setup guidance; nothing installed automatically.
- Scope: file named = that file + its component deps (check other callers of shared components first); none named = whole UI surface in dependency batches in tasks.md. The enumerated file list is a protected decision: shown to the user, never auto-accepted by fast mode (requires_user).
- Quality: role runs `ui-agent` at most once; ui-reviewer/judge/fixer share the existing 2 fix rounds. No second repair loop.
- Mapping: reuse canonical `docs/design-code-map.json` and design-code-mapping gates (map, runtime, fidelity).
- Constitution: DESIGN.md edited first, then core/ + adapters/ + tests + renders for all 5 harnesses; dist drift check; harness-neutral core (neutral verbs only); new role files need a stated reason (agent time budget entry too).
- Prior art: ~/.config/opencode/agents/pen-to-avalonia.md and skills/ui-agent/SKILL.md (attached by user) are the source of behaviour for the role.
- Chain: full. Fast mode on.
