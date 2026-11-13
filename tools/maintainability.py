#!/usr/bin/env python3
"""One job: measure a repo against the owner's code principle, so "well organised" is checked.

The principle itself is `references/maintainability.md`; this is its instrument. Four rules are
mechanical, so they are measured here rather than judged by eye:

  M1  a folder past the map limit has a README map          (navigation)
  M2  a file past the debt limit is NAMED as debt in a doc   (size is debt with a date)
  M3  a source module says its job in its first lines        (one job per module)
  M4  a link in a LIVING doc resolves                        (docs move with the code)

Two rules are NOT mechanical and are not faked here: "extract jobs, not hubs" and "comments say
why" need a reader. The report says so rather than printing a clean line that implies otherwise —
a blind instrument reporting like a seeing one is the thing the audit exists to catch (S20).

Usage:  python maintainability.py <repo-root> [--json] [--rule M1,M2]

Exit 0 = no gaps. Exit 1 = gaps printed. Exit 2 = could not run (not a git repo).

Dated documents are records, not living docs: M4 skips any doc whose name or folder carries a
date, because correcting a record in place is how it stops being a record.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import PurePosixPath

MAP_LIMIT = 20       # folder files past this need a README map
DEBT_LIMIT = 600     # lines past this must be named as debt
CUT_LIMIT = 1000     # lines past this: the cut is taken, not named
JOB_LINE_LIMIT = 200 # lines past this, the module must say its job in prose (see m3)

CODE_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".rs", ".py", ".go", ".java", ".rb"}
DATA_EXT = {".json", ".stl", ".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp", ".ico",
            ".bin", ".wasm", ".csv", ".txt", ".glb", ".gltf", ".3mf", ".obj", ".woff",
            ".woff2", ".ttf", ".otf", ".snap", ".lock", ".map", ".ply", ".wrl"}
# Vendored or generated: consumed as built, never edited here, so none of the rules apply.
SKIP_RE = re.compile(r"(^|/)(vendor|node_modules|dist|build|out|__pycache__|\.venv|"
                     r"graphify-out|coverage|artefacts|goldens)(/|$)")
DATED_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
# A folder of fixtures/goldens/snapshots is a data store, not a navigation surface.
DATA_FOLDER_RE = re.compile(r"(^|/)(fixtures?|golden|goldens|snapshots?|__snapshots__|"
                            r"corpus|samples?|locales?|assets)(/|$)")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)")
# A leading comment in any of the supported languages.
LEAD_COMMENT_RE = re.compile(r"^\s*(//|/\*|#|\*)")


def git(root: str, *args: str) -> list[str]:
    out = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True)
    if out.returncode:
        raise SystemExit("not a git repo (or git failed): %s" % root)
    return out.stdout.split("\n")


def tracked(root: str) -> list[str]:
    return [f for f in git(root, "ls-files") if f and not SKIP_RE.search(f)]


def line_count(path: str) -> int:
    try:
        with open(path, "rb") as fh:
            return fh.read().count(b"\n") + 1
    except OSError:
        return 0


def m1_folder_maps(root: str, files: list[str]) -> list[dict]:
    """A folder past MAP_LIMIT with no README.

    The exemption tests CONTENTS, not the folder's name: `src/core/assets` is code about assets
    and needs a map, while `tests/fixtures` is a data store and nobody navigates it. Keying this
    on the name exempted the first one on its first run.
    """
    counts: dict[str, int] = {}
    data: dict[str, int] = {}
    has_map: set[str] = set()
    for f in files:
        p = PurePosixPath(f)
        d = str(p.parent)
        if d == ".":
            continue
        counts[d] = counts.get(d, 0) + 1
        if p.suffix.lower() in DATA_EXT:
            data[d] = data.get(d, 0) + 1
        if p.name.upper().startswith("README"):
            has_map.add(d)
    gaps = []
    for d, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        if n <= MAP_LIMIT or d in has_map:
            continue
        if data.get(d, 0) / n > 0.6:
            continue
        gaps.append({"rule": "M1", "path": d, "detail": "%d files, no README map" % n})
    return gaps


def m2_size_debt(root: str, files: list[str]) -> list[dict]:
    """Past DEBT_LIMIT the file must be NAMED in a doc; past CUT_LIMIT naming is not enough."""
    docs = [f for f in files if f.endswith(".md")]
    corpus = ""
    for d in docs:
        try:
            corpus += open(os.path.join(root, d), encoding="utf-8", errors="replace").read()
        except OSError:
            pass
    gaps = []
    for f in files:
        ext = PurePosixPath(f).suffix
        if ext not in CODE_EXT or DATA_FOLDER_RE.search(f):
            continue
        n = line_count(os.path.join(root, f))
        if n <= DEBT_LIMIT:
            continue
        named = f in corpus or PurePosixPath(f).name in corpus
        if n > CUT_LIMIT:
            gaps.append({"rule": "M2", "path": f,
                         "detail": "%d lines, over the %d cut limit%s" % (
                             n, CUT_LIMIT, "" if named else " and not named as debt")})
        elif not named:
            gaps.append({"rule": "M2", "path": f,
                         "detail": "%d lines, not named as debt in any doc" % n})
    return gaps


def m3_job_line(root: str, files: list[str]) -> list[dict]:
    """A module past JOB_LINE_LIMIT lines with no prose anywhere in its head.

    Deliberately narrow, twice over, because the first version of this rule was a bad instrument:

      * It only applies past JOB_LINE_LIMIT. A short module's name and its one export say its job;
        a long one costs a reader minutes before they learn whether it is the file they want. And a
        rule that fires on every small file gets satisfied by pasting a header that restates the
        code, which makes the measure read clean while the codebase gets no better -- a blind
        instrument, the thing this skill exists to catch.
      * It scans the whole head past the import block, not a fixed window. Measuring only the first
        three lines reported `BedFit.js` and `src/kit/Check.tsx` as undocumented when both open with
        prose, because a long import block pushed it out of view.

    What it therefore CANNOT tell you: whether the prose says the job, or merely says something.
    That is the reader's call, and §2 of the doctrine says so rather than implying otherwise.
    """
    gaps = []
    for f in files:
        p = PurePosixPath(f)
        if p.suffix not in CODE_EXT or DATA_FOLDER_RE.search(f):
            continue
        if re.search(r"\.(test|spec)\.[a-z]+$", p.name) or p.stem in {"index", "mod", "__init__"}:
            continue
        if p.suffix == ".rs" and p.stem == "lib":
            continue
        full = os.path.join(root, f)
        if line_count(full) <= JOB_LINE_LIMIT:
            continue
        try:
            head = open(full, encoding="utf-8", errors="replace").read(8000)
        except OSError:
            continue
        lines = [ln for ln in head.split("\n") if ln.strip()][:40]
        if not lines:
            continue
        if not any(LEAD_COMMENT_RE.match(ln) for ln in lines):
            gaps.append({"rule": "M3", "path": f,
                         "detail": "%d lines, no prose in its head saying the module's job"
                                   % line_count(full)})
    return gaps


def m4_living_links(root: str, files: list[str]) -> list[dict]:
    """A markdown link in a living doc that resolves to nothing. Dated docs are records: skipped."""
    tracked_set = set(files)
    dirs: set[str] = set()
    for t in tracked_set:
        parts = t.split("/")
        for i in range(1, len(parts)):
            dirs.add("/".join(parts[:i]))
    gaps = []
    for f in files:
        if not f.endswith(".md") or DATED_RE.search(f):
            continue
        base = str(PurePosixPath(f).parent)
        try:
            text = open(os.path.join(root, f), encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for raw in LINK_RE.findall(text):
            if raw.startswith(("http://", "https://", "mailto:", "#", "<")):
                continue
            target = raw.split("#")[0].split("?")[0]
            if not target:
                continue
            joined = os.path.normpath(os.path.join("" if base == "." else base, target))
            cand = joined.replace("\\", "/")
            if cand in tracked_set or cand in dirs or os.path.exists(os.path.join(root, cand)):
                continue
            gaps.append({"rule": "M4", "path": f, "detail": "link does not resolve: %s" % raw})
    return gaps


RULES = {"M1": m1_folder_maps, "M2": m2_size_debt, "M3": m3_job_line, "M4": m4_living_links}
TITLES = {"M1": "folder maps (over %d files)" % MAP_LIMIT,
          "M2": "size debt (over %d named, over %d cut)" % (DEBT_LIMIT, CUT_LIMIT),
          "M3": "a module over %d lines says its job in prose" % JOB_LINE_LIMIT,
          "M4": "living docs link to files that exist"}


def main() -> int:
    args = [a for a in sys.argv[1:]]
    as_json = "--json" in args
    args = [a for a in args if a != "--json"]
    wanted = list(RULES)
    for a in list(args):
        if a.startswith("--rule"):
            wanted = (a.split("=", 1)[1] if "=" in a else args[args.index(a) + 1]).split(",")
            args = [x for x in args if x != a and x != ",".join(wanted)]
    if not args:
        print(__doc__)
        return 2
    root = os.path.abspath(args[0])
    files = tracked(root)

    gaps: list[dict] = []
    for key in wanted:
        gaps.extend(RULES[key](root, files))

    if as_json:
        print(json.dumps({"repo": root, "files": len(files), "gaps": gaps}, indent=2))
        return 1 if gaps else 0

    print("%s -- %d tracked files (vendored and generated paths excluded)" % (root, len(files)))
    for key in wanted:
        rows = [g for g in gaps if g["rule"] == key]
        print("\n%s  %s — %d" % (key, TITLES[key], len(rows)))
        for g in rows:
            print("   %-58s %s" % (g["path"], g["detail"]))
    print("\nNOT measured here, and not claimed clean: 'extract jobs, not hubs' and 'comments say")
    print("why, not what' need a reader. Judge those by hand; this tool is blind to them.")
    print("\n%d gaps" % len(gaps))
    return 1 if gaps else 0


if __name__ == "__main__":
    sys.exit(main())
