# Code-graph tools — when a project has become complicated enough to need one, and which one

> Job of this file: decide **when** the AI should bring in a code graph, **which** graph to use, and what to check before a graph tool installs anything or edits configuration. The graph answers "what touches what" cheaply; `test-tools.md` §1 says how to read it, `agent-deployment.md` says where it sits on the executor ladder (rung 1).
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

## 2. Which graph

| Situation | Use |
|---|---|
| Two or more complexity signals hold (§1) | **CodeGraphContext** — from now on the AI's code graph for this project, after the checks in §3. It serves the graph over MCP, so later sessions query it instead of re-exploring the same code, and `cgc watch .` keeps it current while code changes. If the repo also has `graphify-out/`, stop refreshing it once CodeGraphContext is in place: two graphs double the stale-index risk |
| Below the thresholds, or a one-off audit | graphify (`graphify update .`) or grep — nothing is installed and no configuration is edited |
| CodeGraphContext cannot run here (no embedded database on this platform, Neo4j not available, probe fails) | graphify, and the report says why |

**Never keep two graph tools indexing the same repository.** Pick one per repository and say which in the handoff.

**Then measure, and keep it only if it pays.** The aim is less repeated exploration, fewer regressions and fewer total tokens, not more tools. After the first few real tasks with CodeGraphContext, compare the tokens spent on exploration against a comparable task before it, with the same findings, and write both numbers in the handoff. If CodeGraphContext did not reduce them, tell the owner and fall back to graphify.

---

## 3. What CodeGraphContext changes on the machine — check before running it

CodeGraphContext is a Python CLI plus a database plus an MCP server. Indexing reads the code; three other steps change things outside the project's source:

- **installing it** (a Python package) — user-scope, rung 3 of the self-service ladder (`SKILL.md` §0.8): `pipx` or a user `pip install`, never `sudo` or a system package manager;
- **`cgc mcp setup`** — a wizard that edits the AI client's configuration (Claude, VS Code, Cursor, Windsurf, per its README). That is persistent configuration: **ask the owner first** and say which file it will edit;
- **the database** — an embedded database by default per its README; Neo4j is optional, and one mirror says it is needed on Windows without WSL. A Neo4j server is a system-level install, which is a rung-5 owner decision. This machine is Windows: probe whether the embedded database works before planning on it.

Before running it:

1. **Probe.** `cgc --help` (or `codegraphcontext --help` in some copies) must answer. Record the version in the report's rung line. If it does not answer after a user-scope install, fall back to graphify and say so.
2. **Ask the owner before `cgc mcp setup`** and before any Neo4j install. Name the config file the wizard will change.
3. **Find the index location and gitignore it.** The sources do not agree on where the embedded store lives; read it from the installed version's output. A committed index is a stale index waiting to be trusted.
4. **Confirm locality.** The tool indexes local code into a local database per its README. Check that against the installed version before a confidential project is indexed.
5. **Watch the watcher.** `cgc watch .` is a background process. If it dies, the graph goes stale silently and every later answer is about old code — the dead-watchdog defect of S20 applied to the graph. Before trusting an answer, check the graph is newer than the last code change; if the watcher is not running, re-index.

---

## 4. How the AI uses it

- **Ask the graph before reading wide.** The graph's answer (callers, callees, the path from an entry point to a write) replaces a multi-file read. Grade it as `test-tools.md` §1 says: a graph edge is a lead until the line is read.
- **Feed it to the matrices.** A capability's callers feed `surface-map.md` (orphans, dead controls); a path feeds the blast radius in `test-tools.md` §3; components and arrows feed the C4 check in `design-tools.md` §1.
- **Keep it fresh.** A graph older than the last code change is stale. The closure gate G8 in `build-orchestration.md` requires a refresh before the session finishes: `cgc index .` (or a running watcher) for CodeGraphContext, `graphify update .` for graphify.
- **Do not let the graph grade.** It maps the code; it does not prove a behaviour (`evidence.md` §E1).

---

## 5. Report line

```
GRAPH — tool <name> <version> (probed); trigger signals held <list>; index path <path>, fresh as of <commit>; watcher <running|not used|dead>; queries <n>, truncated <t>; edges used E; stale-check: <pass|fail>.
```

---

## 6. Sources

- CodeGraphContext README (mirror of `Shashankss1205/CodeGraphContext`): https://glama.ai/mcp/servers/@Shashankss1205/CodeGraphContext/blob/5cf5aa8eaf2d6bd6f407dca9dfa7203b157d30ba/README.md
- Setup workflows: https://glama.ai/mcp/servers/@Shashankss1205/CodeGraphContext/blob/381af176fb34f46affe9c4771d6f7138754bfa72/docs/docs/setup_workflows.md
- Listing and config: https://mcp.so/server/codegraphcontext
- The original repository appears to be `Shashankss1205/CodeGraphContext`; it was not verified directly. Where the copies disagree, the installed version's own documentation wins.
