---
name: prompt-optimiser
description: 'Rewrite vague or raw user input — typed text or an attached spec/markdown file — into an optimised prompt. Default mode emits one polished paragraph; full mode emits a 7-section structured prompt. Use for /prompt-optimiser, prompt rewriting, or prompt engineering.'
---

# Prompt Optimisation

Turn raw, vague, or incomplete input into a prompt a model can act on. Pick the mode, then
rewrite. Never blend the two output shapes.

## Mode Selection

| Command | Mode | Output |
|---------|------|--------|
| `/prompt-optimiser` | default | One paragraph |
| `/prompt-optimiser default` | default | One paragraph |
| `/prompt-optimiser full` | full | 7-section prompt |

No mode word means default. Everything after the mode word is the input. A word that is not
`default` or `full` is input, not a mode — `/prompt-optimiser summarise my notes` runs default
over the whole remainder.

## Both Modes

- Single-shot. Never ask a follow-up.
- Preserve the original goal, domain, and priority order. Add no new objectives.
- Invent no facts. Encode gaps as `(Assumption: …)` in default, or as Constraints in full.
- Match the user's register. Jargon only if the input implies it.
- Cut filler, repetition, and asides.
- Emit the prompt alone — no preamble, commentary, code fences, or quote marks.
- Always use Context7 when I need library/API documentation, code generation, setup or configuration steps without me having to explicitly ask.

---

## Default Mode

One polished, self-contained paragraph. No headings, lists, bullets, or labels — absolute, even
for long or multi-part input. Length 0.75x–2x the original.

Add only the context a strong answer needs: purpose, background, audience, constraints, success
criteria, output type and format, depth. Assume a competent reader; do not over-explain.

Steps: identify intent and domain → note missing context → fill gaps with minimal marked
assumptions → write the paragraph → verify it is specific, actionable, professional.

---

## Full Mode

Act as an expert prompt engineer. Emit all seven sections in this order, even for trivial input.
Never answer with a bare paragraph.

1. **Role Definition** — expertise, perspective, and authority the target model adopts.
2. **Task Objective** — the concrete goal from the user input, stated unambiguously.
3. **Input Specifications** — inputs the model receives, their format, and how dynamic or
   attached content is treated.
4. **Output Requirements** — exact deliverable, format, structure, length. Must state verbatim
   that the response contains only the requested output, with no explanation, no preamble, and
   no requests for attachments or clarification.
5. **Constraints & Context** — scope boundaries, domain context, prohibitions, carried-over
   background.
6. **Quality Criteria** — measurable standards: accuracy, completeness, tone, verifiability,
   self-consistency.
7. **Handling Dynamic/Attachment Elements** — how placeholders, variables, files, or images are
   referenced and consumed.

### Principles

Explicit over implicit. Structured formatting so each requirement is independently checkable.
Concrete nouns, counts, formats, and units over vague adjectives. Define what is in scope and
what is out. Thorough enough to remove ambiguity, short enough to stay actionable. Examples only
where they narrow the solution space. Embed self-check criteria the model verifies before
responding.

### Emission Rules

- Strip all citation and reference markers.
- If the input references a file or image that is not attached, write `Using the file or image
  attached` rather than requesting it.
- Before emitting, audit all seven sections against the user input. Confirm every aspect is
  covered and the no-clarification rule appears verbatim in Output Requirements. Refine until
  both hold.
