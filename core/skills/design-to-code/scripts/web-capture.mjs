#!/usr/bin/env node
// Capture one design target from a running web page for design-to-code validation.
//
// Usage: node web-capture.mjs --url <url> --root <anchor> --out <dir> --scale <n>
//          --theme <light|dark> --width <w> --height <h> [--attr data-design-id]
//
// Run from the web project root: Playwright resolves from the project's own
// node_modules (`playwright` or `@playwright/test`), never a global install.
// Writes <dir>/capture.png (the root element only, at width × scale by
// height × scale) and <dir>/bounds.json:
//   {"root": "<root anchor>", "elements": {"<anchor path>": {x, y, width, height}}}
// in CSS px relative to the root. An anchor path joins the --attr values of the
// anchored ancestors below the root, then the element's own (Card1/Title).
// Determinism: reduced motion, transitions and animations off, caret hidden,
// focus cleared, fonts loaded, color scheme and data-theme set to --theme.
//
// Exit codes: 0 captured, 1 capture failure (root missing, size mismatch,
// duplicate anchor path, page error), 2 input error, Playwright missing, or no
// launchable Chromium (bundled build first, then installed Google Chrome).

import { createRequire } from "node:module";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";

const USAGE =
  "usage: node web-capture.mjs --url <url> --root <anchor> --out <dir> --scale <n> " +
  "--theme <light|dark> --width <w> --height <h> [--attr data-design-id]";

function parseArgs(argv) {
  const args = { attr: "data-design-id" };
  for (let i = 0; i < argv.length; i += 2) {
    const key = argv[i]?.replace(/^--/, "");
    if (!key || argv[i + 1] === undefined) return null;
    args[key] = argv[i + 1];
  }
  for (const key of ["url", "root", "out", "scale", "theme", "width", "height"]) {
    if (!args[key]) return null;
  }
  for (const key of ["scale", "width", "height"]) {
    args[key] = Number(args[key]);
    if (!(args[key] > 0)) return null;
  }
  if (!["light", "dark"].includes(args.theme)) return null;
  return args;
}

function loadPlaywright() {
  // Walk up from cwd: the project's own Playwright may sit in a nested
  // package (tests/visual) while the recorded command runs from the root.
  let dir = process.cwd();
  for (;;) {
    const require = createRequire(join(dir, "package.json"));
    for (const name of ["playwright", "@playwright/test"]) {
      try {
        return require(name);
      } catch {}
    }
    const parent = dirname(dir);
    if (parent === dir) return null;
    dir = parent;
  }
}

function fail(code, message) {
  console.error(message);
  process.exit(code);
}

const args = parseArgs(process.argv.slice(2));
if (!args) fail(2, USAGE);
const playwright = loadPlaywright();
if (!playwright) fail(2, "Playwright not found in the project's node_modules");

async function launch() {
  for (const options of [{}, { channel: "chrome" }]) {
    try {
      return await playwright.chromium.launch(options);
    } catch {}
  }
  return null;
}

const browser = await launch();
if (!browser) fail(2, "No Chromium for this Playwright version: run `npx playwright install chromium`");
try {
  const context = await browser.newContext({
    viewport: { width: args.width, height: args.height },
    deviceScaleFactor: args.scale,
    colorScheme: args.theme,
    reducedMotion: "reduce",
  });
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto(args.url, { waitUntil: "networkidle" });
  await page.addStyleTag({
    content:
      "*,*::before,*::after{transition:none!important;animation:none!important;caret-color:transparent!important}",
  });
  const result = await page.evaluate(
    async ({ attr, rootName, theme }) => {
      document.documentElement.dataset.theme = theme;
      document.activeElement?.blur?.();
      await document.fonts.ready;
      const root = [...document.querySelectorAll(`[${attr}]`)].find(
        (el) => el.getAttribute(attr) === rootName,
      );
      if (!root) return { error: `root [${attr}="${rootName}"] not found` };
      const origin = root.getBoundingClientRect();
      const elements = {};
      for (const el of [root, ...root.querySelectorAll(`[${attr}]`)]) {
        const names = [];
        for (let node = el; node && node !== root; node = node.parentElement) {
          if (node.hasAttribute(attr)) names.unshift(node.getAttribute(attr));
        }
        const path = el === root ? rootName : names.join("/");
        if (elements[path]) return { error: `duplicate anchor path ${path}` };
        const rect = el.getBoundingClientRect();
        elements[path] = {
          x: rect.x - origin.x,
          y: rect.y - origin.y,
          width: rect.width,
          height: rect.height,
        };
      }
      return { elements };
    },
    { attr: args.attr, rootName: args.root, theme: args.theme },
  );
  if (result.error) throw new Error(result.error);
  if (errors.length) throw new Error(`page errors:\n${errors.join("\n")}`);
  const size = result.elements[args.root];
  if (Math.abs(size.width - args.width) > 0.5 || Math.abs(size.height - args.height) > 0.5) {
    throw new Error(
      `root is ${size.width}x${size.height}, expected ${args.width}x${args.height}; fix the harness size`,
    );
  }
  mkdirSync(args.out, { recursive: true });
  await page
    .locator(`[${args.attr}="${args.root}"]`)
    .first()
    .screenshot({ path: join(args.out, "capture.png"), animations: "disabled", caret: "hide" });
  writeFileSync(
    join(args.out, "bounds.json"),
    JSON.stringify({ root: args.root, elements: result.elements }, null, 1) + "\n",
  );
  console.log(`captured ${Object.keys(result.elements).length} anchors`);
} catch (error) {
  console.error(`capture failed: ${error.message}`);
  process.exitCode = 1;
} finally {
  await browser.close();
}
