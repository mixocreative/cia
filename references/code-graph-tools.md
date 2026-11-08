# Code-graph tools — when a project has become complicated enough to need one, and which one

> Job of this file: decide **when** the AI should bring in a code graph, **which** graph to use, and what to check before letting a graph tool write into the project. The graph answers "what touches what" cheaply; `test-tools.md` §1 says how to read it, `agent-deployment.md` says where it sits on the executor ladder (rung 1).
>
> Two tools are named. **graphify** is already in use on this machine (`graphify-out/`, `graphify update .`). **GitNexus** is the one the owner asked to add. Its public description is at https://cdn.jsdelivr.net/gh/abhigyanpatwari/GitNexus@main/README.md and its overview at https://aiagentstore.ai/ai-agent/gitnexus. Those sources disagree on details (MCP tool count, storage format), so this file names only what they agree on, and says to check the installed version's own help before relying on any detail.

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
| The project already has `graphify-out/` | keep graphify; a second graph in the same repo doubles the stale-index risk |
| No graph yet, one repo, Claude Code is the agent | GitNexus is the stronger fit: it serves the graph over MCP and adds hooks that enrich search calls with graph context |
| Several repos that must be queried together | GitNexus; its README describes a global registry for multi-repo use |
| Graph wanted only for a one-off audit | graphify (`graphify update .`) — nothing is installed into the project |

**Never run two graph tools that both write indexes or agent files into the same repository.** Pick one per repository and say which in the handoff.

---

## 3. What GitNexus does to a project — check before running it

GitNexus is an installer as much as an indexer. Its `analyze` step, per its README, indexes the code into a local store, installs agent skills, registers Claude Code hooks, and creates `AGENTS.md` and `CLAUDE.md` context files. `setup` writes the MCP configuration. Each of those is a change to the project or to the user's configuration.

Before running it:

1. **Read the existing `CLAUDE.md` and `AGENTS.md`.** The project's contract files are read first in §0.5 of the skill. If `analyze` would create or overwrite them, stop: merge by hand or ask the owner. Overwriting a project's contract file is the rung-5 owner decision in `SKILL.md` §0.8.
2. **Ask the owner before any install that writes hooks or config** (`settings.json`, MCP config, project `CLAUDE.md`). These are persistent configuration; the owner decides them, the audit does not.
3. **Add the index directory to `.gitignore`** (GitNexus keeps its index in `.gitnexus/` per its README; check the installed version's output for the exact path). A committed index is a stale index waiting to be trusted.
4. **Probe before relying on it.** Run the tool's own help or version command; if it answers, record the version in the report's rung line. If it does not, fall back to graphify or to `grep` and say that in the report.
5. **Confirm locality.** The README says the index is built and queried locally. Check that claim against the installed version before the project's code is indexed; a project under a confidentiality rule is not indexed by a tool whose network behaviour is unverified.

---

## 4. How the AI uses it

- **Ask the graph before reading wide.** The graph's answer (callers, callees, the path from an entry point to a write) replaces a multi-file read. The answer is `[EXTRACTED]` or `INFERRED` and graded as `test-tools.md` §1 says.
- **Feed it to the matrices.** A capability's callers feed `surface-map.md` (orphans, dead controls); a path feeds the blast radius in `test-tools.md` §3; components and arrows feed the C4 check in `design-tools.md` §1.
- **Keep it fresh.** A graph older than the last code change is stale. The closure gate G8 in `build-orchestration.md` requires a refresh before the session finishes.
- **Do not let the graph grade.** It maps the code; it does not prove a behaviour. A graph edge is a lead until the line is read (`evidence.md` §E1).

---

## 5. Report line

```
GRAPH — tool <name> <version> (probed); trigger signals held <list>; index path <path>, fresh as of <commit>; queries <n>, truncated <t>; edges used E (extracted X, inferred I); stale-check: <pass|fail>.
```

---

## 6. Sources

- GitNexus README (per the search result, the `cdn.jsdelivr.net` copy of `abhigyanpatwari/GitNexus` on `main`): https://cdn.jsdelivr.net/gh/abhigyanpatwari/GitNexus@main/README.md
- GitNexus overview: https://aiagentstore.ai/ai-agent/gitnexus
- Where the details disagree (tool count, storage format, LLM use for wiki generation), the installed version's own documentation wins over both.
