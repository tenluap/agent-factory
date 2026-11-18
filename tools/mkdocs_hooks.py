"""MkDocs hook: point relative links that leave docs/ at the file on GitHub.

Existing docs link to source files such as ../core/skills/factory/SKILL.md.
Those files are not part of the site, so rewrite them to repo URLs instead of
editing every source doc.
"""

import posixpath
import re

REPO_BLOB = "https://github.com/tenluap/claude-factory/blob/main/"
LINK = re.compile(r"\]\((\.\./[^)\s]+)\)")


def on_page_markdown(markdown, page, config, files):
    page_dir = posixpath.dirname(page.file.src_uri)

    def rewrite(match):
        target = match.group(1)
        path, sep, anchor = target.partition("#")
        resolved = posixpath.normpath(posixpath.join(page_dir, path))
        if not resolved.startswith(".."):
            return match.group(0)
        repo_path = posixpath.normpath(posixpath.join("docs", page_dir, path))
        return f"]({REPO_BLOB}{repo_path}{sep}{anchor})"

    return LINK.sub(rewrite, markdown)
