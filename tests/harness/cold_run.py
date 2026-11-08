"""Launch one cold run of this skill against a fixture and capture its report, so a doctrine change is scored by a fresh agent and not by the author.

Usage:
    python tests/harness/cold_run.py --mode audit|build|run-tests
        [--runtime claude|codex] [--dry-run] [--model NAME]

Exit codes: 0 ok, 2 bad input or a missing RUNBOOK section/prompt.

Where things come from
    Prompts are READ from tests/RUNBOOK.md at run time, never hard-coded here: the
    RUNBOOK is the one source of truth, and a copy in this file would drift the first
    time the RUNBOOK wording is tuned (the harness would then score a different
    prompt than the one the humans think they are using).
    The RUNBOOK path can be overridden with the CIA_RUNBOOK env variable (tests use
    this so they do not depend on the live RUNBOOK's progress).

Working directory
    audit / run-tests: tests/fixture-service.
    build: a fresh tempfile.mkdtemp() copy of the fixture. A build run changes code;
    it must never change the planted defects the audit scoring depends on.

Output
    Non-dry-run writes stdout to tests/harness/out/<YYYY-MM-DD>-<mode>-<runtime>.md,
    first line naming the skill commit (git rev-parse HEAD, a read-only call), the
    runtime and the model, and prints only that path. tests/harness/out/ is expected
    to be gitignored by the repo root .gitignore (the coordinator adds it); this
    script deliberately creates no .gitignore of its own.

Runtimes
    claude: `claude -p <prompt> --output-format text [--model NAME]`.
    codex:  `codex exec --skip-git-repo-check -s workspace-write [-m MODEL] -o FILE -` with the prompt on
    stdin, always on a temporary copy of the fixture (flags checked against codex-cli 0.157).
"""
import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
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


def build_prompt(mode, runbook_text):
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
    return f"{base}\n\n{hard_rules(runbook_text)}\n\n{SKILL_LINE}"


# A headless run has nobody to approve a tool call, so each mode gets a bounded allow-list instead.
# Audit and run-tests get no Write/Edit: the fixture's planted defects must survive the run, and the
# list enforces that rather than trusting the HARD RULES text. Build mode edits, but only ever on the
# throwaway copy main() makes.
# The project's own linter and test runner are part of Step 1; a run that cannot call them reports NOT RUN.
READ_TOOLS = ["Read", "Grep", "Glob", "Skill", "Bash(python:*)", "Bash(py:*)", "Bash(ls:*)", "Bash(wc:*)",
              "Bash(ruff:*)", "Bash(pytest:*)"]
ALLOWED_TOOLS = {
    "audit": READ_TOOLS,
    "run-tests": READ_TOOLS,
    "build": READ_TOOLS + ["Write", "Edit"],
}


def build_command(runtime, prompt, model, mode=None):
    if runtime == "claude":
        cmd = ["claude", "-p", prompt, "--output-format", "text"]
        if model:
            cmd += ["--model", model]
        if mode in ALLOWED_TOOLS:
            cmd += ["--allowedTools", *ALLOWED_TOOLS[mode]]
    else:
        # codex: flags checked against `codex exec --help` (codex-cli 0.157). Codex sandboxes the whole
        # run rather than single tools, so every codex run works on a throwaway copy of the fixture
        # (see main) with a writable sandbox there; the planted defects cannot change by construction.
        cmd = ["codex", "exec", "--skip-git-repo-check", "-s", "workspace-write"]
        if model:
            cmd += ["-m", model]
        cmd += [prompt]
    return cmd


def skill_commit():
    out = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True
    )
    return out.stdout.strip() or "unknown"


def main(argv=None, runbook=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--mode", required=True, choices=["audit", "build", "run-tests"])
    ap.add_argument("--runtime", default="claude", choices=["claude", "codex"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--model")
    args = ap.parse_args(argv)  # argparse exits 2 on a malformed --mode

    rb_path = Path(runbook or os.environ.get("CIA_RUNBOOK") or DEFAULT_RUNBOOK)
    try:
        prompt = build_prompt(args.mode, rb_path.read_text(encoding="utf-8"))
    except (RunbookError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    cmd = build_command(args.runtime, prompt, args.model, args.mode)

    if args.mode == "build" or args.runtime == "codex":
        if args.dry_run:
            cwd = os.path.join(tempfile.gettempdir(), f"cia-{args.mode}-<new-copy>")
        else:
            cwd = tempfile.mkdtemp(prefix=f"cia-{args.mode}-")
            shutil.copytree(FIXTURE, cwd, dirs_exist_ok=True)
            print(f"{args.mode} copy: {cwd}", file=sys.stderr)
    else:
        cwd = str(FIXTURE)

    if args.dry_run:
        print(json.dumps(cmd))
        print(f"cwd: {cwd}")
        return 0

    # Trap 1: on Windows the CLIs are npm .CMD shims, which subprocess cannot start by bare name.
    exe = shutil.which(cmd[0])
    if exe is None:
        print(f"error: {cmd[0]} is not on PATH", file=sys.stderr)
        return 2
    # Trap 2: a .CMD shim runs through cmd.exe, which cuts an argument at its first line break, and the
    # prompt carries the multi-line HARD RULES block. claude -p reads the prompt from stdin instead.
    if args.runtime == "claude":
        argv = [exe] + [a for a in cmd[1:] if a != prompt]
        stdin = prompt
    else:  # codex reads the prompt from stdin when it is "-"; -o keeps only its final message
        last_msg = os.path.join(tempfile.mkdtemp(prefix="cia-codex-out-"), "last.md")
        argv = [exe] + [a for a in cmd[1:] if a != prompt] + ["-o", last_msg, "-"]
        stdin = prompt
    res = subprocess.run(argv, cwd=cwd, input=stdin, capture_output=True, text=True,
                         encoding="utf-8", timeout=TIMEOUT_S)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    day = datetime.date.today().isoformat()
    stamp = datetime.datetime.now().strftime("%H%M%S")  # two same-day runs of one mode must not overwrite each other
    path = OUT_DIR / f"{day}-{stamp}-{os.getpid()}-{args.mode}-{args.runtime}.md"
    header = (
        f"<!-- skill commit {skill_commit()} | runtime {args.runtime} | "
        f"model {args.model or 'default'} | exit {res.returncode} -->\n"
    )
    # Trap 3: a failed run must not be saved as an empty report and exit 0 - that is the fail-open
    # this skill audits for. Keep stderr in the artefact and return non-zero.
    out_text = res.stdout
    if args.runtime == "codex" and os.path.exists(last_msg):
        out_text = Path(last_msg).read_text(encoding="utf-8")
    body = out_text if res.returncode == 0 else f"{out_text}\n\n<!-- stderr -->\n{res.stderr}"
    path.write_text(header + body, encoding="utf-8")
    print(path)
    return 0 if res.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
