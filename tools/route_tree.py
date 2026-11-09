"""route.py's tree reader: one walk of the project under the skip, secret and symlink rules, plus the evidence helpers.

Split from route.py on 2026-11-09 (843 lines, named as debt). The safety contract in route.py's docstring
lives here in code: secrets are never opened, links never followed, evidence is a token and never a whole
line. tools/sweep_leads.py walks the tree through this module too, so both scans skip and hide the same files.
"""
from __future__ import annotations

import os
import re

SKIP_DIRS = frozenset(
    ".git node_modules dist build vendor __pycache__ .venv venv graphify-out target .next "
    "coverage .ruff_cache .pytest_cache".split())
MAX_BYTES = 2 * 1024 * 1024
TEST_DIRS = frozenset({"tests", "test", "__tests__", "spec", "specs"})

SRC_EXTS = frozenset(
    ".py .js .mjs .cjs .jsx .ts .tsx .go .rb .php .java .kt .rs .c .cc .cpp .h .hpp .cs "
    ".swift .vue .svelte".split())
STR_PAGE_EXTS = frozenset({".py", ".php", ".js", ".ts", ".go", ".rb"})
TEXT_EXTS = SRC_EXTS | frozenset(
    ".html .htm .jinja .jinja2 .twig .tpl .md .txt .toml .json .yaml .yml .cfg .ini .sql "
    ".xml .mod .lock .gradle .sum".split())
TEMPLATE_RE = re.compile(r"\.(html?|jinja\w*|twig|tpl|vue|svelte)$|\.blade\.php$", re.I)

UNKNOWN_TEXT = ("not scanned: callers outside the tree (cron, systemd, CI of another repo), "
                "dynamic route registration, templates outside "
                "*.html/*.jinja/*.twig/*.tpl/*.vue/*.svelte  (evidence.md §E5 boundary)")


# --------------------------------------------------------------------------- reading the tree

class Rec:
    """One non-skipped file. `lines` is None when unreadable, binary, secret or over 2 MB."""
    __slots__ = ("rel", "name", "ext", "lines", "mtime")

    def __init__(self, rel, name, ext, lines, mtime):
        self.rel, self.name, self.ext, self.lines, self.mtime = rel, name, ext, lines, mtime


def is_secret(name: str) -> bool:
    low = name.lower()
    if low.startswith(".env") or low.endswith((".pem", ".key", ".p12", ".pfx")):
        return True
    # `id_rsa`, `id_ed25519.pub` — but not `id_helper.py`, which is source, not a key.
    return low.startswith("id_") and os.path.splitext(low)[1] in ("", ".pub")


def _is_link(path: str) -> bool:
    junction = getattr(os.path, "isjunction", None)  # Windows junctions are links too (3.12+)
    return os.path.islink(path) or bool(junction and junction(path))


def _wants_text(name: str, ext: str) -> bool:
    return (ext in TEXT_EXTS or name in ("Makefile", "Procfile", "Gemfile", "Pipfile", "Dockerfile")
            or name.startswith(("requirements", "README")))


def _read_lines(path: str):
    try:
        if os.path.getsize(path) > MAX_BYTES:
            return None
        with open(path, "rb") as fh:
            data = fh.read()
    except OSError:
        return None
    if b"\0" in data[:2048]:
        return None
    return data.decode("utf-8", "replace").splitlines()


def walk(root: str):
    """Return (records, all_paths, dir_paths, skipped_dir_names); deterministic order."""
    recs, paths, dirs, skipped = [], set(), set(), set()
    for cur, dnames, fnames in os.walk(root, followlinks=False):
        keep = []
        for d in sorted(dnames):
            full = os.path.join(cur, d)
            if d in SKIP_DIRS:
                skipped.add(d)
            elif not _is_link(full):
                keep.append(d)
                dirs.add(os.path.relpath(full, root).replace(os.sep, "/"))
        dnames[:] = keep
        for f in sorted(fnames):
            full = os.path.join(cur, f)
            if _is_link(full):
                continue
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            paths.add(rel)
            ext = os.path.splitext(f)[1].lower()
            lines = None
            if not is_secret(f) and _wants_text(f, ext):
                lines = _read_lines(full)
            try:
                mtime = os.path.getmtime(full)
            except OSError:
                mtime = 0.0
            recs.append(Rec(rel, f, ext, lines, mtime))
    return recs, paths, dirs, sorted(skipped)


def ev(rel, ln, tok):
    return {"at": f"{rel}:{ln}", "tok": " ".join(str(tok).split())[:80]}


def evs(items, n=2):
    return " , ".join(f"{e['at']} `{e['tok']}`" for e in items[:n])


def _first(pattern: re.Pattern, recs):
    """First match per file of `pattern`, as evidence rows, in path order."""
    out = []
    for r in recs:
        if r.lines is None:
            continue
        for i, line in enumerate(r.lines, 1):
            m = pattern.search(line)
            if m:
                out.append(ev(r.rel, i, m.group(0)))
                break
    return out
