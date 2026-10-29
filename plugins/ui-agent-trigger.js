// ui-agent OpenCode plugin
// Arms the ui-agent skill when a session first shows UI intent: a pen.dev or
// Figma design attachment (.pen file / design node), or a message mentioning
// pen.dev, Figma, UX, or UI. Fires once per session (latched on first match).
// Inert inside factory runs: the ui-designer role there has sole authority
// over ui-agent invocations (factory FR-024), so the trigger never latches
// and never injects while a run's state files are present.
//
// The trigger arms the skill, it does not run it: the critique pipeline in
// skills/ui-agent/SKILL.md still executes only when UI files are actually
// edited. Triggers are hardcoded by design (five rarely-changing strings);
// see the SKILL.md "Auto-Trigger" section.
//
// Trigger set, case-insensitive:
//   whole-word match: ui, ux, .pen
//   substring match:  pen.dev, figma
//
// Injection: appends a synthetic text part to the user message via the
// chat.message hook, so the reminder lands in the same turn the trigger
// fires. If a future OpenCode version stops honouring part mutation there,
// the proven tool.execute.before echo-prefix pattern (see the graphify
// plugin) is the documented fallback; keep the reminder string free of
// backticks and $(...) if it ever moves into an echoed shell command.
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

export const UiAgentTriggerPlugin = async ({ directory }) => {
  const armed = new Set(); // sessionIDs already reminded

  const firstMatch = (text) => {
    if (!text) return null;
    for (const trigger of TRIGGERS) {
      if (trigger.re.test(text)) return trigger.label;
    }
    return null;
  };

  return {
    "chat.message": async (input, output) => {
      if (!input?.sessionID || armed.has(input.sessionID)) return;
      if (inFactoryRun(directory)) return;
      let hit = null;
      for (const part of output.parts) {
        hit =
          firstMatch(part.type === "text" ? part.text : `${part.filename || ""} ${part.url || ""}`);
        if (hit) break;
      }
      if (!hit) hit = firstMatch(output.message?.text);
      if (!hit) return;

      armed.add(input.sessionID);
      const source = hit === ".pen" ? `design attachment (${hit})` : `keyword "${hit}"`;
      output.parts.push({
        id: `uiagent-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`,
        sessionID: input.sessionID,
        messageID: input.messageID ?? output.message?.id,
        type: "text",
        synthetic: true,
        text:
          `[ui-agent] UI trigger matched (${source}). Invoke the ui-agent skill now to arm UI QA. ` +
          "Pipeline runs only when UI files are actually edited. " +
          "For create/convert/build intent, defer to pen-design, pen-to-avalonia, or frontend-design. " +
          "Inert during factory runs.",
      });
    },
  };
};
