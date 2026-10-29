import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import * as module from "../../plugins/ui-agent-trigger.js";

async function fixture(t) {
  const root = mkdtempSync(join(tmpdir(), "ui-agent-trigger-test-"));
  const factoryHome = process.env.FACTORY_HOME;
  process.env.FACTORY_HOME = join(root, "factory-home");
  t.after(() => {
    if (factoryHome === undefined) delete process.env.FACTORY_HOME;
    else process.env.FACTORY_HOME = factoryHome;
    rmSync(root, { recursive: true, force: true });
  });
  const hooks = [];
  await module.default.setup({
    location: { directory: root },
    session: {
      async hook(name, callback) {
        hooks.push({ name, callback });
      },
    },
  });
  assert.equal(hooks.length, 1);
  assert.equal(hooks[0].name, "prompt");
  return { root, prompt: hooks[0].callback };
}

function event(text, sessionID = "session-1", messageID = "message-1") {
  return { sessionID, messageID, prompt: { text }, delivery: "steer" };
}

test("exports a V2 default definition with a stable id and setup", () => {
  assert.equal(module.default?.id, "ui-agent-trigger");
  assert.equal(typeof module.default?.setup, "function");
});

test("arms each supported text trigger without changing existing prompt fields", async (t) => {
  const { prompt } = await fixture(t);
  for (const [i, text] of ["Build UI", "Check UX", "Open mockup.pen", "pen.dev design", "FIGMA node"].entries()) {
    const input = event(text, `session-${i}`);
    input.metadata = { source: "test" };
    input.prompt.agents = [{ name: "reviewer", mention: { start: 0, end: 5 } }];
    const original = structuredClone(input);
    await prompt(input);
    assert.ok(input.prompt.text.startsWith(`${text}\n\n[ui-agent]`));
    assert.match(input.prompt.text, /Invoke the ui-agent skill now/);
    assert.deepEqual({ ...input, prompt: { ...input.prompt, text } }, original);
    const injected = input.prompt.text;
    await prompt(input);
    assert.equal(input.prompt.text, injected);
  }
});

test("ignores unrelated text and does not latch until a match", async (t) => {
  const { prompt } = await fixture(t);
  for (const text of [undefined, "", "Build a parser for liquid and luxury data"]) {
    const input = event(text);
    await prompt(input);
    assert.equal(input.prompt.text, text);
  }
  const input = event("Review UI");
  await prompt(input);
  assert.match(input.prompt.text, /\[ui-agent\]/);
});

test("matches V2 attachment names and URIs, including attachment-only prompts", async (t) => {
  const { prompt } = await fixture(t);
  for (const [i, file] of [
    { uri: "data:application/octet-stream;base64,AA==", name: "design.pen" },
    { uri: "file:///designs/screen.pen" },
    { uri: "file:///designs/node.json", name: "Figma node" },
  ].entries()) {
    const input = event(undefined, `session-${i}`);
    input.prompt.files = [file];
    await prompt(input);
    assert.match(input.prompt.text, /^\[ui-agent\]/);
    assert.deepEqual(input.prompt.files, [file]);
  }
});

test("latches per session, but reinjects on retry of the triggering message", async (t) => {
  const { prompt } = await fixture(t);
  const first = event("Review UI");
  await prompt(first);
  const injected = first.prompt.text;
  await prompt(first);
  assert.equal(first.prompt.text, injected);
  const retry = event("Review UI");
  await prompt(retry);
  assert.equal(retry.prompt.text, injected);
  const later = event("Review UI", "session-1", "message-2");
  await prompt(later);
  assert.equal(later.prompt.text, "Review UI");
  const other = event("Review UI", "session-2", "message-3");
  await prompt(other);
  assert.match(other.prompt.text, /\[ui-agent\]/);
});

test("worktree factory state suppresses injection without latching", async (t) => {
  const { root, prompt } = await fixture(t);
  const state = join(root, "specs", "001-feature", "factory", "state.json");
  mkdirSync(join(root, "specs", "001-feature", "factory"), { recursive: true });
  writeFileSync(state, "{}");
  const input = event("Review UI");
  await prompt(input);
  assert.equal(input.prompt.text, "Review UI");
  rmSync(state);
  await prompt(input);
  assert.match(input.prompt.text, /\[ui-agent\]/);
});

test("pending factory state suppresses injection without latching", async (t) => {
  const { prompt } = await fixture(t);
  const pending = join(process.env.FACTORY_HOME, "pending");
  mkdirSync(pending, { recursive: true });
  const state = join(pending, "run.json");
  writeFileSync(state, "{}");
  const input = event("Review UI");
  await prompt(input);
  assert.equal(input.prompt.text, "Review UI");
  rmSync(state);
  await prompt(input);
  assert.match(input.prompt.text, /\[ui-agent\]/);
});
