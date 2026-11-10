"""route.py's COMPANIONS line: which skills and CLIs from companion-skills.md §2 are installed on this machine.

Split from route.py on 2026-11-09. Reads only the user's agent folders and PATH, never the project.
"""
from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]


CLI_NAMES = "graphify cgc gh docker npx playwright stitch codex claude".split()
SKILL_NAME = re.compile(r"[A-Za-z][\w-]*(?::[\w-]+)?")   # `name` or `plugin:name`


def companion_names():
    """Backticked tokens of the Companion column (2nd) of the §2 table — read at run time so the
    doctrine stays the one list; a copy here would drift the day the table changes."""
    f = SKILL_ROOT / "references" / "companion-skills.md"
    try:
        text = f.read_text(encoding="utf-8")
    except OSError:
        return []
    names, in_table = [], False
    for line in text.splitlines():
        if re.match(r"\|\s*When\s*\|\s*Companion\b", line):
            in_table = True
        elif in_table:
            if not line.startswith("|"):
                break
            cells = line.split("|")
            if len(cells) > 2 and not set(cells[2].strip()) <= set("-: "):
                for t in re.findall(r"`([^`\s]+)`", cells[2]):
                    t = t.lstrip("/")
                    # A row may backtick what the companion delivers (`.svg`, `<img>`): only a
                    # skill-shaped token is a name, or the COMPANIONS line reports a file type
                    # as a missing skill and sends the run to "find, vet, install" it.
                    if not SKILL_NAME.fullmatch(t):
                        continue
                    if t not in names:
                        names.append(t)
    return names


def _subdirs(p: Path):
    try:
        return {c.name for c in p.iterdir() if c.is_dir()}
    except OSError:
        return set()


def _marketplace_names(home: Path):
    """Skill dirs (parent named `skills`) and command stems (parent named `commands`) under
    ~/.claude/plugins/marketplaces; depth- and count-capped so a huge plugin tree cannot stall step 0."""
    base, out, seen = home / ".claude" / "plugins" / "marketplaces", set(), 0
    if not base.is_dir():
        return out
    for cur, dnames, fnames in os.walk(base, followlinks=False):
        seen += 1
        if seen > 20000 or len(Path(cur).relative_to(base).parts) > 6:
            dnames[:] = []
            continue
        parent = Path(cur).name
        if parent == "skills":
            out |= set(dnames)
        if parent == "commands":
            out |= {os.path.splitext(f)[0] for f in fnames if f.endswith(".md")}
    return out


def _plugin_ids(home: Path):
    """Keys of ~/.claude/plugins/installed_plugins.json (`name@marketplace`); {} if absent/unreadable."""
    try:
        data = json.loads((home / ".claude" / "plugins" / "installed_plugins.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    plugins = data.get("plugins", data) if isinstance(data, dict) else {}
    return plugins if isinstance(plugins, dict) else {}


def scan_companions(home: Path):
    table = companion_names()
    dirs = set()
    for sub in (".claude/skills", ".codex/skills", ".agents/skills"):
        dirs |= _subdirs(home / sub)
    avail = dirs | _marketplace_names(home)

    def part(t):  # `design:ux-copy` lives in a directory called `ux-copy`
        return t.split(":")[-1]

    plugins = _plugin_ids(home)

    def present(t):
        # `plugin:skill` is installed when the plugin is: its skill folders may be named
        # differently (egm:egm-review lives in egm_review), so a folder-name probe alone
        # would report an installed plugin "missing" and push the AI to reinstall it.
        if ":" in t:
            plug = t.split(":")[0]
            pdir = home / ".claude" / "plugins"
            return ((pdir / "marketplaces" / plug).exists() or (pdir / "cache" / plug).exists()
                    or any(k.startswith(plug + "@") for k in plugins))
        return t in avail

    return {"installed": [t for t in table if present(t) or part(t) in avail],
            "other": len(dirs - {part(t) for t in table}),
            "missing": [t for t in table if not (present(t) or part(t) in avail)],
            "clis": [c for c in CLI_NAMES if shutil.which(c)], "table_read": bool(table)}


def resolve_home():
    """HOME/USERPROFILE override exists for tests. On Windows prefer USERPROFILE: Git-Bash exports
    HOME as /c/Users/x, which Python-for-Windows cannot open."""
    order = ("USERPROFILE", "HOME") if os.name == "nt" else ("HOME", "USERPROFILE")
    for k in order:
        if os.environ.get(k):
            return Path(os.environ[k])
    return Path.home()
