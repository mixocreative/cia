"""route.py's text report: turns the scan dict into the ROUTE block a run pastes at step 0.

Split from route.py on 2026-11-09. Pure: dict in, lines out, so the JSON and the text cannot disagree.
"""
from __future__ import annotations

from route_tree import UNKNOWN_TEXT, evs


def _list(items, none="none"):
    return ", ".join(items) if items else none


# code-graph-tools.md §1: six signals, any two bring a graph in. route.scan_graph measures the first two
# (size, mutual imports); the other four (roles/surfaces, blast-radius greps, design checks, delegation)
# need judgement. tests/tools/test_route.py reads all three numbers back from the doctrine.
SIGNALS_TOTAL, SIGNALS_SCANNED, SIGNALS_NEEDED = 6, 2, 2


def graph_route(G: dict) -> str:
    """§1 (is a graph needed) and §2 (which graph answers which question) applied to what the scan saw.

    The trap this replaces: the line once said "graphify, else cgc", the reverse of §2, which puts
    CodeGraphContext first for code relationships and graphify first for architecture. Neither the
    scan nor this line can tell a working cgc from a broken one (a locked KuzuDB store fails the
    same way as a missing one), so it says "probe first" instead of claiming cgc works.
    """
    left = SIGNALS_TOTAL - SIGNALS_SCANNED
    need = SIGNALS_NEEDED - G["held"]
    if need <= 0:
        verdict = "code graph"
    elif need == 1:
        verdict = f"code graph if one of the {left} judged signals holds, else grep"
    else:
        verdict = f"grep unless {need} of the {left} judged signals hold"
    if G["cgc"]:
        code = "cgc (probe `cgc --help` first; failed probe, locked or stale store → graphify explain/path)"
    elif G["graphify"]:
        code = "graphify explain/path (cgc not on PATH)"
    else:
        code = "grep (no graph tool on PATH)"
    if not G["graphify"]:
        arch = "grep (graphify not on PATH)"
    else:
        arch = {"fresh": "graphify", "stale": "graphify after `graphify update .` (graphify-out/ is stale)",
                "absent": "graphify after `graphify update .` (graphify-out/ absent)"}[G["graphify_out"]]
    return (f"signals held {G['held']} of {SIGNALS_SCANNED} scanned, {left} judged by hand "
            f"(code-graph-tools.md §1: any {SIGNALS_NEEDED} of {SIGNALS_TOTAL}) → {verdict} · "
            f"if a graph (§2, one graph per question): code relationships → {code}; architecture → {arch}")


def render(F: dict) -> list[str]:
    """Text report. `elapsed` absent from F (--no-timing) makes the output byte-deterministic."""
    S, G, B = F["surface"], F["graph"], F["bindings"]
    out = []
    t = f"{F['elapsed']:.1f} s" if "elapsed" in F else "timing off"
    out.append(f"ROUTE tools/route.py {F['version']} · root {F['root']} · {F['source_files']} source files / "
               f"{F['source_lines']} lines · {t} · skipped dirs: {_list(F['skipped'])}"
               + ("" if F["recognised"] else " · stack not recognised"))
    if not F["recognised"]:
        out.append("SURFACE stack not recognised (no source file with a known extension, no template)  "
                   "→ load surface-map.md §3 and ask the owner what the system is")
    else:
        form = f"http routes={len(S['routes'])}" + (f" ({evs(S['routes'], 1)})" if S["routes"] else "")
        form += f", form targets={len(S['targets'])}"
        if S["unresolved"]:
            form += f" ({evs(S['unresolved'], 1)} — no handler in tree)"
        elif S["targets"]:
            form += f" ({evs(S['targets'], 1)} — handler found)"
        out.append("SURFACE " + " · ".join([
            f"page={len(S['pages'])}" + (f" ({evs(S['pages'])})" if S["pages"] else ""),
            f"cli={len(S['cli'])}" + (f" ({evs(S['cli'])})" if S["cli"] else ""),
            form, "server=" + (evs(S["server"], 1) if S["server"] else "none")]))
        walk_note = ("rendering walk possible" if S["server"]
                     else "no rendering walk: no server" if (S["pages"] or S["cli"] or S["routes"] or S["targets"])
                     else "no surface found")
        out.append(f"  → load surface-map.md §3, journey-map.md §2; browser-walks.md §12 by CLI/API observers ({walk_note})")
    st = F["state"]
    if st["enums"]:
        e, rd = st["enums"][0], st["renderers"]
        vals = "|".join(e["values"][:6]) + ("|…" if len(e["values"]) > 6 else "")
        rtxt = f"renderers for {rd['k']} of {rd['n']}" + (f" ({rd['at']})" if rd["at"] else " (none found)")
        out.append(f"STATE enums={len(st['enums'])} ({e['at']} {vals}) · {rtxt}  → design-tools.md §4; S16/S22 lead, not a finding")
    else:
        out.append("STATE enums=0 (no list of >= 3 lowercase identifiers within 2 lines of status|state|mode|step|phase, "
                   "no CHECK (status IN (…)))  → design-tools.md §4 not triggered")
    out.append(f"GRAPH files={G['files']} lines={G['lines']} packages={len(G['packages'])} cross-imports={G['cross']}"
               + (f" ({G['cross_pairs'][0]})" if G["cross_pairs"] else "")
               + " · " + graph_route(G)
               + f" · graphify-out/: {G['graphify_out']} · graphify: {'PATH' if G['graphify'] else 'not on PATH'}"
               + f" · cgc: {'PATH' if G['cgc'] else 'not on PATH'}")
    D = F["design"]
    out.append(f"DESIGN top-level modules={D['modules']} · ui framework=" + (evs([D["ui"]], 1) if D["ui"] else "none")
               + ("  → design-tools.md §1–§3" if D["modules"] >= 2 or D["ui"]
                  else "  → design-tools.md not triggered (needs modules >= 2 or a UI dependency)"))
    C = F["commerce"]
    crit = [("payment dep", "payment"), ("orders/cart/products schema", "schema"),
            ("/checkout|/cart route", "route"), ("commerce framework", "framework")]
    hits = [(i + 1, n, C[k]) for i, (n, k) in enumerate(crit) if C[k]]
    if hits:
        out.append(f"COMMERCE criteria {len(hits)} of 4 ("
                   + " · ".join(f"{i} {n}: {evs([e], 1)}" for i, n, e in hits)
                   + ")  → suggest /ecommerce-cia (SKILL §0.3); cia still runs in full")
    else:
        out.append("COMMERCE none (criteria 1–4 of SKILL §0.3: " + " · ".join(f"{n} no" for n, _ in crit) + ")")
    M = F["medical_ai"]
    med = (f"MEDICAL {evs([M['medical']], 1)}  → companion-skills.md meddev row" if M["medical"] else
           "MEDICAL none (deps pydicom|hl7|fhir|dcmtk: no · headings patient|clinical|dental|IEC 62304|FDA|MDR: no)")
    ai_ev = M["ai_dep"] or M["ai_path"]
    out.append(f"{med} · " + (f"AI on (§0.10: {evs([ai_ev], 1)})" if ai_ev
                              else "AI none (§0.10 off: no LLM dep, no prompt dir)"))
    tests = B["tests"]
    ttxt = (f"tests={len(tests)} file{'s' if len(tests) != 1 else ''} ({tests[0]}, {_list(B['test_styles'], 'style unknown')})"
            if tests else "tests=none")
    out.append("BINDINGS " + " · ".join([
        ttxt, f"runner config={_list(B['runner_config'])}", f"ci={_list(B['ci'])}",
        f"lockfile={_list(B['lockfile'])}", f"linter config={_list(B['linter'])}",
        f".env={'present' if B['env'] else 'none'} .env.example={'present' if B['env_example'] else 'none'}",
        f"docs: {_list(B['docs'])}", f"handoff={_list(B['handoff'])}",
        f"gap-register={_list(B['gap_register'])}", f"contract files={_list(B['contract'])}"])
        + "  → §0.5 resolves the commands from these")
    K = F["companions"]
    out.append(f"COMPANIONS installed: {_list(K['installed'])} · other skills {K['other']} · CLIs: {_list(K['clis'])}"
               f" · missing: {_list(K['missing'])}" + ("" if K["table_read"] else " (table unreadable)")
               + "  → companion-skills.md §3")
    out.append("UNKNOWN " + UNKNOWN_TEXT)
    return out
