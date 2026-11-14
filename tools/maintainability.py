#!/usr/bin/env python3
"""One job: measure a repo against the owner's code principle, so "well organised" is checked.

The principle itself is `references/maintainability.md`; this is its instrument. Four rules are
mechanical, so they are measured here rather than judged by eye:

  M1  a folder past the map limit has a README map          (navigation)
  M2  a large file is MENTIONED in a doc                     (size is debt with a date)
  M3  a source module says its job in its first lines        (one job per module)
  M4  a link in a LIVING doc resolves                        (docs move with the code)

Two rules are NOT mechanical and are not faked here: "extract jobs, not hubs" and "comments say
why" need a reader. The report says so rather than printing a clean line that implies otherwise —
a blind instrument reporting like a seeing one is the thing the audit exists to catch (S20).

WHAT M2 ACTUALLY PROVES, because it is weaker than its name suggests: it finds a large file that no
markdown file mentions. It does NOT check that the mention is a real debt entry with a next cut and
a date, which is what the principle asks for. A reader must open the entry and judge it. Raised by
a Codex review of this tool, 2026-11-14.

Usage:  python maintainability.py <path> [--json] [--rule M1,M2]

Works on any directory, not only a checkout. `git ls-files` is preferred where the path is inside a
git worktree: it is what the repository actually contains and it respects ignore rules for free.
Outside a worktree, or with no git, it walks the filesystem instead and SAYS SO — that mode cannot
apply `.gitignore`, so its gaps are candidates for review rather than findings. `.gitignore` is
deliberately not parsed here: doing so would imply a fidelity it could not reliably provide.

Exit 0 = no gaps. Exit 1 = gaps printed. Exit 2 = COULD NOT ENUMERATE, which is deliberately not
the same as "gaps found": a caller must be able to tell a tool that measured and disliked what it
saw from a tool that never measured at all.

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
# Prose in any of the supported languages. A Python module docstring counts: it is THE idiomatic
# way to say a module's job, and omitting it reported tests/consumers.py -- which opens with a
# six-line docstring -- as undocumented.
LEAD_COMMENT_RE = re.compile(r"^\s*(//|/\*|#|\*|\"\"\"|''')")


class CannotEnumerate(Exception):
    """The file list could not be obtained. Reported as exit 2, never as "no gaps"."""


def _git(root: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", root, *args], capture_output=True, text=True)


def _inside_worktree(root: str) -> bool:
    """Is `root` inside a git worktree? Decides which enumeration is honest, nothing else."""
    try:
        out = _git(root, "rev-parse", "--is-inside-work-tree")
    except (OSError, FileNotFoundError):
        return False
    return out.returncode == 0 and out.stdout.strip() == "true"


def _walk(root: str) -> list[str]:
    """Every file under `root`, skipping vendored and generated trees and `.git` itself."""
    found = []
    for base, dirs, names in os.walk(root):
        rel_base = os.path.relpath(base, root).replace("\\", "/")
        rel_base = "" if rel_base == "." else rel_base
        dirs[:] = [d for d in dirs
                   if d != ".git" and not SKIP_RE.search((rel_base + "/" + d).lstrip("/"))]
        for name in names:
            rel = (rel_base + "/" + name).lstrip("/")
            if not SKIP_RE.search(rel):
                found.append(rel)
    return sorted(found)


def enumerate_files(root: str) -> tuple[list[str], str, bool]:
    """The files to measure, how they were found, and whether ignore rules were applied.

    `git ls-files` is preferred INSIDE a worktree: it is what the repository actually contains and
    it honours `.gitignore` for free. Three guards, all from the Codex review of 2026-11-14:

      * a path OUTSIDE a worktree (an unpacked archive, an exported snapshot, a vendored subtree,
        or an untracked directory sitting inside a parent checkout) uses the filesystem walk -- the
        parent's index says nothing about it;
      * `ls-files` FAILING inside a worktree is an enumeration error, not a cue to fall back
        quietly: something is wrong with the repository and a weaker answer would hide it;
      * an EMPTY result must never read as a clean one. Nothing to measure is not nothing wrong.
    """
    if _inside_worktree(root):
        out = _git(root, "ls-files")
        if out.returncode:
            raise CannotEnumerate(
                "inside a git worktree but `git ls-files` failed (%s); refusing to fall back to a "
                "filesystem walk, because a weaker answer here would hide a broken repository"
                % (out.stderr.strip() or "no stderr"))
        files = [f for f in out.stdout.split("\n") if f and not SKIP_RE.search(f)]
        if not files:
            raise CannotEnumerate("`git ls-files` returned nothing for %s; an empty file list is "
                                  "not a clean result" % root)
        return files, "git ls-files", True
    if not os.path.isdir(root):
        raise CannotEnumerate("not a directory: %s" % root)
    files = _walk(root)
    if not files:
        raise CannotEnumerate("no files found under %s; an empty file list is not a clean result"
                              % root)
    return files, "filesystem walk (not a git worktree, or git unavailable)", False


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
        # Matched by PATH, not by basename. Accepting a bare basename let a 778-line
        # `supports/plan/mod.rs` count as named because some doc somewhere says "mod.rs" --
        # and the same hole swallows every index.ts, main.js and __init__.py in a repo.
        # The last two segments are enough for a doc to write `plan/mod.rs` as shorthand.
        p = PurePosixPath(f)
        tail = "/".join(p.parts[-2:]) if len(p.parts) > 1 else p.name
        named = f in corpus or tail in corpus
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


def imported_docs(root: str, files: list[str]) -> set[str]:
    """Markdown files the application imports as CONTENT (`import x from '../TERMS.md?raw'`).

    Their links are resolved against the app's URL at runtime, not against the repo, so M4 must
    not judge them: mixoDental's TERMS.md correctly links to a file that only exists in the built
    output, and reporting it was this rule's first false positive.
    """
    names = {PurePosixPath(f).name: f for f in files if f.endswith(".md")}
    if not names:
        return set()
    found: set[str] = set()
    for f in files:
        if PurePosixPath(f).suffix not in CODE_EXT:
            continue
        try:
            text = open(os.path.join(root, f), encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for name, path in names.items():
            if name in text and re.search(r"(import|require|from)[^\n]*" + re.escape(name), text):
                found.add(path)
    return found


def m4_living_links(root: str, files: list[str]) -> list[dict]:
    """A markdown link in a living doc that resolves to nothing. Dated docs are records: skipped."""
    served = imported_docs(root, files)
    tracked_set = set(files)
    dirs: set[str] = set()
    for t in tracked_set:
        parts = t.split("/")
        for i in range(1, len(parts)):
            dirs.add("/".join(parts[:i]))
    gaps = []
    for f in files:
        if not f.endswith(".md") or DATED_RE.search(f) or f in served:
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
          # The old title said "no doc mentions", which MISDESCRIBED its own output: a file past
          # CUT_LIMIT is reported whether or not it is named, because rule 5 says the cut is taken
          # rather than named, and its detail line then carries no mention complaint at all. A
          # reader who trusted the title went looking for a missing doc entry that was never the
          # finding -- which is the blind-instrument failure (S20) in the instrument built to catch
          # it. The title now names BOTH gates, so the heading and the detail say the same thing.
          "M2": "large files: over %d named as debt, over %d the cut taken" % (DEBT_LIMIT, CUT_LIMIT),
          "M3": "a module over %d lines says its job in prose" % JOB_LINE_LIMIT,
          "M4": "living docs link to files that exist"}


def main() -> int:
    args = [a for a in sys.argv[1:]]
    # `--help` prints what this is and exits 0, doing no work. A stranger's first command is --help,
    # and this tool answered it by treating `-h` as a PATH and failing to enumerate it -- caught by
    # tests/tools/test_cli_help.py in CI, which the pre-push hook does not run. Exit 0 here is the
    # contract; exit 2 below, for no arguments at all, is a usage error and stays 2.
    if any(a in ("-h", "--help") for a in args):
        print(__doc__)
        return 0
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

    # Exit 2, kept distinct from exit 1 on purpose: "I could not measure" and "I measured and found
    # gaps" must not look the same to a caller or to a report.
    try:
        files, source, ignored_applied = enumerate_files(root)
    except CannotEnumerate as err:
        message = "could not enumerate %s: %s" % (root, err)
        if as_json:
            print(json.dumps({"path": root, "error": str(err), "gaps": None}, indent=2))
        else:
            print(message, file=sys.stderr)
        return 2

    gaps: list[dict] = []
    for key in wanted:
        gaps.extend(RULES[key](root, files))

    if as_json:
        print(json.dumps({"path": root, "files": len(files), "source": source,
                          "ignore_rules_applied": ignored_applied, "gaps": gaps}, indent=2))
        return 1 if gaps else 0

    print("%s -- %d files via %s" % (root, len(files), source))
    if not ignored_applied:
        print("     NOTE: this mode measures the supplied tree and cannot apply .gitignore, so")
        print("     generated or ignored files may be counted. Treat the gaps below as CANDIDATES")
        print("     for review, not findings, and re-run inside a checkout to get the real list.")
    for key in wanted:
        rows = [g for g in gaps if g["rule"] == key]
        print("\n%s  %s — %d" % (key, TITLES[key], len(rows)))
        for g in rows:
            print("   %-58s %s" % (g["path"], g["detail"]))
    print("\nNOT measured here, and not claimed clean: 'extract jobs, not hubs' and 'comments say")
    print("why, not what' need a reader. Judge those by hand; this tool is blind to them.")
    print("M2 is TWO gates, and its rows mean different things. Under %d lines it only proves a" % CUT_LIMIT)
    print("large file is UNMENTIONED. Past %d it reports the file whether it is named or not," % CUT_LIMIT)
    print("because rule 5 says the cut is TAKEN there rather than written down -- so such a row is")
    print("never answered by adding a doc entry. Whether a mention is a real debt entry, with a next")
    print("cut and a date, is for a reader to open and judge either way.")
    print("\n%d gaps" % len(gaps))
    return 1 if gaps else 0


if __name__ == "__main__":
    sys.exit(main())
