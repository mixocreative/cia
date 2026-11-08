#!/usr/bin/env python3
"""Design checks an AI can run: dependency rules, ADR hygiene, state-transition tables.

One job per subcommand. Stdlib only, so it runs with nothing installed (executor level E0 in
references/agent-deployment.md). The rules these check are described in references/design-tools.md.

  deps   <root> [--rules design-rules.json]  import cycles, layer and forbidden-import violations
  adr    <dir>                               ADR files carry the required fields; supersedes links resolve
  states <table.json>                        a transition table is total, reachable and has exits

Exit 0 = clean. Exit 1 = findings, each printed with its site. Exit 2 = bad input or bad config.
An exception without a reason and an owner is a config error: silence about a known breach is the finding.

Known limits, printed in every deps report rather than hidden:
  - path aliases (e.g. "@/features/x") are not resolved; they are counted as UNRESOLVED, not checked;
  - Python imports are resolved by dotted name only; dynamic imports are not seen.
"""
import ast
import fnmatch
import json
import re
import sys
from pathlib import Path

SKIP_DIRS = {".git", "node_modules", "dist", "build", "__pycache__", ".venv", "venv", "graphify-out"}
PY_EXT = {".py"}
JS_EXT = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"}
JS_IMPORT = re.compile(
    r"""(?:import\s+(?:[^'"()]*?\s+from\s+)?|export\s+[^'"]*?\s+from\s+|require\(\s*|import\(\s*)(['"])([^'"]+)\1"""
)
ADR_FIELD = re.compile(r"^\**(Status|Date|Context|Decision|Consequences)\**:\s*(.*)$", re.M)
ADR_STATUS = re.compile(r"^(proposed|accepted|superseded by (\d{4})|deprecated)\b")
ADR_NAME = re.compile(r"^(\d{4})-.+\.md$")
STATE_TABLE_KEYS = {"initial", "states", "events", "terminal", "transitions"}


class ConfigError(Exception):
    pass


# ---------- deps ----------

def strip_roots(parts, roots):
    for r in roots:
        rp = r.split("/")
        if parts[: len(rp)] == rp:
            return parts[len(rp):]
    return parts


def iter_sources(root: Path):
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix not in PY_EXT | JS_EXT:
            continue
        if any(part in SKIP_DIRS for part in p.relative_to(root).parts[:-1]):
            continue
        yield p


def module_id(root: Path, path: Path, roots) -> str:
    parts = list(path.relative_to(root).with_suffix("").parts)
    if path.suffix in PY_EXT:
        if parts and parts[-1] == "__init__":
            parts = parts[:-1]
        parts = strip_roots(parts, roots)
        return ".".join(parts)
    if parts and parts[-1] == "index":
        parts = parts[:-1]
    return "/".join(strip_roots(parts, roots))


def py_edges(path: Path, mid: str, known: set):
    """(resolved project module or None, lineno, spec) per import. None = external (stdlib, third party).

    `from pkg import sub` names the submodule pkg.sub when that module exists; resolving it to pkg alone
    loses the edge that a cycle between pkg.a and pkg.b is made of.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    pkg = mid.split(".") if path.name == "__init__.py" else mid.split(".")[:-1]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                yield resolve_py(a.name, known), node.lineno, a.name
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = pkg[: len(pkg) - (node.level - 1)] if node.level > 1 else pkg
                target = ".".join(base + ([node.module] if node.module else []))
            else:
                target = node.module or ""
            spec = "." * node.level + (node.module or "")
            for a in node.names:
                sub = f"{target}.{a.name}" if target else a.name
                hit = sub if sub in known else (resolve_py(target, known) if target else None)
                yield hit, node.lineno, spec


def js_edges(root: Path, path: Path, mid: str, roots, text: str):
    """(target id or None, lineno, spec) for every import in a JS/TS file. None = not resolvable here."""
    for m in JS_IMPORT.finditer(text):
        spec = m.group(2)
        lineno = text.count("\n", 0, m.start()) + 1
        if not spec.startswith("."):
            yield None, lineno, spec
            continue
        target = (path.parent / spec).resolve()
        try:
            rel = target.relative_to(root.resolve())
        except ValueError:
            yield None, lineno, spec
            continue
        yield (rel.as_posix(), lineno, spec)


def resolve_js(root: Path, target_rel: str, known: set, roots):
    """A relative JS specifier names a file with or without an extension, or a folder index."""
    base = root / target_rel
    for cand in [base, *(base.with_suffix(e) for e in JS_EXT), *(base / ("index" + e) for e in JS_EXT)]:
        if cand.is_file() and cand.suffix in JS_EXT:
            return module_id(root, cand, roots)
    return None


def resolve_py(name: str, known: set):
    parts = name.split(".")
    for k in range(len(parts), 0, -1):  # longest known prefix wins
        cand = ".".join(parts[:k])
        if cand in known:
            return cand
    return None


def load_rules(path: Path | None):
    if path is None:
        return {"source_roots": [], "layers": None, "forbidden": [], "exceptions": []}
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise ConfigError(f"cannot read rules {path}: {e}")
    for ex in cfg.get("exceptions", []):
        if not ex.get("reason") or not ex.get("owner"):
            raise ConfigError(f"exception {ex.get('from')} -> {ex.get('to')} needs a reason and an owner")
    for rule in cfg.get("forbidden", []):
        if not rule.get("reason"):
            raise ConfigError(f"forbidden rule {rule.get('from')} -> {rule.get('to')} needs a reason")
    return {
        "source_roots": cfg.get("source_roots", []),
        "layers": cfg.get("layers"),
        "forbidden": cfg.get("forbidden", []),
        "exceptions": cfg.get("exceptions", []),
    }


def find_cycles(graph: dict):
    """Tarjan's strongly connected components; a component with more than one node is a cycle."""
    index, low, on, stack, out, counter = {}, {}, set(), [], [], [0]

    def visit(v):
        index[v] = low[v] = counter[0]
        counter[0] += 1
        stack.append(v)
        on.add(v)
        for w in graph.get(v, ()):
            if w not in index:
                visit(w)
                low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = stack.pop()
                on.discard(w)
                comp.append(w)
                if w == v:
                    break
            if len(comp) > 1 or v in graph.get(v, ()):
                out.append(sorted(comp))

    for v in list(graph):
        if v not in index:
            visit(v)
    return out


def layer_of(mid: str, layers: list):
    head = mid.split("/")[0] if "/" in mid else mid.split(".")[0]
    return (layers.index(head), head) if head in layers else (None, None)


def check_layers(imp, tgt, layers_cfg, layers):
    ri, li = layer_of(imp, layers)
    rj, lj = layer_of(tgt, layers)
    if ri is None or rj is None:
        return None
    if rj < ri:
        return f"upward import: {li} may not import {lj}"
    if rj == ri and layers_cfg.get("same_layer_slices") == "forbidden":
        si = imp.split("/")[1] if "/" in imp else None
        st = tgt.split("/")[1] if "/" in tgt else None
        if si and st and si != st:
            return f"sideways import: slice {si} imports slice {st} in layer {li}"
    return None


def cmd_deps(root: Path, rules_path: Path | None) -> int:
    rules = load_rules(rules_path)
    roots = rules["source_roots"]
    files = list(iter_sources(root))
    ids = {p: module_id(root, p, roots) for p in files}
    known = set(ids.values())
    graph: dict[str, set] = {i: set() for i in known}
    sites: dict[tuple, str] = {}
    unresolved = 0
    edges = []
    for p in files:
        mid = ids[p]
        rel = p.relative_to(root).as_posix()
        if p.suffix in PY_EXT:
            text = p.read_text(encoding="utf-8")
            for tgt, lineno, _spec in py_edges(p, mid, known):
                if tgt is None or tgt == mid:  # external import, or a self-reference: not a project edge
                    continue
                edges.append((mid, tgt, f"{rel}:{lineno}"))
        else:
            text = p.read_text(encoding="utf-8")
            for target_rel, lineno, spec in js_edges(root, p, mid, roots, text):
                tgt = resolve_js(root, target_rel, known, roots) if target_rel else None
                if tgt is None:
                    unresolved += 1
                    continue
                if tgt != mid:
                    edges.append((mid, tgt, f"{rel}:{lineno}"))
    for a, b, site in edges:
        graph[a].add(b)
        sites.setdefault((a, b), site)

    findings = []
    for comp in find_cycles(graph):
        findings.append(f"CYCLE {' -> '.join(comp)}  (sites: {', '.join(sites[(a, b)] for a in comp for b in comp if (a, b) in sites)})")

    exceptions_hit = 0
    layers = rules["layers"]["order"] if rules["layers"] else None
    for a, b, site in edges:
        msgs = []
        if layers:
            v = check_layers(a, b, rules["layers"], layers)
            if v:
                msgs.append(v)
        for rule in rules["forbidden"]:
            if fnmatch.fnmatch(a, rule["from"]) and fnmatch.fnmatch(b, rule["to"]):
                msgs.append(f"forbidden: {rule['reason']}")
        if not msgs:
            continue
        excepted = any(fnmatch.fnmatch(a, ex["from"]) and fnmatch.fnmatch(b, ex["to"]) for ex in rules["exceptions"])
        if excepted:
            exceptions_hit += 1
            continue
        for m in msgs:
            findings.append(f"VIOLATION {m}: {a} imports {b}  ({site})")

    print(f"deps: {len(known)} modules, {len(edges)} internal edges, UNRESOLVED {unresolved} "
          f"(aliases and dynamic imports are not checked), cycles {sum(1 for f in findings if f.startswith('CYCLE'))}, "
          f"violations {sum(1 for f in findings if f.startswith('VIOLATION'))}, exceptions honoured {exceptions_hit}")
    for f in findings:
        print("  " + f)
    return 1 if findings else 0


# ---------- adr ----------

def cmd_adr(adr_dir: Path) -> int:
    if not adr_dir.is_dir():
        raise ConfigError(f"no such directory: {adr_dir}")
    files = sorted(p for p in adr_dir.glob("*.md") if p.name.lower() != "readme.md")
    findings, numbers, seen = [], {}, set()
    for p in files:
        m = ADR_NAME.match(p.name)
        if not m:
            findings.append(f"NAME {p.name}: not NNNN-title.md")
            continue
        num = m.group(1)
        if num in numbers:
            findings.append(f"DUPLICATE number {num}: {numbers[num]} and {p.name}")
        numbers[num] = p.name
        text = p.read_text(encoding="utf-8")
        fields = {k: v.strip() for k, v in ADR_FIELD.findall(text)}
        for need in ("Status", "Date", "Context", "Decision", "Consequences"):
            if not fields.get(need):
                findings.append(f"MISSING {need} in {p.name}")
        st = ADR_STATUS.match(fields.get("Status", "").lower())
        if fields.get("Status") and not st:
            findings.append(f"STATUS {p.name}: '{fields['Status']}' is not proposed / accepted / superseded by NNNN / deprecated")
        if st and st.group(2):
            seen.add((p.name, st.group(2)))
    for name, target in seen:
        if target not in numbers:
            findings.append(f"SUPERSEDES {name}: names ADR {target}, which does not exist")
    print(f"adr: {len(files)} records, findings {len(findings)}")
    for f in findings:
        print("  " + f)
    return 1 if findings else 0


# ---------- states ----------

def cmd_states(table_path: Path) -> int:
    try:
        t = json.loads(table_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise ConfigError(f"cannot read table {table_path}: {e}")
    if not STATE_TABLE_KEYS <= set(t):
        raise ConfigError(f"table needs keys {sorted(STATE_TABLE_KEYS)}")
    states, events, terminal = set(t["states"]), set(t["events"]), set(t["terminal"])
    if t["initial"] not in states or not terminal <= states:
        raise ConfigError("initial and terminal states must be declared states")
    trans = t["transitions"]
    findings = []
    for s in sorted(states):
        row = trans.get(s, {})
        for e in sorted(events):
            cell = row.get(e)
            if cell is None:
                findings.append(f"MISSING {s} x {e}: no transition and no explicit ignore")
            elif isinstance(cell, dict):
                if not cell.get("ignore"):
                    findings.append(f"IGNORE {s} x {e}: an ignore needs a reason")
            elif cell not in states:
                findings.append(f"TARGET {s} x {e} -> {cell}: not a declared state")
    reach, frontier = {t["initial"]}, [t["initial"]]
    while frontier:
        s = frontier.pop()
        for cell in trans.get(s, {}).values():
            tgt = cell if isinstance(cell, str) else None
            if tgt in states and tgt not in reach:
                reach.add(tgt)
                frontier.append(tgt)
    for s in sorted(states - reach):
        findings.append(f"UNREACHABLE {s}: no path from the initial state")
    for s in sorted(states - terminal):
        exits = [c for c in trans.get(s, {}).values() if isinstance(c, str) and c != s]
        if not exits:
            findings.append(f"EXITLESS {s}: a non-terminal state with no way out")
    print(f"states: {len(states)} states x {len(events)} events = {len(states) * len(events)} cells; findings {len(findings)}")
    for f in findings:
        print("  " + f)
    return 1 if findings else 0


# ---------- entry ----------

USAGE = __doc__.split("\n\n")[0] + "\n\n" + "\n".join(l for l in __doc__.splitlines() if l.startswith("  deps") or l.startswith("  adr") or l.startswith("  states"))


def main(argv) -> int:
    try:
        if len(argv) >= 2 and argv[0] == "deps":
            rules = None
            if "--rules" in argv:
                rules = Path(argv[argv.index("--rules") + 1])
            root = Path(argv[1])
            if not root.is_dir():
                raise ConfigError(f"no such directory: {root}")
            return cmd_deps(root, rules)
        if len(argv) == 2 and argv[0] == "adr":
            return cmd_adr(Path(argv[1]))
        if len(argv) == 2 and argv[0] == "states":
            return cmd_states(Path(argv[1]))
        print(USAGE)
        return 2
    except ConfigError as e:
        print(f"config error: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
