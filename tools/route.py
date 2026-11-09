"""Step-0 project scan: facts with path:line that tell the cia skill which references, graphs and companions to engage — leads, never verdicts.

Usage: python tools/route.py <project-root> [--json] [--no-timing]

Why it exists: routing by memory or by the project's name is how a skill engages the wrong
references. This reads the tree once, prints what is really there with evidence, and names the
reference file each fact routes to. It does not grade, does not resolve test or lint commands
(SKILL §0.5 does, from the BINDINGS facts), and exit code is 0 on success, 2 on a missing root —
it is a lead, never a gate.

Safety contract (each line is a trap this file avoids):
  * read-only: nothing is written, no project code runs, no package manager, no network;
  * secrets: `.env*`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `id_*` are never opened — their NAME is
    the whole fact. Opening `.env` "just to count keys" is how a token ends up in a transcript;
  * symlinks and junctions are never followed, so a link out of the root cannot widen the scan;
  * evidence is the matched token (<= 80 chars), never a whole line of file content;
  * identifiers only for commerce: the bare word "order" is SQL `ORDER BY` and `OrderedDict`.
"""
from __future__ import annotations

import argparse
import bisect
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

VERSION = 1
SKILL_ROOT = Path(__file__).resolve().parents[1]

# Pinned to references/code-graph-tools.md §1 by tests/tools/test_route.py: change one side
# alone and the test is red. Do not "tune" these here.
FILES_THRESHOLD = 200      # "more than about 200 source files"
LINES_THRESHOLD = 50_000   # "or about 50,000 lines"
PACKAGES_THRESHOLD = 3     # "three or more top-level packages with cross-imports"


# The tree reader, the companion probe and the renderer are their own modules (split 2026-11-09); their
# names are re-exported here because tests and runs call route.walk, route.is_secret, route.render.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from route_tree import (  # noqa: E402,F401  (re-exported: route.walk, route.is_secret)
    MAX_BYTES,
    Rec,
    SKIP_DIRS,
    SRC_EXTS,
    STR_PAGE_EXTS,
    TEMPLATE_RE,
    TEST_DIRS,
    ev,
    is_secret,
    walk,
)
from route_tree import _first, _is_link, _read_lines, _wants_text  # noqa: E402,F401
from route_companions import resolve_home, scan_companions  # noqa: E402,F401
from route_render import render  # noqa: E402,F401


# --------------------------------------------------------------------------- SURFACE

PAGE_RE = re.compile(r"<(html|table|form|button|input|select|main|div)\b>?", re.I)
CLI_PY = re.compile(r"^\s*(?:import|from)\s+(?:argparse|click|typer|fire)\b")
CLI_JS = re.compile(r"""(?:require\(\s*|from\s+)['"](?:commander|yargs|oclif|@oclif/[\w-]+)['"/]""")
CLI_GO = re.compile(r'"github\.com/(?:spf13/cobra|urfave/cli)[^"]*"')
CLI_RS = re.compile(r"^\s*(?:use\s+clap\b|clap\s*=)")
CLI_SCRIPTS = re.compile(r'console_scripts|^\s*\[project\.scripts\]|^\s*"bin"\s*:')
MAIN_RE = re.compile(r"""__name__\s*==\s*['"]__main__['"]""")
ARGV_RE = re.compile(r"sys\.argv")

_P = r"""(?P<p>[^'"`]*)"""
ROUTE_RES = [  # (regex, only-in-file-names, path-must-start-with-slash)
    (re.compile(r"""@\w+(?:\.\w+)*\.(?:get|post|put|delete|patch|route)\(\s*(?:rule\s*=\s*)?['"]""" + _P), None, True),
    (re.compile(r"""\brouter\.\w+\(\s*['"`]""" + _P), None, True),
    (re.compile(r"""\bapp\.(?:get|post|put|delete|patch)\(\s*['"`]""" + _P), None, True),
    (re.compile(r"""\bRoute::\w+\(\s*['"]""" + _P), None, False),
    (re.compile(r"""\b(?:re_)?path\(\s*['"]""" + _P), {"urls.py"}, False),
    (re.compile(r"""\bHandleFunc\(\s*"(?:[A-Z]+\s+)?""" + _P), None, True),
    (re.compile(r"""@(?:Get|Post|Put|Delete|Request)Mapping(?:\((?:value\s*=\s*)?"?)?""" + _P), None, False),
]
FORM_RES = [
    re.compile(r"""(?<![\w-])formaction\s*=\s*\\?['"]?(?P<p>/[^'" >\\]*)['"]?"""),
    re.compile(r"""(?<![\w-])action\s*=\s*\\?['"](?P<p>/[^'"\\]*)['"]?"""),
    re.compile(r"""\bfetch\(\s*["'`](?P<p>/[^"'`]*)["'`]?"""),
    re.compile(r"""\bhx-(?:post|get|put|delete|patch)\s*=\s*['"](?P<p>/[^'"]*)['"]?"""),
]
_PARAM = r"<[^>]*>|\{[^}]*\}|\$\{[^}]*\}|\{\{[^}]*\}\}|%\(\w+\)[sd]|%[sd]|:\w+"


def _route_regex(path: str) -> re.Pattern:
    """A route pattern as a regex: every param spelling (<id>, {id}, :id, *) matches one segment."""
    path = "/" + path.strip().lstrip("/")
    parts = re.split(f"({_PARAM}|\\*)", path.rstrip("/") or "/")
    body = "".join(".*" if p == "*" else "[^/]+" if re.fullmatch(_PARAM, p) else re.escape(p)
                   for p in parts if p)
    return re.compile(body + "/?")


def _target_text(path: str) -> str:
    path = re.split(r"[?#]", path)[0]
    return re.sub(_PARAM, "x", path)


def scan_surface(recs):
    pages = []
    for r in recs:
        if TEMPLATE_RE.search(r.name):
            pages.append(ev(r.rel, 1, "template file"))
        elif r.ext in STR_PAGE_EXTS and r.lines:
            for i, line in enumerate(r.lines, 1):
                m = PAGE_RE.search(line)
                if m and re.search(r"""["'`]""", line):
                    pages.append(ev(r.rel, i, m.group(0)))
                    break
    clis = []
    for r in recs:
        if r.lines is None:
            continue
        pat = {".py": CLI_PY, ".go": CLI_GO, ".rs": CLI_RS}.get(r.ext)
        if r.ext in (".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx"):
            pat = CLI_JS
        manifest = r.name in ("pyproject.toml", "setup.py", "setup.cfg", "package.json")
        hit = None
        for i, line in enumerate(r.lines, 1):
            m = (pat and pat.search(line)) or (manifest and CLI_SCRIPTS.search(line))
            if m:
                hit = ev(r.rel, i, m.group(0).strip())
                break
        if not hit and r.ext == ".py" and any(MAIN_RE.search(x) for x in r.lines):
            for i, line in enumerate(r.lines, 1):
                if ARGV_RE.search(line):
                    hit = ev(r.rel, i, "sys.argv")
                    break
        if hit:
            clis.append(hit)
    routes, route_paths = [], []
    for r in recs:
        if r.lines is None or r.ext not in SRC_EXTS:
            continue
        for i, line in enumerate(r.lines, 1):
            for rx, only, slash in ROUTE_RES:
                if only and r.name not in only:
                    continue
                m = rx.search(line)
                if m and (not slash or m.group("p").startswith("/")):
                    routes.append(ev(r.rel, i, m.group(0).strip()))
                    route_paths.append(m.group("p"))
                    break
    regexes = [_route_regex(p) for p in route_paths]
    targets, unresolved = [], []
    for r in recs:
        if r.lines is None or not (r.ext in SRC_EXTS or TEMPLATE_RE.search(r.name)):
            continue
        for i, line in enumerate(r.lines, 1):
            for rx in FORM_RES:
                for m in rx.finditer(line):
                    if m.group("p").startswith("//"):
                        continue
                    e = ev(r.rel, i, m.group(0).strip())
                    targets.append(e)
                    if not any(g.fullmatch(_target_text(m.group("p"))) for g in regexes):
                        unresolved.append(e)
    return pages, clis, routes, route_paths, targets, unresolved


def scan_server(recs):
    out = []
    for r in recs:
        if r.name in ("manage.py", "artisan", "Procfile"):
            out.append(ev(r.rel, 1, r.name))
        if r.lines is None:
            continue
        if r.name == "package.json":
            try:
                scripts = json.loads("\n".join(r.lines)).get("scripts", {})
            except (ValueError, AttributeError):
                scripts = {}
            for key in ("dev", "start"):
                if key in scripts:
                    ln = next((i for i, x in enumerate(r.lines, 1) if f'"{key}"' in x), 1)
                    out.append(ev(r.rel, ln, f"scripts.{key}"))
        elif re.match(r"docker-compose.*\.ya?ml$", r.name):
            out.extend(_first(re.compile(r"^\s*ports:"), [r]))
        elif r.name == "Makefile" or r.name.upper().startswith("README"):
            out.extend(_first(re.compile(r"\b(?:uvicorn|flask run|php -S)\b"), [r]))
    return out


# --------------------------------------------------------------------------- STATE

STATE_WORD = re.compile(r"\b(?:status|state|mode|step|phase)\b", re.I)
_ITEM = r"""['"][a-z][a-z0-9_]*['"]"""
QLIST = re.compile(rf"(?:{_ITEM}\s*,\s*){{2,}}{_ITEM}|(?:{_ITEM}\s*\|\s*){{2,}}{_ITEM}")
CLIST = re.compile(r"(?:--|#|//)\s*(?:\w+\s*[:=]\s*)?([a-z][a-z0-9_]*(?:\s*[,|]\s*[a-z][a-z0-9_]*){2,})\s*$")


def scan_state(recs):
    """Enums of >= 3 lowercase identifiers with a status-ish word within 2 lines; renderer map."""
    enums, seen = [], set()
    for r in recs:
        if r.lines is None or not (r.ext in SRC_EXTS or r.ext == ".sql"):
            continue
        text = "\n".join(r.lines)
        if not STATE_WORD.search(text):
            continue
        starts, pos = [], 0
        for line in r.lines:
            starts.append(pos)
            pos += len(line) + 1

        def near(a, b, lines=r.lines):
            lo, hi = max(a - 2, 1), min(b + 2, len(lines))
            return any(STATE_WORD.search(lines[k - 1]) for k in range(lo, hi + 1))

        cands = []
        for m in QLIST.finditer(text):
            a = bisect.bisect_right(starts, m.start())
            b = bisect.bisect_right(starts, m.end() - 1)
            if near(a, b):
                cands.append((a, re.findall(r"[a-z][a-z0-9_]*", m.group(0))))
        for i, line in enumerate(r.lines, 1):
            m = CLIST.search(line)
            if m and near(i, i):
                cands.append((i, re.findall(r"[a-z][a-z0-9_]*", m.group(1))))
        for ln, vals in sorted(cands):
            key = frozenset(vals)
            if key not in seen:
                seen.add(key)
                enums.append({"at": f"{r.rel}:{ln}", "values": vals})
    renderers = None
    if enums:
        vals = enums[0]["values"]
        best = (0, None)
        for r in recs:
            if r.lines is None or r.ext not in SRC_EXTS:
                continue
            found = {}
            for i, line in enumerate(r.lines, 1):
                for v in vals:
                    if re.search(rf"""(?:['"]{v}['"]\s*(?::|=>)|\bcase\s+['"]{v}['"])""", line):
                        found.setdefault(v, i)
            if len(found) > best[0]:
                best = (len(found), (r.rel, min(found.values()), max(found.values())))
        at = None
        if best[1]:
            at = f"{best[1][0]}:{best[1][1]}" + (f"-{best[1][2]}" if best[1][2] != best[1][1] else "")
        renderers = {"k": best[0], "n": len(vals), "at": at}
    return enums, renderers


# --------------------------------------------------------------------------- GRAPH / DESIGN

PY_IMPORT = re.compile(r"^\s*(?:from\s+([A-Za-z_]\w*)[\w.]*\s+import\b|import\s+([A-Za-z_]\w*))")
JS_REL = re.compile(r"""(?:from|require\(|import\()\s*['"](\.{1,2}/[^'"]*)['"]""")


def top_of(rel: str):
    return rel.split("/")[0] if "/" in rel else None


def scan_graph(recs):
    src = [r for r in recs if r.ext in SRC_EXTS]
    lines = sum(len(r.lines or []) for r in src)
    # A top-level dir is a "package" if code lives below it. `src/` layouts collapse into one
    # package — a known blind spot, which only makes cross-imports under-count (a lead, not a verdict).
    pkgs = sorted({top_of(r.rel) for r in src if top_of(r.rel)
                   and top_of(r.rel).lower() not in TEST_DIRS and not top_of(r.rel).startswith(".")})
    edges = {}
    for r in src:
        s = top_of(r.rel)
        if s not in pkgs or r.lines is None or r.ext not in (".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx"):
            continue
        for i, line in enumerate(r.lines, 1):
            t = None
            if r.ext == ".py":
                m = PY_IMPORT.match(line)
                t = m and (m.group(1) or m.group(2))
            else:
                m = JS_REL.search(line)
                if m:
                    t = os.path.normpath(os.path.join(os.path.dirname(r.rel), m.group(1))).replace("\\", "/").split("/")[0]
            if t in pkgs and t != s:
                edges.setdefault((s, t), (r.rel, i))
    # Mutual pairs only: a one-way dependency is layering, a two-way one is the coupling that
    # makes grep-level questions expensive (code-graph-tools.md §1).
    mutual = sorted({tuple(sorted(e)) for e in edges if (e[1], e[0]) in edges})
    held = int(len(src) > FILES_THRESHOLD or lines > LINES_THRESHOLD) + \
        int(len(pkgs) >= PACKAGES_THRESHOLD and bool(mutual))
    return {"files": len(src), "lines": lines, "packages": pkgs, "cross": len(mutual),
            "cross_pairs": [f"{a}<->{b} {edges[(a, b)][0]}:{edges[(a, b)][1]}" for a, b in mutual],
            "held": held}, src


UI_DEPS = "react vue svelte angular @angular electron three qt pyqt pyqt5 pyqt6 pyside pyside2 pyside6 tkinter".split()
COMMERCE_PAY = "stripe braintree adyen paypal square newebpay ecpay linepay payuni mollie".split()
COMMERCE_FW = "woocommerce shopify sylius magento saleor medusa".split()
MEDICAL_DEPS = "pydicom hl7 fhir dcmtk".split()
AI_DEPS = "anthropic openai langchain llamaindex @ai-sdk ollama".split()

_NAME = re.compile(r"[A-Za-z0-9_.@/\-]+")
_QUOTED = re.compile(r"""['"]([^'"]+)['"]""")
_JSON_DEPS = ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies", "require", "require-dev")


def _dep_rows(r: Rec):
    """Yield (lineno, lowercase dependency name) from a manifest, structurally where possible so a
    description string in pyproject cannot masquerade as a dependency."""
    L = r.lines
    low = r.name.lower()
    if re.match(r"requirements.*\.txt$", low):
        for i, line in enumerate(L, 1):
            s = line.split("#")[0].strip()
            m = _NAME.match(s)
            if m and not s.startswith("-"):
                yield i, m.group(0).lower()
    elif low in ("package.json", "composer.json"):
        try:
            data = json.loads("\n".join(L))
        except ValueError:
            return
        for key in _JSON_DEPS:
            deps = data.get(key) if isinstance(data, dict) else None
            for dep in (deps if isinstance(deps, dict) else ()):
                ln = next((i for i, x in enumerate(L, 1) if f'"{dep}"' in x), 1)
                yield ln, dep.lower()
    elif low in ("pyproject.toml", "pipfile", "cargo.toml", "setup.py"):
        sec, arr = False, False
        for i, line in enumerate(L, 1):
            s = line.strip()
            if arr:
                for q in _QUOTED.findall(line):
                    m = _NAME.match(q)
                    if m:
                        yield i, m.group(0).lower()
                arr = "]" not in line
                continue
            h = re.match(r"\[+([^\]]+)\]+", s)
            if h:
                sec = bool(re.search(r"dependencies|packages", h.group(1)))
                continue
            a = re.match(r"""["']?(?:dependencies|install_requires|requires)["']?\s*[=:]\s*\[(.*)""", s) or \
                (sec and re.match(r"""[\w.@/\-"']+\s*=\s*\[(.*)""", s))
            if a:
                rest = a.group(1)
                for q in _QUOTED.findall(rest):
                    m = _NAME.match(q)
                    if m:
                        yield i, m.group(0).lower()
                arr = "]" not in rest
            elif sec:
                m = re.match(r"""["']?([A-Za-z0-9_.\-]+)["']?\s*=""", s)
                if m:
                    yield i, m.group(1).lower()
    elif low == "go.mod":
        for i, line in enumerate(L, 1):
            m = re.match(r"\s*(?:require\s+)?([\w.\-]+\.[\w.\-]+/[\w./\-]+)\s+v", line)
            if m:
                yield i, m.group(1).lower()
    elif low == "gemfile":
        for i, line in enumerate(L, 1):
            m = re.match(r"""\s*gem\s+['"]([^'"]+)""", line)
            if m:
                yield i, m.group(1).lower()
    elif low.endswith(".lock") or low in ("package-lock.json", "yarn.lock", "pnpm-lock.yaml", "go.sum"):
        for i, line in enumerate(L[:30000], 1):
            for t in _NAME.findall(line):
                yield i, t.lower()


def dep_hit(tok: str, wanted: str) -> bool:
    """Whole-word hit on a dependency name: `stripe-php` and `@stripe/js` hit `stripe`,
    `stripey` and `payment_terms` do not. `llama-index` hits `llamaindex` by joined pieces."""
    if wanted.startswith("@"):
        return tok.startswith(wanted)
    p = [x for x in re.split(r"[/@_.\-]", tok) if x]
    return any("".join(p[i:j]) == wanted for i in range(len(p)) for j in range(i + 1, min(len(p), i + 3) + 1))


def deps_of(recs):
    return [(r.rel, ln, name) for r in recs if r.lines is not None for ln, name in _dep_rows(r)]


def find_dep(deps, wanted):
    for rel, ln, name in deps:
        for w in wanted:
            if dep_hit(name, w):
                return ev(rel, ln, w)
    return None


# --------------------------------------------------------------------------- COMMERCE / MEDICAL / AI

SCHEMA_RES = [
    re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"\[]?(?:\w+\.)?(?:orders|carts|products|payments)\b", re.I),
    re.compile(r"^\s*class\s+(?:Order|Cart|Product|Payment)\b"),
    re.compile(r"^\s*model\s+(?:Order|Cart|Product|Payment)\s*\{"),
]
MIGRATION_RE = re.compile(r"(?:^|/)migrations?/")
MIGRATION_WORDS = {"order", "orders", "cart", "carts", "product", "products", "payment", "payments"}
MED_HEAD = re.compile(r"(?i:patient|clinical|dental)|IEC 62304|\bFDA\b|\bMDR\b")


def _find_schema(recs):
    for r in recs:
        if MIGRATION_RE.search(r.rel) and r.ext in (".py", ".sql", ".php", ".js", ".ts", ".rb") and \
                MIGRATION_WORDS & set(re.split(r"[_\-.]", os.path.splitext(r.name)[0].lower())):
            return ev(r.rel, 1, "migration " + r.name)
        if r.lines and (r.ext in SRC_EXTS or r.ext == ".sql"):
            for i, line in enumerate(r.lines, 1):
                for rx in SCHEMA_RES:
                    m = rx.search(line)
                    if m:
                        return ev(r.rel, i, m.group(0).strip())
    return None


def scan_commerce(recs, deps, route_paths, routes):
    route = next((e for e, p in zip(routes, route_paths) if re.match(r"/?(?:checkout|cart)\b", p)), None)
    return {"payment": find_dep(deps, COMMERCE_PAY), "schema": _find_schema(recs),
            "route": route, "framework": find_dep(deps, COMMERCE_FW)}


def scan_medical_ai(recs, deps, dirs, paths):
    med_head = None
    for r in recs:
        if r.lines and r.ext == ".md" and (r.rel.count("/") == 0 or r.rel.startswith("docs/")):
            for i, line in enumerate(r.lines, 1):
                if line.startswith("#") and MED_HEAD.search(line):
                    med_head = ev(r.rel, i, line.strip())
                    break
        if med_head:
            break
    ai_dir = next((d for d in sorted(dirs) if d.split("/")[-1] in ("prompts", "prompt")), None)
    ai_file = next((p for p in sorted(paths) if ".prompt" in p.split("/")[-1]), None)
    ai_path = ai_dir or ai_file
    return {"medical": find_dep(deps, MEDICAL_DEPS) or med_head, "ai_dep": find_dep(deps, AI_DEPS),
            "ai_path": ev(ai_path, 1, "prompt dir/file") if ai_path else None}


# --------------------------------------------------------------------------- BINDINGS

TEST_NAME = re.compile(r"^(test_.*\.py|.*_test\.py|.*\.(test|spec)\.[jt]sx?|.*Test\.php|.*_test\.go)$")
LINTER_NAMES = re.compile(
    r"^(\.eslintrc.*|eslint\.config\..*|\.flake8|ruff\.toml|\.ruff\.toml|\.pylintrc|\.prettierrc.*|"
    r"\.stylelintrc.*|phpcs\.xml.*|\.golangci.*|mypy\.ini)$")
LOCKFILES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "Pipfile.lock",
             "composer.lock", "Cargo.lock", "go.sum", "uv.lock", "bun.lockb"}
RUNNER_CFG = re.compile(r"^(pytest\.ini|pyproject\.toml|phpunit\.xml.*|jest\.config.*|vitest\.config.*)$")
CI_RE = re.compile(r"^(\.github/workflows/.+|\.gitlab-ci\.yml|azure-pipelines\.yml|Jenkinsfile|\.circleci/.+)$")
ENV_EXAMPLE = re.compile(r"^\.env\.(example|sample|template)$", re.I)
STYLE_IMPORTS = (("unittest", r"^\s*(?:import|from)\s+unittest"), ("pytest", r"^\s*(?:import|from)\s+pytest"),
                 ("vitest", r"['\"]vitest['\"]"), ("jest", r"\bjest\b|@jest"),
                 ("phpunit", r"PHPUnit"), ("go test", r'"testing"'))


def _base(p):
    return p.split("/")[-1]


def scan_bindings(recs, paths, dirs):
    tests = sorted(r.rel for r in recs if TEST_NAME.match(r.name))
    styles = set()
    for r in recs:
        if r.rel in tests and r.lines:
            blob = "\n".join(r.lines[:80])
            styles |= {label for label, rx in STYLE_IMPORTS if re.search(rx, blob, re.M)}
        if r.name == "pyproject.toml" and r.lines and any(x.startswith("[tool.pytest") for x in r.lines):
            styles.add("pytest")
    for p in paths:
        b = _base(p)
        if b == "pytest.ini":
            styles.add("pytest")
        elif b.startswith("vitest.config"):
            styles.add("vitest")
        elif b.startswith("jest.config"):
            styles.add("jest")
        elif b.startswith("phpunit.xml"):
            styles.add("phpunit")
    linters = sorted(p for p in paths if LINTER_NAMES.match(_base(p)))
    linters += [r.rel + " [tool.*]" for r in recs if r.name == "pyproject.toml" and r.lines
                and any(re.match(r"\[tool\.(ruff|black|flake8|mypy|pylint)", x) for x in r.lines)]
    lower = {p.lower(): p for p in paths}
    lowdirs = {d.lower(): d for d in dirs}

    def pick(names, dir_names=()):
        out = [lower[n.lower()] for n in names if n.lower() in lower]
        out += [lowdirs[d.lower()] + "/" for d in dir_names if d.lower() in lowdirs]
        return sorted(out)

    envs = [p for p in paths if _base(p).lower().startswith(".env")]   # NAME only, never opened
    return {
        "tests": tests, "test_styles": sorted(styles),
        "runner_config": sorted(p for p in paths if RUNNER_CFG.match(_base(p))),
        "ci": sorted(p for p in paths if CI_RE.match(p)),
        "lockfile": sorted(p for p in paths if _base(p) in LOCKFILES),
        "linter": sorted(linters),
        "env": sorted(p for p in envs if not ENV_EXAMPLE.match(_base(p))),
        "env_example": sorted(p for p in envs if ENV_EXAMPLE.match(_base(p))),
        "docs": pick(["docs/ARCHITECTURE.md"], ["docs/adr"]),
        "handoff": pick(["HANDOFF.md"], ["docs/handoff"]),
        "gap_register": pick(["GAP-REGISTER.md", "KNOWN_ISSUES.md"]),
        "contract": pick(["CLAUDE.md", "AGENTS.md", "CONTRIBUTING.md", "README.md"]),
    }


# --------------------------------------------------------------------------- assembling and rendering

def scan(root: str, home: Path | None = None) -> dict:
    t0 = time.perf_counter()
    recs, paths, dirs, skipped = walk(root)
    pages, clis, routes, route_paths, targets, unresolved = scan_surface(recs)
    enums, renderers = scan_state(recs)
    graph, src = scan_graph(recs)
    deps = deps_of(recs)
    gpath = Path(root) / "graphify-out" / "graph.json"
    if gpath.is_file():
        newest = max((r.mtime for r in src), default=0.0)
        graph_out = "stale" if gpath.stat().st_mtime < newest else "fresh"
    else:
        graph_out = "absent"
    graph.update({"graphify_out": graph_out, "graphify": bool(shutil.which("graphify")),
                  "cgc": bool(shutil.which("cgc"))})
    return {
        "version": VERSION, "root": root.replace("\\", "/").rstrip("/") or "/",
        "source_files": graph["files"], "source_lines": graph["lines"], "skipped": skipped,
        "recognised": bool(src) or bool(pages),
        "surface": {"pages": pages, "cli": clis, "routes": routes, "targets": targets,
                    "unresolved": unresolved, "server": scan_server(recs)},
        "state": {"enums": enums, "renderers": renderers},
        "graph": graph,
        "design": {"modules": len(graph["packages"]), "ui": find_dep(deps, UI_DEPS)},
        "commerce": scan_commerce(recs, deps, route_paths, routes),
        "medical_ai": scan_medical_ai(recs, deps, dirs, paths),
        "bindings": scan_bindings(recs, paths, dirs),
        "companions": scan_companions(home or resolve_home()),
        "elapsed": round(time.perf_counter() - t0, 3),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="cia step-0 project scan (leads, never verdicts)")
    ap.add_argument("root")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-timing", action="store_true", help="omit the elapsed-time field (deterministic output)")
    a = ap.parse_args(argv)
    if not os.path.isdir(a.root):
        print(f"route.py: not a directory: {a.root}", file=sys.stderr)
        return 2
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # the report uses · and → ; cp1252 consoles crash on them
    F = scan(a.root)
    if a.no_timing:
        F.pop("elapsed")
    if a.json:
        print(json.dumps(F, sort_keys=True, ensure_ascii=False))
    else:
        print("\n".join(render(F)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
