#!/usr/bin/env node
// design-to-code trigger hook for claude-code and codex.
// Both harnesses fire UserPromptSubmit with the same stdin shape
// ({ session_id, prompt, cwd, hook_event_name }) and accept the same JSON
// output ({ hookSpecificOutput: { hookEventName, additionalContext } }), so
// one script serves both. Wired manually: see install.sh output for the
// snippet to paste into ~/.claude/settings.json (hooks.UserPromptSubmit) or
// ~/.codex/hooks.json (hooks.UserPromptSubmit).
//
// Behaviour mirrors plugins/design-to-code-trigger.js (the OpenCode plugin):
// fires once per session when the prompt matches a UI trigger, injecting the
// reminder that arms the design-to-code skill. The pipeline itself still runs only
// when UI files are actually edited. Inert inside factory runs (factory
// FR-024: the design-to-code role there has sole authority over the quality pass).
//
// Hook processes are one-shot, so the latch is a tiny state file per session
// under ${XDG_CACHE_HOME:-~/.cache}/design-to-code-trigger/, pruned when older
// than 7 days. Prompts are plain text here (no attachment parts), so `.pen`
// matches when the file path appears in the prompt text.
//
// Triggers, case-insensitive: whole-word `ui`, `ux`, `.pen`; substring
// `pen.dev`, `figma`. Hardcoded by design — see core/skills/design-to-code/SKILL.md.
//
// Never fail the prompt flow: any problem exits 0 silently.
import { existsSync, readdirSync, readFileSync, statSync, writeFileSync, mkdirSync, rmSync } from "fs";
import { homedir } from "os";
import { join } from "path";

const TRIGGERS = [
  { label: "ui", re: /\bui\b/i },
  { label: "ux", re: /\bux\b/i },
  { label: ".pen", re: /\.pen\b/i },
  { label: "pen.dev", re: /pen\.dev/i },
  { label: "figma", re: /figma/i },
];

const CACHE_DIR =
  process.env.XDG_CACHE_HOME || join(homedir(), ".cache", "design-to-code-trigger");
const MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000;

function armed(sessionId) {
  try {
    return existsSync(join(CACHE_DIR, `${sessionId}.armed`));
  } catch {
    return false;
  }
}

function latch(sessionId) {
  try {
    mkdirSync(CACHE_DIR, { recursive: true });
    writeFileSync(join(CACHE_DIR, `${sessionId}.armed`), String(Date.now()));
    for (const f of readdirSync(CACHE_DIR)) {
      const p = join(CACHE_DIR, f);
      try {
        if (Date.now() - statSync(p).mtimeMs > MAX_AGE_MS) rmSync(p);
      } catch {}
    }
  } catch {}
}

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

function main() {
  let input;
  try {
    input = JSON.parse(readFileSync(0, "utf8"));
  } catch {
    return;
  }
  const sessionId = input.session_id || "";
  const prompt = typeof input.prompt === "string" ? input.prompt : "";
  const cwd = typeof input.cwd === "string" && input.cwd ? input.cwd : process.cwd();
  if (!sessionId || !prompt || armed(sessionId) || inFactoryRun(cwd)) return;

  let hit = null;
  for (const trigger of TRIGGERS) {
    if (trigger.re.test(prompt)) {
      hit = trigger.label;
      break;
    }
  }
  if (!hit) return;

  latch(sessionId);
  const reminder =
    `[design-to-code] UI trigger matched (keyword "${hit}"). Invoke the design-to-code skill now to arm UI QA. ` +
    "Pipeline runs only when UI files are actually edited. " +
    "For create/convert/build intent, defer to pen-design or frontend-design. " +
    "Inert during factory runs.";
  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "UserPromptSubmit",
        additionalContext: reminder,
      },
    }),
  );
}

try {
  main();
} catch {}
