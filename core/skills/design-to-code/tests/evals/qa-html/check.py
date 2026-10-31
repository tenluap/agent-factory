#!/usr/bin/env python3
"""Grade a qa-mode run on the qa-html fixture.

Usage: python3 -I check.py <run-dir> [--no-report] [--locked]

<run-dir> is a copy of fixture/ after design-to-code qa ran on it. Checks the three
seeded defects and that their elements survived:
  1. header icon-only button has an accessible name (aria-label, aria-labelledby,
     or visible text);
  2. hero image has an alt attribute;
  3. "Notes sync" paragraph text contrast is at least 4.5:1 against its background.
--locked (qa-locked eval): the design governs colors, so check 3 inverts: the
paragraph color must stay #aaaaaa and the report must log it as a "design conflict".
Unless --no-report, <run-dir>/qa-report.md must contain "Status: complete" and
report at most 2 iterations.

Prints one PASS or FAIL line per check. Exit 0 all pass, 1 any fail, 2 input error.
"""

import re
import sys
from html.parser import HTMLParser
from pathlib import Path


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.buttons, self.images, self.paragraphs = [], [], [], []

    def handle_starttag(self, tag, attrs):
        node = {
            "tag": tag,
            "attrs": dict(attrs),
            "text": "",
            "parents": list(self.stack),
        }
        if tag == "button":
            self.buttons.append(node)
        elif tag == "img":
            self.images.append(node)
        elif tag == "p":
            self.paragraphs.append(node)
        if tag not in ("img", "meta", "link", "br", "hr", "input", "path"):
            self.stack.append(node)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index]["tag"] == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        for node in self.stack:
            node["text"] += data


def parse_css(text):
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    rules = []
    for selectors, body in re.findall(r"([^{}]+)\{([^{}]*)\}", text):
        declarations = dict(
            (name.strip(), value.strip())
            for name, value in re.findall(r"([\w-]+)\s*:\s*([^;]+)", body)
        )
        rules.append(([s.strip() for s in selectors.split(",")], declarations))
    return rules


def resolve(value, variables):
    for _ in range(5):
        match = re.search(r"var\(\s*(--[\w-]+)\s*(?:,\s*([^)]+))?\)", value)
        if not match:
            break
        value = value.replace(
            match.group(0), variables.get(match.group(1), match.group(2) or "")
        )
    return value.strip()


def rgb(value):
    value = value.strip().lower()
    named = {"white": "#ffffff", "black": "#000000"}
    value = named.get(value, value)
    match = re.fullmatch(r"#([0-9a-f]{3}|[0-9a-f]{6})", value)
    if match:
        digits = match.group(1)
        if len(digits) == 3:
            digits = "".join(c * 2 for c in digits)
        return tuple(int(digits[i : i + 2], 16) for i in (0, 2, 4))
    match = re.fullmatch(
        r"rgba?\(\s*(\d+)[\s,]+(\d+)[\s,]+(\d+)(?:[\s,/]+([\d.]+%?))?\s*\)", value
    )
    if match:
        alpha = match.group(4)
        if alpha and alpha not in ("1", "100%"):
            return None
        return tuple(int(match.group(i)) for i in (1, 2, 3))
    return None


def luminance(color):
    def channel(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(c) for c in color)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    high, low = sorted((luminance(a), luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def matches(selector, node):
    classes = set(node["attrs"].get("class", "").split())
    if selector == node["tag"]:
        return True
    parts = re.fullmatch(r"(\w*)((?:\.[\w-]+)+)", selector)
    if not parts:
        return False
    tag, wanted = parts.group(1), set(parts.group(2).split(".")[1:])
    return (not tag or tag == node["tag"]) and wanted <= classes


def computed(node, prop, rules, variables):
    chain = node["parents"] + [node]
    for element in reversed(chain):
        value = None
        style = dict(
            (n.strip(), v.strip())
            for n, v in re.findall(
                r"([\w-]+)\s*:\s*([^;]+)", element["attrs"].get("style", "")
            )
        )
        for selectors, declarations in rules:
            if prop in declarations and any(matches(s, element) for s in selectors):
                value = declarations[prop]
        value = style.get(prop, value)
        if value is not None:
            return resolve(value, variables)
    return None


def background(node, rules, variables):
    for element in reversed(node["parents"] + [node]):
        for prop in ("background-color", "background"):
            value = computed(dict(element, parents=[]), prop, rules, variables)
            if value and rgb(value):
                return rgb(value)
    return (255, 255, 255)


def main():
    args = sys.argv[1:]
    want_report = "--no-report" not in args
    locked = "--locked" in args
    args = [a for a in args if a not in ("--no-report", "--locked")]
    if len(args) != 1:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    root = Path(args[0])
    try:
        page = Page()
        page.feed((root / "index.html").read_text())
        css = "\n".join(p.read_text() for p in sorted(root.rglob("*.css")))
    except OSError as error:
        print(f"input error: {error}", file=sys.stderr)
        sys.exit(2)
    rules = parse_css(css)
    variables = {}
    for selectors, declarations in rules:
        if ":root" in selectors or "html" in selectors:
            variables.update(
                {k: v for k, v in declarations.items() if k.startswith("--")}
            )

    results = []
    header_buttons = [
        b for b in page.buttons if any(p["tag"] == "header" for p in b["parents"])
    ]
    if not header_buttons:
        results.append((False, "icon button: header button missing"))
    else:
        b = header_buttons[0]
        named = (
            b["attrs"].get("aria-label", "").strip()
            or b["attrs"].get("aria-labelledby", "").strip()
            or b["text"].strip()
        )
        results.append((bool(named), f"icon button accessible name: {named or 'none'}"))

    hero = [i for i in page.images if "hero" in i["attrs"].get("src", "")]
    if not hero:
        results.append((False, "hero image: missing"))
    else:
        results.append(
            (
                "alt" in hero[0]["attrs"],
                f"hero image alt: {hero[0]['attrs'].get('alt')!r}",
            )
        )

    note = [p for p in page.paragraphs if "Notes sync" in p["text"]]
    if not note:
        results.append((False, "muted paragraph: missing"))
    else:
        fg = rgb(computed(note[0], "color", rules, variables) or "")
        if fg is None:
            results.append(
                (False, "muted paragraph: color not resolvable to opaque hex/rgb")
            )
        else:
            ratio = contrast(fg, background(note[0], rules, variables))
            if locked:
                results.append((fg == (170, 170, 170), f"muted paragraph color kept: {fg}"))
            else:
                results.append((ratio >= 4.5, f"muted paragraph contrast: {ratio:.2f}:1"))

    if want_report:
        report_path = root / "qa-report.md"
        report = report_path.read_text() if report_path.exists() else ""
        results.append(("Status: complete" in report, "report: Status: complete"))
        if locked:
            results.append(("design conflict" in report.lower(), "report: contrast logged as design conflict"))
        counts = [
            int(n)
            for n in re.findall(
                r"(?i)iterations?\D{0,12}(\d+)|(\d+)\s+iterations?", report
            )
            for n in n
            if n
        ]
        results.append(
            (
                bool(counts) and max(counts) <= 2,
                f"report: iterations {counts or 'not found'}",
            )
        )

    for ok, message in results:
        print(("PASS " if ok else "FAIL ") + message)
    sys.exit(0 if all(ok for ok, _ in results) else 1)


if __name__ == "__main__":
    main()
