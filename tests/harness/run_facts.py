"""What a finished run left behind, read into the facts its header carries: the report text, the
model and cost, the receipts it quoted, the references it opened, the sweep lines that name sites.

Split from cold_run.py on 2026-11-10 (it had reached 597 lines). One job: read, never run. Every
function here takes text or a path and returns facts, so each is tested without a CLI.
"""
import importlib.util
import json
import re
from pathlib import Path


# Vocabulary only the cia skill teaches. An arm report that carries it read cia somehow (a python
# one-liner, the user CLAUDE.md naming the path), and its score says nothing about the baseline.
CIA_TRACES = ("S:\\ai\\skills\\cia", "references/", "SKILL.md", "§", "ROUTE block", "Verified Controls")


def cia_traces(text):
    return [t for t in CIA_TRACES if t in text]


def claude_result(stdout):
    """(report text, facts) from `claude -p --output-format json`; raw stdout if it is not that JSON.

    Why JSON: the `sonnet` alias resolves to whatever model is current, and on 2026-11-09 the same
    doctrine went from four of four runs reading the references to two of eight within hours, with
    no record of which model had answered. The header now names it, with cost and turns."""
    try:
        d = json.loads(stdout)
    except ValueError:
        return stdout, {}
    if not isinstance(d, dict):
        return stdout, {}
    return d.get("result") or "", {"resolved": ",".join(d.get("modelUsage") or {}) or "?",
                                   "cost": d.get("total_cost_usd"), "turns": d.get("num_turns"),
                                   "session": d.get("session_id")}


SHORT_RESULT = 2000  # characters; a report is never this short, a reply to a late notification always is


def longest_reply(jsonl_text):
    """The longest assistant text in a Claude Code session transcript (one JSON object per line).

    Why: `claude -p` returns only the LAST turn. A run that left a background server up got one more
    turn when that task was killed at its time limit, and the result was a two-line note about the
    server; the 13,788-character report was the turn before (both fixture-shop-live runs, 2026-11-10)."""
    best = ""
    for line in jsonl_text.splitlines():
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if not isinstance(d, dict) or d.get("type") != "assistant":
            continue
        for c in (d.get("message") or {}).get("content") or []:
            if isinstance(c, dict) and c.get("type") == "text" and len(c.get("text", "")) > len(best):
                best = c["text"]
    return best


def recovered_reply(out_text, collected, transcript_text):
    """The earlier, longer reply to save in place of a short final one, or None to keep the final reply.

    The trap: under the skill's Stop hook the final reply is short BECAUSE the run went on to fix its
    report, and the longest earlier reply is the draft the hook blocked. So only a run with no collected
    report file falls back (the hooked batch of 2026-11-10 saved ten stale drafts before this)."""
    if collected or len(out_text) >= SHORT_RESULT:
        return None
    longer = longest_reply(transcript_text)
    return longer if len(longer) > len(out_text) else None


def transcript_of(session, cwd, home=None):
    """Where Claude Code keeps a session's transcript: ~/.claude/projects/<cwd, non-alphanumerics as ->/<id>.jsonl."""
    enc = re.sub(r"[^A-Za-z0-9]", "-", str(Path(cwd).resolve()))
    return Path(home or Path.home()) / ".claude" / "projects" / enc / f"{session}.jsonl"


def receipts_quoted(text, root):
    """(quoted, total): how many of the skill's reading receipts the report carries.

    A receipt can be grepped rather than read, so this counts quoting, not reading; but a report
    with none certainly worked from the index, which is the failure the count makes visible."""
    path = root / "tools" / "receipts.py"
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("skill_receipts", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    found = mod.scan()[0]
    return sum(1 for phrase in found.values() if phrase in text), len(found)


# Phrases a report uses when it admits reading a reference in part. Added 2026-11-09: runs AF and AJ quoted
# all nine receipts and said, further down, that five were read 'only' at their closing line. The receipt
# count cannot see that; this count can, and it is a line count of admissions, not a proof of reading.
PARTIAL_READ = re.compile(
    r"only (?:the |their )?(?:closing )?receipt lines?|read only (?:the|their)|by heading only|"
    r"not read in full|read (?:§[\w.–-]+|sections?)[^.\n]{0,30} only|skimmed|read in part",
    re.IGNORECASE)


def partial_reads(text):
    """How many lines of the report admit a reference read in part."""
    return sum(1 for line in text.splitlines() if PARTIAL_READ.search(line))


# A 2a sweep line that names sites. Added 2026-11-09: Codex runs C4 and C5 each closed a sweep with
# a finding ref and no site list, and each missed the second instance of a class in a file whose
# first instance it had filed. A sweep line is one that STARTS with its id ("- **S3:**", "S3 swept",
# "| S3 |"); its indented sub-lines belong to it. Finding rows ("| RUN-1 | S3 |") are not sweep lines,
# so a finding ref cannot stand in for a site list here either. A count of sweeps whose line carries
# a path, not a proof that every site was read.
SWEEP_START = re.compile(r"^(\s*)[-*|]?\s*\**S(\d{1,2})(?:\.\d+)?\b")
PATHLIKE = re.compile(r"[\w.-]+/[\w./-]+|\b[\w-]+\.(?:py|js|ts|php|go|rb|json|toml|ya?ml|sql)\b")


def sweep_sites(text):
    """How many of S1-S24 have a sweep line (or its indented sub-lines) carrying a path."""
    ids, cur, depth = set(), None, 0
    for line in text.splitlines():
        m = SWEEP_START.match(line)
        if m:
            depth = len(m.group(1))
            cur = int(m.group(2)) if 1 <= int(m.group(2)) <= 24 else None
        elif len(line) - len(line.lstrip()) <= depth:   # back at or above the sweep line's indent
            cur = None
        if cur and PATHLIKE.search(line):
            ids.add(cur)
    return len(ids)


def refs_opened(transcript, names):
    """Which of the skill's reference files (`names`, paths relative to references/) Codex's commands name:
    an upper bound on reading (a grep or a tail counts too). Two traps met on the first real log: the log
    also holds every file's *output*, and SKILL.md's index names all nineteen references, so only the
    command line after each `exec` marker is read; and Codex opens files from Python one-liners
    (`root=Path('...references'); names=['theory.md', ...]`), so a bare file name counts when the same
    command mentions `references`, not only a `references/x.md` path."""
    lines = transcript.splitlines()
    commands = [lines[i + 1] for i, line in enumerate(lines[:-1]) if line.strip() == "exec"]
    hit = set()
    for cmd in (c.replace("\\\\", "/").replace("\\", "/") for c in commands):
        if "references" not in cmd:
            continue
        hit.update(n for n in names if n in cmd or n.split("/")[-1] in cmd)
    return sorted(hit)
