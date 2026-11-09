"""Launch one cold run of this skill against a fixture and capture its report, so a doctrine change is scored by a fresh agent and not by the author.

Usage:
    python tests/harness/cold_run.py --mode audit|build|run-tests
        [--runtime claude|codex] [--dry-run] [--model NAME]
    python tests/harness/cold_run.py --mode audit --arm none|ponytail [--model NAME]
    python tests/harness/cold_run.py --mode egm --doc references/X.md [--reviewer comprehension]

Exit codes: 0 ok, 2 bad input or a missing RUNBOOK section/prompt.

Comparison arms (--arm, audit only, claude only)
    The same audit task, HARD RULES and permission shape, with the skill swapped out: `none` gives
    no skill, `ponytail` gives ponytail-audit's instructions (pinned copy in tests/harness/arms/).
    They answer whether cia earns its tokens against a bare model and a popular rival. An arm run
    may not read the cia skill: Read is scoped to the working copy, skills are disabled, and the
    header records any cia vocabulary the report still carries (`cia-traces`). Arm rows go to
    tests/ARMS.md, never RUNS.md: they measure the baseline, not the doctrine under test.

EGM reviews (--mode egm)
    One Goldfish reviewer of the egm plugin (`claude -p --agent egm:egm-<reviewer>`) cold-reads one
    of this skill's documents, read-only (Read/Grep/Glob only), from the skill root. Rows go to
    tests/EGM.md. tools/due.py says which documents and arms are due; the AI runs what it lists.

Where things come from
    Prompts are READ from tests/RUNBOOK.md at run time, never hard-coded here: the
    RUNBOOK is the one source of truth, and a copy in this file would drift the first
    time the RUNBOOK wording is tuned (the harness would then score a different
    prompt than the one the humans think they are using).
    The RUNBOOK path can be overridden with the CIA_RUNBOOK env variable (tests use
    this so they do not depend on the live RUNBOOK's progress).

Working directory
    Every mode: a fresh tempfile.mkdtemp() copy of the fixture (tests/fixture-service, or
    --skill-root/tests/--fixture). A build run changes code and an audit's runtime walk
    writes the fixture's state; neither may change the planted defects the scoring depends on.

Output
    Non-dry-run writes stdout to tests/harness/out/<YYYY-MM-DD>-<mode>-<runtime>.md,
    first line naming the skill commit (git rev-parse HEAD, a read-only call), the
    runtime and the model, and prints only that path. tests/harness/out/ is expected
    to be gitignored by the repo root .gitignore (the coordinator adds it); this
    script deliberately creates no .gitignore of its own.

Runtimes
    claude: `claude -p --output-format json [--model NAME]`, prompt on stdin; the report is the JSON `result`,
    and the header adds the model that answered, cost, turns and the receipts the report quotes.
    codex:  `codex exec --skip-git-repo-check -s danger-full-access [-m MODEL] -o FILE -` with the prompt
    on stdin, always on a temporary copy of the fixture (flags checked against codex-cli 0.157). Full
    access is the owner's decision of 2026-11-09: the Windows workspace-write sandbox runs commands
    under a restricted token that cannot start a per-user Python (error 5), so no run could test.
"""
import argparse
import datetime
import importlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "tests" / "fixture-service"
DEFAULT_RUNBOOK = REPO / "tests" / "RUNBOOK.md"
OUT_DIR = REPO / "tests" / "harness" / "out"
SKILL_DIR = r"S:\ai\skills\cia"
TIMEOUT_S = 3600

SKILL_LINE = (
    f"You may and should read the skill at {SKILL_DIR} (SKILL.md and references/) "
    "per its section 0.13."
)
# What an interactive owner would have approved, said up front. The allow-list matches a command by
# its first word, so `cd dir && node x`, `VAR=1 node x` and `node x | grep` are refused in a headless
# run, and runs that composed commands that way could not start the shop: three of ten on 2026-11-09
# (E, H, I) were downgraded to code reviews and graded the race from reading. This is the session's
# permission shape, not doctrine: it names no defect and no method.
SHELL_LINE = (
    "Shell commands in this session are pre-approved only when the command itself starts with python, py, "
    "node, curl, ls, wc, ruff or pytest, run from the working directory: no `cd ... &&`, no `VAR=value` "
    "prefix, no pipes into other programs. Set environment variables inside your own script "
    "(process.env / os.environ), and start a server with the Bash tool's run_in_background option."
)


ARM_DIR = REPO / "tests" / "harness" / "arms"
PONYTAIL_COMMIT = "96608e0"  # DietrichGebert/ponytail, skills/ponytail-audit/SKILL.md; see arms/README.md
NO_SKILL_LINE = ("No skill is provided for this run. Audit the project with your own judgement; "
                 "do not look for skill files.")


def arm_line(arm):
    """What replaces the cia skill line for a comparison arm. The task text stays identical."""
    if arm == "none":
        return NO_SKILL_LINE
    if arm == "ponytail":
        text = (ARM_DIR / "ponytail-audit" / "SKILL.md").read_text(encoding="utf-8")
        body = text.split("---", 2)[2].strip()  # drop the frontmatter: the Skill tool would not show it either
        return (f"No skill is installed for this run. Follow these audit instructions "
                f"(ponytail-audit at {PONYTAIL_COMMIT}):\n\n{body}")
    raise ValueError(f"unknown arm {arm!r}")


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
                                   "cost": d.get("total_cost_usd"), "turns": d.get("num_turns")}


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


# Processes a run leaves behind. Added 2026-11-09: Codex runs C1-C7 each left a `graphify watch`
# running after `codex exec` returned, seven found at once, parents gone. The harness REPORTS them and
# never stops them: what to stop on the owner's machine is the owner's call. A failed snapshot is
# `n/r`, never 0 - a count of zero from a listing that did not run is the blind instrument S20 audits.
def list_processes():
    """Every process as {pid, ppid, cmd}, or None when the listing cannot be taken."""
    try:
        if os.name == "nt":
            # Trap: Windows PowerShell writes in the console code page (cp950 here), and one non-UTF-8
            # command line crashed the reader on 2026-11-09. Force UTF-8 out, and replace what still is not.
            ps = ("[Console]::OutputEncoding = [Text.Encoding]::UTF8; "
                  "Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,CommandLine"
                  " | ConvertTo-Json -Compress")
            out = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True,
                                 text=True, encoding="utf-8", errors="replace", timeout=60).stdout
            return [{"pid": p["ProcessId"], "ppid": p["ParentProcessId"], "cmd": p.get("CommandLine") or ""}
                    for p in json.loads(out)]
        out = subprocess.run(["ps", "-eo", "pid=,ppid=,args="], capture_output=True, text=True,
                             errors="replace", timeout=60).stdout
        rows = (line.split(None, 2) for line in out.splitlines() if line.strip())
        return [{"pid": int(r[0]), "ppid": int(r[1]), "cmd": r[2] if len(r) > 2 else ""} for r in rows]
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        return None


def leftovers(before_pids, after, copy_dir):
    """New processes that outlived the run: orphaned (parent gone) or naming the fixture copy.

    Two traps: a parallel harness run's orphan is reported by every run that ends after it (the
    report says so, it does not guess whose), and Windows reuses PIDs, so an orphan whose parent PID
    was reused looks parented - a false negative, never a false alarm."""
    alive = {p["pid"] for p in after}
    return [p for p in after if p["pid"] not in before_pids
            and (p["ppid"] not in alive or (copy_dir and copy_dir.lower() in p["cmd"].lower()))]


def copy_fixture(src, dst):
    """The throwaway copy a run works on. A corpus clone's .git holds the maintainer's fix commit, which
    is the oracle, so .git is never copied: a run that ran `git log` would read the answer."""
    shutil.copytree(src, dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".git"))


def owned_by_run(left, copy_dir):
    """The leftovers that are certainly this run's: their command line names its own throwaway copy.

    Only these are stopped (the owner approved this on 2026-11-10). Codex obeys a user's global
    AGENTS.md, and one that says "keep a graphify watch running per project" started a watcher in every
    copy and left it running. An orphan that does not name the copy may be a parallel run's or the
    user's own, so it stays a report: stopping what cannot be attributed would be the fail-open this
    skill audits for."""
    return [p for p in left if copy_dir and copy_dir.lower() in p["cmd"].lower()]


def stop(pids):
    """Stop each process and its children; returns the PIDs the OS reported as stopped."""
    done = []
    for pid in pids:
        cmd = ["taskkill", "/PID", str(pid), "/T", "/F"] if os.name == "nt" else ["kill", "-TERM", str(pid)]
        if subprocess.run(cmd, capture_output=True).returncode == 0:
            done.append(pid)
    return done


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


EGM_REVIEWERS = ("comprehension", "structural", "style", "design", "codebase-details",
                 "implementation-readiness", "zoom-out")


def egm_prompt(doc):
    # The last line is fixed so a row in tests/EGM.md is copied, not counted by hand.
    return (f"Mode: REVIEW\nDocument: {doc}\n"
            "The working directory is the repository the document belongs to; read any file you need.\n"
            "Review the document in your role, read-only. Give every finding its path:line, group them as "
            "Blocker, Major and Nit, and end with exactly one line: `Findings: <blockers>/<majors>/<nits>`.")


class RunbookError(Exception):
    """A RUNBOOK section or prompt this harness depends on is missing."""


def section(text, heading):
    """Body of the '## heading' section (up to the next '## ' heading), exact heading match."""
    lines = text.split("\n")
    start = None
    for i, line in enumerate(lines):
        if line.rstrip() == heading:
            start = i + 1
            break
    if start is None:
        raise RunbookError(f"RUNBOOK section not found: {heading!r}")
    end = len(lines)
    for j in range(start, len(lines)):
        # '### ' subsections stay inside; only a sibling/parent '## ' ends the section.
        if re.match(r"^## (?!#)", lines[j]):
            end = j
            break
    return "\n".join(lines[start:end])


def first_fence(text):
    """Content of the first fenced code block in text, or None."""
    m = re.search(r"^```[^\n]*\n(.*?)^```", text, re.S | re.M)
    return m.group(1).rstrip("\n") if m else None


def hard_rules(text):
    """The fenced block whose first line is 'HARD RULES:', byte-for-byte between the fences."""
    for m in re.finditer(r"^```[^\n]*\n(.*?)^```", text, re.S | re.M):
        body = m.group(1)
        if body.startswith("HARD RULES:"):
            return body.rstrip("\n")
    raise RunbookError("RUNBOOK has no fenced block beginning with 'HARD RULES:'")


def backticked(text, wanted):
    """Find a backticked span in text equal to wanted; fail if absent."""
    for span in re.findall(r"`([^`\n]+)`", text):
        if span == wanted:
            return span
    raise RunbookError(f"RUNBOOK Procedure has no backticked prompt {wanted!r}")


def build_prompt(mode, runbook_text, skill_line=SKILL_LINE):
    """Mode prompt + HARD RULES + skill-reading line, all sourced from the RUNBOOK."""
    if mode == "build":
        try:
            body = section(runbook_text, "## The build-mode run")
        except RunbookError:
            raise RunbookError("RUNBOOK has no '## The build-mode run' section")
        base = first_fence(body)
        if base is None:
            raise RunbookError("'## The build-mode run' has no fenced code block")
    else:
        proc = section(runbook_text, "## Procedure")
        base = backticked(
            proc, "pre-launch audit, Screen tier" if mode == "audit" else "run tests"
        )
    return f"{base}\n\n{hard_rules(runbook_text)}\n\n{skill_line}\n\n{SHELL_LINE}"


# A headless run has nobody to approve a tool call, so each mode gets a bounded allow-list instead.
# Audit and run-tests get no Write/Edit: the fixture's planted defects must survive the run, and the
# list enforces that rather than trusting the HARD RULES text. Build mode edits, but only ever on the
# throwaway copy main() makes.
# The project's own linter and test runner are part of Step 1; a run that cannot call them reports NOT RUN.
# node and curl are the runtime walk of a Node fixture (ecommerce-cia's fixture-shop-node): without them
# the run cannot fire a probe, so it grades every race from reading, one level low. Measured 2026-11-09:
# two runs blocked this way scored 3.5 and 3.0 where probing runs score 4. They add no write power that
# python does not already have; the planted code is protected by running on a copy (see main).
READ_TOOLS = ["Read", "Grep", "Glob", "Skill", "Bash(python:*)", "Bash(py:*)", "Bash(ls:*)", "Bash(wc:*)",
              "Bash(ruff:*)", "Bash(pytest:*)", "Bash(node:*)", "Bash(curl:*)"]
ALLOWED_TOOLS = {
    # An audit writes exactly one file, its report (SKILL Step 6); `Edit(./path)` is the rule Claude Code
    # honours for a single file (checked 2026-11-09: `Write(path)` patterns did not grant it headless).
    "audit": READ_TOOLS + ["Edit(./cia-audit-report.md)"],
    "run-tests": READ_TOOLS,
    "build": READ_TOOLS + ["Write", "Edit"],
    "egm": ["Read", "Grep", "Glob"],  # a Goldfish only reads; the list enforces it
}
# A comparison arm must not reach the cia skill: Read is scoped to the working copy (checked
# 2026-11-09: `Read(./**)` denies S:\ai\skills\cia\SKILL.md headless) and the Skill tool is gone.
ARM_TOOLS = ["Read(./**)"] + [t for t in READ_TOOLS if t not in ("Read", "Skill")]


def build_command(runtime, prompt, model, mode=None, arm="cia", reviewer=None):
    if runtime == "claude":
        cmd = ["claude", "-p", prompt, "--output-format", "json"]
        if model:
            cmd += ["--model", model]
        if mode == "egm":
            cmd += ["--agent", f"egm:egm-{reviewer}"]
        if arm != "cia":
            cmd += ["--disable-slash-commands", "--allowedTools", *ARM_TOOLS]
        elif mode in ALLOWED_TOOLS:
            cmd += ["--allowedTools", *ALLOWED_TOOLS[mode]]
    else:
        # codex: flags checked against `codex exec --help` (codex-cli 0.157). Codex sandboxes the whole
        # run rather than single tools. On Windows its workspace-write sandbox denies CreateProcessAsUserW
        # on a per-user python.exe (error 5, `codex sandbox python --version`), so the owner granted full
        # access (2026-11-09). The trap: full access is safe here ONLY because every codex run works on a
        # throwaway copy of the fixture (see main) - never point a codex run at the repo itself.
        cmd = ["codex", "exec", "--skip-git-repo-check", "-s", "danger-full-access"]
        if model:
            cmd += ["-m", model]
        cmd += [prompt]
    return cmd


def skill_commit(root=REPO):
    # The commit of the skill under test - a sibling skill's own HEAD, not this repo's.
    out = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True
    )
    return out.stdout.strip() or "unknown"


def main(argv=None, runbook=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--mode", required=True, choices=["audit", "build", "run-tests", "egm"])
    ap.add_argument("--runtime", default="claude", choices=["claude", "codex"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--model")
    # One launcher for sibling skills (ecommerce-cia): their RUNBOOK, fixture and skill path, not a copy of this script.
    ap.add_argument("--skill-root", help="skill repo whose tests/RUNBOOK.md and fixture to use (default: this repo)")
    ap.add_argument("--fixture", default="fixture-service", help="folder under <skill-root>/tests/")
    ap.add_argument("--arm", default="cia", choices=["cia", "none", "ponytail"],
                    help="audit with the skill swapped out (comparison arm; rows go to tests/ARMS.md)")
    ap.add_argument("--doc", help="egm: the document to review, relative to the skill root")
    ap.add_argument("--reviewer", default="comprehension", choices=EGM_REVIEWERS, help="egm: which Goldfish")
    ap.add_argument("--target", help="audit: any directory instead of a fixture (the corpus: a repo prepared by "
                                     "tests/corpus/run.py prepare); copied without .git")
    ap.add_argument("--scope", help="audit with --target: the entry's scope, appended to the prompt")
    args = ap.parse_args(argv)  # argparse exits 2 on a malformed --mode

    skill_root = Path(args.skill_root).resolve() if args.skill_root else REPO
    if args.mode == "egm":
        return run_egm(args, skill_root)
    # The arms are scored against this repo's key, and only the claude CLI can scope Read to the copy.
    if args.arm != "cia" and (args.mode != "audit" or args.runtime != "claude" or skill_root != REPO):
        print("error: --arm runs only with --mode audit, --runtime claude and this repo's fixture", file=sys.stderr)
        return 2
    if args.target and args.mode != "audit":
        print("error: --target is for --mode audit (the corpus)", file=sys.stderr)
        return 2
    fixture = Path(args.target).resolve() if args.target else skill_root / "tests" / args.fixture
    if not fixture.is_dir():
        print(f"error: no fixture at {fixture}", file=sys.stderr)
        return 2
    skill_line = SKILL_LINE if skill_root == REPO else (
        f"You may and should read the skill at {skill_root} (SKILL.md and references/), per its own reference index.")
    if args.arm != "cia":
        skill_line = arm_line(args.arm)
    rb_path = Path(runbook or os.environ.get("CIA_RUNBOOK") or (skill_root / "tests" / "RUNBOOK.md"))
    try:
        prompt = build_prompt(args.mode, rb_path.read_text(encoding="utf-8"), skill_line)
    except (RunbookError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if args.scope:
        prompt += f"\nScope for this audit: {args.scope}\n"

    cmd = build_command(args.runtime, prompt, args.model, args.mode, args.arm)

    # Every run works on a throwaway copy of the fixture: build edits it, codex sandboxes the whole run,
    # and an audit's runtime walk (node server.js --reset, a probe) writes the fixture's own state. The
    # planted code and the repo's working tree cannot change by construction, whatever the run executes.
    if args.dry_run:
        cwd = os.path.join(tempfile.gettempdir(), f"cia-{args.mode}-<new-copy>")
    else:
        cwd = tempfile.mkdtemp(prefix=f"cia-{args.mode}-")
        copy_fixture(fixture, cwd)
        print(f"{args.mode} copy of {fixture}: {cwd}", file=sys.stderr)

    if args.dry_run:
        print(json.dumps(cmd))
        print(f"fixture: {fixture}")
        print(f"cwd: {cwd}")
        return 0

    tag = "" if skill_root == REPO else f"{skill_root.name}-{args.fixture}-"
    if args.target:
        tag = f"corpus-{fixture.name}-"
    if args.arm != "cia":
        tag += f"arm-{args.arm}-"
    label = "" if args.arm == "cia" else f"arm {args.arm} | "
    return execute(cmd, prompt, cwd, args.runtime, args.model, f"{tag}{args.mode}", label, skill_root,
                   traces=args.arm != "cia", receipts=args.arm == "cia",
                   report_file={"build": BUILD_REPORT, "audit": AUDIT_REPORT}.get(args.mode))


def run_egm(args, skill_root):
    """One EGM Goldfish on one document of the skill, read-only, from the skill root."""
    if args.runtime != "claude" or not args.doc:
        print("error: --mode egm needs --doc and the claude runtime", file=sys.stderr)
        return 2
    doc = (skill_root / args.doc).resolve()
    if not doc.is_file() or skill_root not in doc.parents:
        print(f"error: no document {args.doc} inside {skill_root}", file=sys.stderr)
        return 2
    rel = doc.relative_to(skill_root).as_posix()
    prompt = egm_prompt(rel)
    cmd = build_command("claude", prompt, args.model, "egm", reviewer=args.reviewer)
    if args.dry_run:
        print(json.dumps(cmd))
        print(f"cwd: {skill_root}")
        return 0
    return execute(cmd, prompt, str(skill_root), "claude", args.model, f"egm-{doc.stem}-{args.reviewer}",
                   f"egm {rel} | reviewer {args.reviewer} | ", skill_root, receipts=False)


BUILD_REPORT = "cia-build-report.md"
AUDIT_REPORT = "cia-audit-report.md"
# Which checker counts which report: the skill's own tools, imported from the skill under test.
CHECKERS = {BUILD_REPORT: "build_report", AUDIT_REPORT: "audit_report"}


def collect_report(path, root, label):
    """The report is a file the run writes in the project (SKILL Step 6, §0.10a), not its reply: build
    replies (2 of 8) and audit replies (BC, BE) were summaries of a checked report that dropped parts.
    Collect the file, and put the checker's own count in the header, so the scorer and the run read
    the same instrument."""
    if not path.is_file():
        return label + "report-file none | ", ""
    text = path.read_text(encoding="utf-8", errors="replace")
    tools = str(Path(root) / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    try:
        checker = importlib.import_module(CHECKERS.get(path.name, "build_report"))
        results = checker.checks(text)
        label += f"report-file {sum(ok for _, ok, _ in results)}/{len(results)} | "
    except ImportError:
        label += "report-file present, checker n/r | "
    return label, f"\n\n<!-- {path.name}, collected from the copy -->\n{text}"


def execute(cmd, prompt, cwd, runtime, model, name, label, root, traces=False, receipts=True, report_file=None):
    """Run the CLI with the prompt on stdin, save stdout under tests/harness/out/, print the path."""
    # Read the commit BEFORE the run: read after, a commit that landed mid-run was stamped on a run that
    # never saw it (four rows on 2026-11-09 needed a "header says X" note for exactly this).
    commit = skill_commit(root)
    # Trap 1: on Windows the CLIs are npm .CMD shims, which subprocess cannot start by bare name.
    exe = shutil.which(cmd[0])
    if exe is None:
        print(f"error: {cmd[0]} is not on PATH", file=sys.stderr)
        return 2
    # Trap 2: a .CMD shim runs through cmd.exe, which cuts an argument at its first line break, and the
    # prompt carries the multi-line HARD RULES block. claude -p reads the prompt from stdin instead.
    last_msg = None
    if runtime == "claude":
        argv = [exe] + [a for a in cmd[1:] if a != prompt]
    else:  # codex reads the prompt from stdin when it is "-"; -o keeps only its final message
        last_msg = os.path.join(tempfile.mkdtemp(prefix="cia-codex-out-"), "last.md")
        argv = [exe] + [a for a in cmd[1:] if a != prompt] + ["-o", last_msg, "-"]
    before = list_processes()
    t0 = time.monotonic()
    res = subprocess.run(argv, cwd=cwd, input=prompt, capture_output=True, text=True,
                         encoding="utf-8", timeout=TIMEOUT_S)
    label += f"seconds {round(time.monotonic() - t0)} | "  # the cost side of an arm comparison
    after = list_processes()
    left = None if before is None or after is None else leftovers({p["pid"] for p in before}, after, str(cwd))
    label += f"leftover-procs {'n/r' if left is None else len(left)} | "
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    day = datetime.date.today().isoformat()
    stamp = datetime.datetime.now().strftime("%H%M%S")  # two same-day runs of one mode must not overwrite each other
    path = OUT_DIR / f"{day}-{stamp}-{os.getpid()}-{name}-{runtime}.md"
    # Trap 3: a failed run must not be saved as an empty report and exit 0 - that is the fail-open
    # this skill audits for. Keep stderr in the artefact and return non-zero.
    out_text, facts = (claude_result(res.stdout) if runtime == "claude" else (res.stdout, {}))
    if last_msg and os.path.exists(last_msg):
        out_text = Path(last_msg).read_text(encoding="utf-8")
        # Codex's -o keeps only its final message; its stdout is the event log of what it opened and ran.
        # Kept beside the report because "did it read the references?" is otherwise unanswerable.
        path.with_suffix(".transcript.log").write_text(res.stdout + "\n" + res.stderr, encoding="utf-8")
        refs = sorted(str(f.relative_to(root / "references")).replace("\\", "/") for f in (root / "references").rglob("*.md"))
        label += f"refs-opened {len(refs_opened(res.stdout + res.stderr, refs))}/{len(refs)} | "
    if facts:
        label += f"resolved {facts['resolved']} | cost {facts['cost']} | turns {facts['turns']} | "
    collected = ""
    if report_file:
        label, collected = collect_report(Path(cwd) / report_file, root, label)
    # The report is the collected file when there is one; the reply is then a summary, and counting
    # receipts in it printed "receipts 0/19" on runs whose report quoted all nine.
    report = collected or out_text
    rq = receipts_quoted(report, root) if receipts else None
    if rq:
        label += (f"receipts {rq[0]}/{rq[1]} | partial-reads {partial_reads(report)} | "
                  f"sweep-sites {sweep_sites(report)}/24 | ")
    if traces:
        label += f"cia-traces {', '.join(cia_traces(out_text)) or 'none'} | "
    header = (
        f"<!-- skill commit {commit} | runtime {runtime} | "
        f"model {model or 'default'} | {label}exit {res.returncode} -->\n"
    )
    body = out_text if res.returncode == 0 else f"{out_text}\n\n<!-- stderr -->\n{res.stderr}"
    body += collected
    path.write_text(header + body, encoding="utf-8")
    if left:
        stopped = set(stop([p["pid"] for p in owned_by_run(left, str(cwd))]))
        listing = "\n".join(f"{p['pid']}\tparent {p['ppid']}\t"
                            f"{'stopped' if p['pid'] in stopped else 'left running'}\t{p['cmd']}" for p in left)
        path.with_suffix(".leftovers.log").write_text(listing + "\n", encoding="utf-8")
        print(f"warning: {len(left)} process(es) outlived the run; stopped {len(stopped)} that named its copy, "
              f"left the rest; see {path.with_suffix('.leftovers.log')}", file=sys.stderr)
    print(path)
    return 0 if res.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
