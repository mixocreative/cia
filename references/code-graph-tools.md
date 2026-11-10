# Code-graph tools — when a project has become complicated enough to need one, and which one

> Job of this file: decide **when** the AI should bring in a code graph, **which** graph answers which question, and what to check before a graph tool installs anything or edits configuration. The graph answers "what touches what" cheaply; `test-tools.md` §1 says how to read it, `agent-deployment.md` says where it sits on the executor ladder (level X1).
>
> Two tools are named. **graphify** is already in use on this machine (`graphify-out/`, `graphify update .`). **CodeGraphContext** (`cgc`, an MCP server and CLI that indexes local code into a graph database) is the one the owner asked to add. It is not installed here and has not been run. Its README exists in several mirrors and forks whose versions and commands differ (`cgc start` versus `cgc mcp start`, Neo4j versus an embedded database), so this file names only what they agree on and says to check the installed version's own `--help` before relying on any detail. Sources are in §6.

---

## 1. When a project is complicated enough

Do not bring a graph in for a small project; the cost of building and reading it is not paid back. Bring one in when **any two** of these hold, and say which ones held in the report:

| Signal | Default threshold (owner-tunable) |
|---|---|
| Source size | more than about 200 source files, or about 50,000 lines |
| Modules that import each other | three or more top-level packages with cross-imports |
| Surfaces and roles | two or more roles, or more than one surface for the same capability (`surface-map.md`) |
| Blast-radius questions | a change needs more than two greps to know its callers, or the same question is asked on three or more changes |
| Design checks in play | the dependency rules or C4 map of `design-tools.md` are being enforced |
| Delegation | structural questions are being sent to subagents more than once in a phase (`agent-deployment.md` §3) |

Below the thresholds, `grep` and the test runner are enough. Say so in the report rather than building a graph for its own sake.

---

## 2. Two graphs, two jobs

Below the thresholds of §1, graphify alone (or grep). Once CodeGraphContext is in place (§1 triggers, §3 checks), both serve the same repository, **each for one kind of question**:

| Question | Ask first | Ask the other only when |
|---|---|---|
| **Code relationships** — who calls X, what X calls, imports, the call chain from an entry point to a write, what a change touches | **CodeGraphContext** | it cannot answer: a language it does not parse, a stale index, a failed probe. Then graphify `explain` / `path` |
| **Architectural context** — which modules cluster together, which docs and sections describe a component, how the system divides, the overview a new session needs | **graphify** (`graphify-out/GRAPH_REPORT.md`, `graphify query`) | the answer names a component whose code relationships matter. Then CodeGraphContext, for those relationships only |

### 2.1 One question, one graph

Do not ask both graphs the same question to compare them: that doubles the tokens and leaves two answers to reconcile. Ask the second graph only when the first returned nothing usable, returned `TRUNCATED` and narrowing did not help, or is stale. Record each fallback and its reason in the report line (§5).

### 2.2 Separate storage

- graphify writes only `graphify-out/` at the project root.
- CodeGraphContext keeps its own database (its embedded store, or Neo4j) in its own location.
- Never point either tool at the other's directory or database, never share one Neo4j database between them, and gitignore both index locations.
- Record both index paths in the handoff, so the next session knows which store belongs to which tool.

### 2.3 One source of truth: the code and its architecture documents

- The repository's code and its architecture documentation (ADRs, the C4 map, design docs, README maps) are **authoritative**. Both graphs are derived indexes of them.
- A graph that disagrees with the code is **stale**: the code wins, and the graph is re-indexed.
- A graph that disagrees with an architecture document is a drift question between the document and the code (`test-tools.md` §2). It is settled by reading both, never by trusting the graph.
- No graph answer enters a report as a fact until the cited line has been read (`evidence.md` §E1).

### 2.4 Both stay; measurement tunes the routing

Both graphs help, so neither is retired for one bad result. What the measurement decides is **which questions go to which graph**:

- after the first few real tasks, compare the tokens each graph spent per question type, with the same findings, and write the numbers in the handoff;
- if a question type is answered more cheaply by the other graph (say graphify answers a call-chain question well enough on this codebase, or CodeGraphContext gives a better module overview), move that question type in the §2 table and say so in the handoff;
- only if a graph cannot run at all (failed probe, no usable database on this platform) does the other answer both kinds of question, and the report says why.


### 2.5 Other ways each can help

The table in §2 says where to ask **first**; it is not a fence. Either graph may help in other ways, as long as §2.1–§2.3 still hold (one graph per question, separate stores, the code authoritative). Uses worth reaching for:

| Graph | Other help | Feeds |
|---|---|---|
| graphify | its markdown nodes show which doc sections describe a component, so a code change can be traced to the docs it may have made stale | the cascade check, `build-orchestration.md` §5 |
| graphify | its communities give a first draft of the C4 component level, to be checked against the code | `design-tools.md` §1 |
| graphify | `graphify diagnose multigraph` before a count from the graph is reported | `test-tools.md` §1 |
| CodeGraphContext | callers and call chains for every capability, so orphans show up as nodes with no inbound edge | `surface-map.md` SC1 (orphans), S13 |
| CodeGraphContext | dead-code and complexity queries, **if the installed version offers them** (check its `--help` or MCP tool list; do not assume) | orphan candidates (S13); size-debt cut targets (`build-orchestration.md` §4) |
| CodeGraphContext | the running watcher keeps the graph current during a long build session | the freshness check, §4 and CG8 |

Each of these is a lead, not a verdict: the cited line is read before it enters a report (§2.3).

---

## 3. What CodeGraphContext changes on the machine — check before running it

CodeGraphContext is a Python CLI plus a database plus an MCP server. Indexing reads the code; three other steps change things outside the project's source:

- **installing it** (a Python package) — user-scope, rung 3 of the self-service ladder (`SKILL.md` §0.8): `pipx` or a user `pip install`, never `sudo` or a system package manager;
- **`cgc mcp setup`** — a wizard that edits the AI client's configuration (Claude, VS Code, Cursor, Windsurf, per its README). That is persistent configuration: **ask the owner first** and say which file it will edit;
- **the database** — an embedded database by default per its README; Neo4j is optional, and one mirror says it is needed on Windows without WSL. A Neo4j server is a system-level install, which is a rung-5 owner decision. This machine is Windows: probe whether the embedded database works before planning on it.

Before running it:

1. **Probe.** `cgc --help` (or `codegraphcontext --help` in some copies) must answer. Verified with 0.6.13 on 2026-11-09: a user-scope pip install puts `cgc.exe` in the user Scripts folder, which may not be on PATH (call it by full path); `cgc --db kuzudb --path <store-dir> index <root>` builds an embedded KuzuDB store with no server and no config change; `cgc analyze callers|calls|chain|dead-code|complexity` answers the code-relationship questions (it found the fixture's orphan `with_backoff` with zero callers); it keeps its own config and logs in `~/.codegraphcontext/`. Record the version in the EXECUTORS line (`agent-deployment.md` §8). If it does not answer after a user-scope install, fall back to graphify and say so.
2. **Ask the owner before `cgc mcp setup`** and before any Neo4j install. Name the config file the wizard will change.
3. **Find the index location, keep it apart from graphify's, and gitignore it.** The sources do not agree on where the embedded store lives; read it from the installed version's output, and confirm it is not inside `graphify-out/` and does not share a database with anything else (§2.2). A committed index is a stale index waiting to be trusted.
4. **Confirm locality.** The tool indexes local code into a local database per its README. Check that against the installed version before a confidential project is indexed.
5. **Watch the watcher.** `cgc watch .` is a background process. If it dies, the graph goes stale silently and every later answer is about old code — the dead-watchdog defect of S20 applied to the graph. Before trusting an answer, check the graph is newer than the last code change; if the watcher is not running, re-index.
6. **One writer per store.** The embedded store takes an exclusive lock. A second process that opens it (a second AI session whose MCP entry names the same store, an index run while the server is up) fails to start, and the client reports only that the server closed the connection. Keep one store per project; a user-wide MCP entry that pins one project's store makes every other session fail. When the server will not start, check whether another process holds the store before reinstalling anything. On Windows the held file cannot even be copied, so a fallback copy has to be taken while the store is free. A server that will not start is a failed probe: graphify answers both kinds of question and the report says why (§2.4).

---

## 4. How the AI uses it

- **Ask the right graph before reading wide** (§2): CodeGraphContext for code relationships, graphify for architectural context. The answer replaces a multi-file read. Grade it as `test-tools.md` §1 says: a graph edge is a lead until the line is read.
- **Feed it to the matrices.** A capability's callers feed `surface-map.md` (orphans, dead controls); a path feeds the blast radius in `test-tools.md` §3; components and arrows feed the C4 check in `design-tools.md` §1.
- **Keep it fresh.** A graph older than the last code change is stale. The closure gate CG8 in `build-orchestration.md` requires a refresh before the session finishes: `cgc index .` (or a running watcher) for CodeGraphContext, `graphify update .` for graphify. Refresh each one that is in use; a fresh graph next to a stale one is still a stale answer when the stale one is asked.
- **Do not let the graph grade or override.** It maps the code; it does not prove a behaviour, and it never outranks the code or the architecture documents (§2.3).

---

## 5. Report line

```
GRAPH — code relationships via <cgc|graphify> <version> (n queries); architecture via graphify (m queries); second-graph fallbacks f (reasons);
        trigger signals held <list>; index paths <cgc path> | graphify-out/ (separate: yes|no); fresh as of <commit> each; watcher <running|not used|dead>;
        truncated t; graph-vs-code disagreements d (code won, re-indexed); stale-check: <pass|fail>.
```

---

## 6. Sources

- CodeGraphContext README (mirror of `Shashankss1205/CodeGraphContext`): https://glama.ai/mcp/servers/@Shashankss1205/CodeGraphContext/blob/5cf5aa8eaf2d6bd6f407dca9dfa7203b157d30ba/README.md
- Setup workflows: https://glama.ai/mcp/servers/@Shashankss1205/CodeGraphContext/blob/381af176fb34f46affe9c4771d6f7138754bfa72/docs/docs/setup_workflows.md
- Listing and config: https://mcp.so/server/codegraphcontext
- The original repository appears to be `Shashankss1205/CodeGraphContext`; it was not verified directly. Where the copies disagree, the installed version's own documentation wins.

---

**Reading receipt: _two graphs, two stores, one truth_.** Quote this phrase on the report's receipts line (Step 6) to show this file was read rather than inferred from the skill's index.
It appears nowhere else.
