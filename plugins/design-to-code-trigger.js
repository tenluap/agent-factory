// design-to-code OpenCode plugin
// Arms the design-to-code skill when a session first shows UI intent: a pen.dev or
// Figma design attachment (.pen file / design node), or a message mentioning
// pen.dev, Figma, UX, or UI. Fires once per session (latched on first match).
// Inert inside factory runs: the design-to-code role there has sole authority
// over the quality pass (factory FR-024), so the trigger never latches
// and never injects while a run's state files are present.
//
// The trigger arms the skill, it does not run it: the QA pipeline in
// .agents/skills/design-to-code/SKILL.md still executes only when UI files are actually
// edited. Triggers are hardcoded by design (five rarely-changing strings);
// see the SKILL.md "Auto-Trigger" section.
//
// Trigger set, case-insensitive:
//   whole-word match: ui, ux, .pen
//   substring match:  pen.dev, figma
//
// Injection: appends the reminder to the V2 prompt draft before admission.
// Appending preserves attachment and agent mention offsets in existing text.
import { existsSync, readdirSync } from "fs";
import { homedir } from "os";
import { join } from "path";

const TRIGGERS = [
  { label: "ui", re: /\bui\b/i },
  { label: "ux", re: /\bux\b/i },
  { label: ".pen", re: /\.pen\b/i },
  { label: "pen.dev", re: /pen\.dev/i },
  { label: "figma", re: /figma/i },
];

// Factory runs are detectable on disk (factory references/state.md): a
// committed run state inside the worktree, or pending state under
// FACTORY_HOME before the worktree exists.
function inFactoryRun(directory) {
  const specs = join(directory, "specs");
  try {
    for (const branch of readdirSync(specs)) {
      if (existsSync(join(specs, branch, "factory", "state.json"))) return true;
    }
  } catch {}
  const factoryHome = process.env.FACTORY_HOME || join(homedir(), ".factory");
  try {
    return readdirSync(join(factoryHome, "pending")).some((f) => f.endsWith(".json"));
  } catch {}
  return false;
}

export default {
  id: "design-to-code-trigger",
  async setup(ctx) {
    // Remember the triggering message so admission retries keep the reminder.
    const armed = new Map();

    const firstMatch = (text) => {
      if (!text) return null;
      for (const trigger of TRIGGERS) {
        if (trigger.re.test(text)) return trigger.label;
      }
      return null;
    };

    await ctx.session.hook("prompt", ({ sessionID, messageID, prompt }) => {
      const previous = armed.get(sessionID);
      if (!sessionID || (previous && previous.messageID !== messageID)) return;
      if (inFactoryRun(ctx.location.directory)) return;
      let hit = null;
      for (const file of prompt.files || []) {
        hit = firstMatch(`${file.name || ""} ${file.uri || ""}`);
        if (hit) break;
      }
      if (!hit) hit = firstMatch(prompt.text);
      if (!hit) return;

      const source = hit === ".pen" ? `design attachment (${hit})` : `keyword "${hit}"`;
      const reminder =
        previous?.reminder ??
        (`[design-to-code] UI trigger matched (${source}). Invoke the design-to-code skill now to arm UI QA. ` +
          "Pipeline runs only when UI files are actually edited. " +
          "For create/convert/build intent, defer to pen-design or frontend-design. " +
          "Inert during factory runs.");
      if (!prompt.text?.endsWith(reminder)) {
        prompt.text = prompt.text ? `${prompt.text}\n\n${reminder}` : reminder;
      }
      armed.set(sessionID, { messageID, reminder });
    });
  },
};
