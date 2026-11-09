"""Which harness checks are due now — comparison arms and EGM reviews — with the command for each.

Usage: python tools/due.py      (advisory: always exits 0; prints what to run, or "nothing due")

Who runs it: the AI, at the end of every edit to SKILL.md or references/ (SKILL.md "Testing this
skill", RUNBOOK step 7), and then runs what it lists. That is how these checks are triggered
"whenever appropriate" without a hook: a hook fires in every session on this machine, and each of
these runs costs minutes of a model, so the trigger is a rule with a threshold the AI reads.

What makes each due
    Arms (tests/ARMS.md): no arm row yet; or the doctrine (SKILL.md + references/) grew by
    ARMS_GROWTH since the newest arm row's commit — a heavier skill must still beat no skill; or the
    answer key or fixture changed since then, which makes the old baseline incomparable.
    EGM (tests/EGM.md): a doctrine document changed by EGM_MIN_LINES or more since its newest EGM
    row, or since BASELINE for a document never reviewed.

The trap: diffs are taken against the working tree, not HEAD, so an edit that is not committed yet
already counts. Running this after the commit would still work; running it before is the point.
"""
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ARMS = REPO / "tests" / "ARMS.md"
EGM = REPO / "tests" / "EGM.md"
DOCTRINE = ["SKILL.md", "references"]
KEY_PATHS = ["tests/EXPECTED-fixture-service.md", "tests/fixture-service"]
ARMS_GROWTH = 0.10
EGM_MIN_LINES = 20
# Documents untouched since this commit are not due. The ones never reviewed before it are a
# backlog, named in tests/EGM.md, not hidden: reviewing all of them at once is the token spend this
# script exists to ration.
BASELINE = "23d0128"


# ---- pure: no git, no files ------------------------------------------------------------------

def table_rows(text):
    """Cells of every data row (a row whose first cell is a date) in the markdown tables of text."""
    rows = []
    for line in text.splitlines():
        if re.match(r"^\|\s*\d{4}-\d{2}-\d{2}\s*\|", line):
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
    return rows


def commit_of(cell):
    m = re.search(r"\b[0-9a-f]{7,40}\b", cell)
    return m.group(0) if m else None


def newest_arm_commit(rows):
    """Commit cell (column 2) of the last arm row, or None."""
    return commit_of(rows[-1][1]) if rows else None


def reviewed_at(rows):
    """{document: commit of its newest EGM row}; columns: date, commit, document, ..."""
    out = {}
    for r in rows:
        c = commit_of(r[1])
        if c and len(r) > 2:
            out[r[2].strip("`")] = c
    return out


def arms_reasons(last_commit, size_then, size_now, key_changed):
    if last_commit is None:
        return ["no comparison arm has been run"]
    reasons = []
    if size_then and size_now >= size_then * (1 + ARMS_GROWTH):
        reasons.append(f"doctrine grew {round(100 * (size_now - size_then) / size_then)}% "
                       f"({size_then} -> {size_now} lines) since {last_commit}")
    if key_changed:
        reasons.append(f"the answer key or fixture changed since {last_commit}")
    return reasons


def egm_due(changed, threshold=EGM_MIN_LINES):
    """[(doc, lines changed)] at or over the threshold, most changed first."""
    return sorted(((d, n) for d, n in changed.items() if n >= threshold), key=lambda x: (-x[1], x[0]))


# ---- git: thin wrappers ----------------------------------------------------------------------

def git(*args):
    # UTF-8, not the console code page: keys and commit text carry non-ASCII, and cp950 crashed on them.
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True,
                          encoding="utf-8", errors="replace").stdout


def numstat(rev, *paths):
    """{path: (added, removed)} between rev and the working tree."""
    out = {}
    for line in git("diff", "--numstat", rev, "--", *paths).splitlines():
        a, r, p = line.split("\t", 2)
        if a != "-":
            out[p] = (int(a), int(r))
    return out


PIN_MARKER = "<!-- site-pins (tools/check_key_lines.py) -->"


def key_text_changed(then: str, now: str) -> bool:
    """The scored part of a key (above its site pins), compared without line endings."""
    def body(text):
        return text.split(PIN_MARKER)[0].replace("\r\n", "\n").strip()
    return body(then) != body(now)


def scored_key_changed(rev):
    """Did anything an arm is scored against change: the key above its site pins, or the fixture's code?

    A re-pin rewrites only digests below the marker, and a line-ending change rewrites no content;
    counting either made the arms due on 2026-11-09 for a change no arm could score differently."""
    for path in KEY_PATHS:
        if path.endswith(".md"):
            if key_text_changed(git("show", f"{rev}:{path}"), (REPO / path).read_text(encoding="utf-8")):
                return True
        elif git("diff", "--ignore-cr-at-eol", "--stat", rev, "--", path):
            return True
    return False


def doctrine_files():
    files = [REPO / "SKILL.md"] + sorted((REPO / "references").rglob("*.md"))
    return [f for f in files if f.is_file()]


def main():
    lines = []
    size_now = sum(len(f.read_text(encoding="utf-8").splitlines()) for f in doctrine_files())

    arm_rows = table_rows(ARMS.read_text(encoding="utf-8")) if ARMS.exists() else []
    last = newest_arm_commit(arm_rows)
    size_then, key_changed = None, False
    if last:
        diff = numstat(last, *DOCTRINE)
        size_then = size_now - sum(a for a, _ in diff.values()) + sum(r for _, r in diff.values())
        key_changed = scored_key_changed(last)
    for reason in arms_reasons(last, size_then, size_now, key_changed):
        lines.append(f"ARMS due: {reason}\n  python tests/harness/cold_run.py --mode audit --arm none --model sonnet   (twice)"
                     f"\n  python tests/harness/cold_run.py --mode audit --arm ponytail --model sonnet   (twice)")

    seen = reviewed_at(table_rows(EGM.read_text(encoding="utf-8")) if EGM.exists() else [])
    changed = {}
    for f in doctrine_files():
        rel = f.relative_to(REPO).as_posix()
        stat = numstat(seen.get(rel, BASELINE), rel)
        changed[rel] = sum(a + r for a, r in stat.values())
    for doc, n in egm_due(changed):
        since = seen.get(doc, BASELINE)
        lines.append(f"EGM due: {doc} changed {n} lines since {since}\n"
                     f"  python tests/harness/cold_run.py --mode egm --doc {doc} --reviewer comprehension --model sonnet")

    print("\n".join(lines) if lines else "nothing due")
    print("Record arm rows in tests/ARMS.md and reviews in tests/EGM.md (RUNBOOK step 7).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
