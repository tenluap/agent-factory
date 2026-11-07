# Source: pen.dev

Read once, at the start of `implement` Discover. Pinned to pen `0.3.14` (`execute.md` in `@pen.dev/cli`).

## Access

1. `pen version` must report `0.3.14`. Otherwise stop and report the version gap with a proposed diff to this file, drawn from the docs under `$(npm root -g)/@pen.dev/cli/dist/out/skills/pen-dev/`. Edit this file and continue only on approval. Run `pen status` once. A missing CLI or login is a blocker: ask. Never install globally or sign up without approval.
2. Read designs only through `pen-read.py`. Read `.pen` bytes no other way; `shasum` for the cache hash is the only exception. Never guess a signature. Do not load `pen-design`.
3. Cache: `~/Library/Caches/design-to-code/<hash16>/<targetId>/<scale>-<theme>/`. `<hash16>` is the first 16 hex characters of `shasum -a 256 source.pen`. Write `manifest.json` last, after every section succeeds. Reuse the cache only when the manifest matches hash, target, scale, and theme. A live app has no hash: refresh on resume.
4. Unknown target: run `Get((n,c)=>{c.skipChildren();Print(n.id,n.type,n.name)})` once, or `get_app_state` for a live app.
5. Failed call: read-only sections resend a corrected snippet. Design writes follow the pen docs (`edits` plus `editId`; never resend). Test `edits` in file mode once before relying on it.

## Survey (once per manifest)

Skip when the manifest matches. Otherwise run one `pen-read.py` call with this commands file. Replace `ID`, `<scale>`, and `<cache>` (absolute; pen resolves relative paths against its own working directory):

```
#! rows
execute({ input: 'Get("ID",(n,c)=>Print([n.id,n.type,n.name||"",c.depth,c.index,+c.bounds.x.toFixed(2),+c.bounds.y.toFixed(2),+c.bounds.width.toFixed(2),+c.bounds.height.toFixed(2),n.ref||"",c.problems||""].join("\t")),{resolveInstances:true})' })
#! refs
execute({ input: 'Get("ID",n=>{if(n.type==="ref")Print(n.id+"\t"+n.ref)})' })
#! full
execute({ input: 'const seen=new Set(["ID"]),todo=["ID"];while(todo.length){const id=todo.pop();Print(Get(id,{includePathGeometry:true}));Get(id,n=>{if(n.type==="ref"&&!seen.has(n.ref)){seen.add(n.ref);todo.push(n.ref)}})}' })
#! vars
execute({ input: 'Print(GetVariables())' })
#! ref
execute({ input: 'Export(["ID"],"png","<cache>",{scale:<scale>})' })
```

- `rows.txt`: id, type, name, depth, index, x, y, width, height, ref, problems, with instances expanded so their internals are surveyed. Instance descendants have path IDs (`<instanceId>/<childId>`); the ref column is empty because instances resolve to frames. x and y are parent-relative; a child's x includes its parent's padding. Load only an outline: `awk -F'\t' '$4<=3' rows.txt`.
- `refs.txt`: `<instanceId>\t<componentId>` for every instance under the target. Use it for components, instance counts, and `instanceIds`.
- `full.txt`: one JSON document per line: the target, then each referenced definition, transitively. Query with jq.
- `vars.txt`: `{ variables, themes }`. A variable's `value` is a plain value or an array of `{ value, theme }`. Resolve a token only from the entry whose `theme.mode` matches the validation theme. Map tokens by raw name (`$bg`).
- `<cache>/<ID>.png`: reference image. Read it at most once. Code edits never invalidate the survey.

## API excerpt

- `Get(path, options?)`: one node with nested children. Options: `depth` (0 = node only), `resolveVariables`, `resolveInstances`, `includePathGeometry`. Default keeps raw token names.
- `Get(path, visit, options?)` or `Get(visit, options?)`: top-down visit. `ctx`: `node`, `parentCtx`, `depth`, `index`, `bounds` (parent space), `problems` (`partially clipped` or `fully clipped`), `skipChildren()`.
- `Print(...values)`: one line per call; strings raw, other values JSON.
- `Export(nodeIds, "png", outputDir, { scale })`: writes `<nodeId>.png`. Default scale 2.
- Writes, refused by `pen-read.py`: `Insert`, `Copy`, `Update`, `Replace`, `Move`, `Delete`, `SetVariables`, `Generate`, `save()`.
- A failed call prints nothing; the error names the call and an `editId`.

## Design edits

Only on explicit request. Write a NEW `.pen` output through the CLI. Call `save()` only for that output, outside `pen-read.py`.
