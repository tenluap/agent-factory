# Capture contract

Read once, before the first capture. The framework file names the backend; this file defines what every backend must produce.

## Command

`commands.capture` is one command line with the placeholders `<id>`, `<dir>`, `<scale>`, and `<theme>`. It writes `<dir>/capture.png` and `<dir>/bounds.json` and exits non-zero on failure. Delete both outputs before each run; outputs older than the command start are a capture failure.

`commands.launch`, when the capture needs a server, is one runnable shell command started once from the project root before capture (for example `python3 -m http.server 8000 --bind 127.0.0.1`); a command that only works from a subdirectory carries its own `cd`. No annotations, environment notes, or trailing prose — the verifier starts it as written, waits, and stops it afterward.

## Outputs

- `capture.png`: the target root only, at design width × scale by design height × scale (from `rows.txt`; a frame target equals the viewport). It must equal the reference PNG size; `pixel-diff.py` never resizes. Crop to the root when the host renders more.
- `bounds.json`: `{"root": "<root anchor>", "elements": {"<anchor path>": {"x", "y", "width", "height"}}}`, in DIPs (CSS px on the web), relative to the root's top-left.
- Anchor path: the anchors of the anchored ancestors below the root, then the element's own, joined with `/` (for example `Card1/Title`). The root's key is its own anchor. Paths keep repeated names inside component scopes distinct. The writer fails on a duplicate path. `codeAnchor.anchor` stores the same path.

## Determinism

Every backend: animations and transitions off, focus cleared, caret hidden, exact viewport, fonts loaded before capture, theme applied through the framework's theme mechanism.

## Backends

| Backend | `captureMethod` | Used by | Machine-dependent |
|---|---|---|---|
| Headless test project | `headless` | Avalonia | no |
| DevTools screenshot | `devtools` | Avalonia fallback | yes |
| `web-capture.mjs` | `playwright` | Blazor, React, Next.js, HTML/JS/CSS | no |
| App-hosted capture hook | `device` | MAUI | yes |

`web-capture.mjs` runs from the web project root with the project's own Playwright:

```
node <skill>/scripts/web-capture.mjs --url <harness-url> --root <root anchor> --out <dir> --scale <scale> --theme <theme> --width <w> --height <h>
```

It sets `deviceScaleFactor`, `colorScheme`, reduced motion, and `data-theme` on `<html>`, waits for `document.fonts.ready`, and fails when the root size differs from `--width` × `--height`. Store it in `commands.capture` with the harness URL pattern filled in.

## Pass rule

1. `bounds-diff.py rows.txt bounds.json map.json`: exit 0 with the full `checked` count (±1 DIP). Confirm text-only mismatches with one fresh survey. Store `boundsResult`.
2. `pixel-diff.py <ref> capture.png --montage <file> --max-diff <threshold>`: exit 0. View the montage only. Check clipping, overflow, text, icons, and stretch. Exit 2 is an input error, not a fidelity failure; exit 3 means fix the capture size.

Flag machine-dependent captures in the report.
