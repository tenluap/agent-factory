# Library skills are linked from their source folders, not rendered

The factory skill and role agents reach a harness through the rendered distribution (ADR 0005), but library skills do not. Each library skill is symlinked from its own folder (repo layer `skills/<name>/` or per-user layer `${FACTORY_HOME}/skills/<name>/`) straight into the harness's skills root. Vendored skills are verbatim third-party copies with their upstream LICENSE, and per-user skills live outside the checkout. Rendering either one would rewrite attributed content, and for per-user skills it would put user files into tracked output. Linking keeps `dist/` and its porcelain gate unaffected by library content.

## Considered options

- **Render library skills into `dist/`**: this would give one install path for everything. But it would modify verbatim upstream files, couple the dist gate to third-party content, and could not cover the per-user layer without committing user files.
- **Copy skills into skills roots**: this needs no symlink support. But copies drift from the library, and the installer could no longer tell its own files from user files, which breaks the rule that the installer never deletes or overwrites user files.
- **Symlink from source folders** (chosen): an update takes effect with no reinstall, and ownership is decidable. A link pointing into a library layer is the installer's own. Anything else at that path is skipped.

## Consequences

The installer needs a separate link helper for library links. The factory-skill helper replaces foreign symlinks; the library helper skips them. Because ownership is decided by link target, the library helper can also remove its own links whose source folder is gone, and uninstall removes links without touching either layer. The name `factory` is reserved so a library link never contends with the factory skill link.
