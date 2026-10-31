# Design-code map (version 3)

Path: `docs/design-code-map.json` in the app project. Read once, before the first map edit. Update the map with jq, once per batch.

```json
{
  "version": 3,
  "framework": "avalonia | maui | blazor | react | nextjs | html-js-css",
  "commands": { "build": "", "test": "", "capture": "", "launch": "" },
  "revisionFiles": [],
  "targets": [{
    "designSource": { "file": "", "frameId": "", "revision": "sha256:<16 hex> or null for a live app", "surveyedAt": "" },
    "validation": [{ "theme": "light", "scale": 2, "viewport": "WxH", "designRevision": "", "codeRevision": "sha256:<16 hex>", "threshold": 0.5, "capture": "WxH@scale theme", "captureMethod": "headless | devtools | playwright | device", "boundsResult": { "result": "pass | fail", "checked": 0, "mismatches": 0, "tolerance": 1 }, "result": "pass | fail" }],
    "components": [], "instances": [], "nodeMap": [], "unmappedDesignNodes": [], "orphanedCode": []
  }]
}
```

## Migration

A map below version 3: run `map-migrate.py <map> <framework>` once before any other edit. It moves version 1 top-level records into `targets[0]`, renames `codeAnchor.xName` to `codeAnchor.anchor`, and sets `framework`. Helpers still read `xName` for safety.

## Records

- Component: `designId`, `designName`, `designPath`, `kind`, `code` (`project`, `file`, `symbol`, `anchor`), `instanceIds`, `instanceCount`, `overrides`, `tokens`, `dependencies`, `status`.
- Instance: `designId`, `componentId`, `parentDesignId`, `overrides`, `codeAnchor` (`file`, `symbol`, `anchor`), `status`.
- nodeMap: `designId`, `parentDesignId`, `coveredBy`, `codeAnchor`, `status`. Generate with `map-coverage.py`; it keeps records that have a `codeAnchor`. Hand-write only components and exceptions.
- `codeAnchor.anchor` (or a component's `code.anchor`) is the anchor path that `bounds-diff.py` looks up in `bounds.json`. The framework file defines what an anchor is. Give every geometry-bearing mapped node one.
- Status: `planned`, `implemented`, `validated`, `stale`, `unmapped`. Mark records `stale` before changing validated design or code. Mark `validated` only with passing evidence for the current validation record. An intentional divergence needs a reason.
- Anchors are exact design IDs and stable file, symbol, anchor, or resource names. Line numbers are hints only.

## Validation record

- Current record: the `validation[]` entry whose `theme`, `scale`, and `viewport` match this run. Create it when absent. "The validation record" always means this entry.
- `codeRevision` comes from `map-revision.py`. A git hash may go in a separate `gitHead` field for humans; it never proves freshness.
- `revisionFiles`: project-relative files that mapped code depends on but no record names (token file, global styles, consumed assets, web layout and global CSS).
- `threshold`: percent from 0 to 0.5, default 0.5. Lower it only after two consecutive passing captures of an unchanged build, to their larger share rounded up to 0.05.
- `boundsResult.checked` must equal the number of geometry-bearing mapped nodes for a bounds pass.

## Resume

Reuse evidence only when `designSource.revision` equals `sha256:<hash16>` and the current record's `codeRevision` equals `map-revision.py` output. Continue from the first invalid gate.
