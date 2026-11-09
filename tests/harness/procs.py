"""Processes a harness run starts: list them, attribute the ones left behind, stop only its own.

Split out of cold_run.py on 2026-11-10 (the file passed 600 lines): this is one job, and its input
(snapshots, a copy path, a PID tree) is wider than its output (which PIDs to stop).
"""
from __future__ import annotations

import json
import os
import subprocess
import threading


# Processes a run leaves behind. Added 2026-11-09: Codex runs C1-C7 each left a `graphify watch`
# running after `codex exec` returned, seven found at once, parents gone. The harness reports every one
# and stops only its own (owned_by_run, approved by the owner 2026-11-10); the rest are the owner's
# call. A failed snapshot is
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


def descendants(procs, roots):
    """{pid: cmd} of every process in one snapshot that descends from `roots` (the roots excluded).

    Trap: Windows reuses PIDs, so a process whose parent died can point at a reused PID; that is why
    ownership also compares the command line (owned_by_run), never the PID alone."""
    kids = {}
    for p in procs:
        kids.setdefault(p["ppid"], []).append(p)
    out, todo = {}, list(roots)
    while todo:
        for p in kids.get(todo.pop(), []):
            if p["pid"] not in out and p["pid"] not in roots:
                out[p["pid"]] = p["cmd"]
                todo.append(p["pid"])
    return out


def owned_by_run(left, copy_dir, seen=None):
    """The leftovers that are certainly this run's: their command line names its own throwaway copy, or
    the process was seen descending from the run's agent with the same command line (`seen`, from
    run_watched).

    Only these are stopped (the owner approved this on 2026-11-10). Codex obeys a user's global
    AGENTS.md, and one that says "keep a graphify watch running per project" started a watcher in every
    copy and left it running. The copy-name rule alone missed `graphify watch runner` (a relative path,
    run 2026-11-10 C16/C17), hence the tree. An orphan neither rule claims may be a parallel run's or the
    user's own, so it stays a report: stopping what cannot be attributed would be the fail-open this
    skill audits for."""
    seen = seen or {}
    return [p for p in left if (copy_dir and copy_dir.lower() in p["cmd"].lower())
            or seen.get(p["pid"]) == p["cmd"]]


POLL_S = 5   # a watcher's parent shell lives seconds; slower polling loses the link to the run


def run_watched(argv, cwd, prompt, timeout):
    """Run the agent like subprocess.run, and return (result, {pid: cmd} of every process seen
    descending from it while it ran). A failed listing only loses attribution, never the run."""
    proc = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, encoding="utf-8")
    box = {}

    def talk():
        try:
            box["out"] = proc.communicate(prompt, timeout=timeout)
        except subprocess.TimeoutExpired as e:   # same contract as subprocess.run: kill, then raise
            proc.kill()
            proc.communicate()
            box["timeout"] = e

    t = threading.Thread(target=talk, daemon=True)
    t.start()
    seen = {}
    while t.is_alive():
        snap = list_processes()
        if snap:
            seen.update(descendants(snap, {proc.pid} | set(seen)))
        t.join(POLL_S)
    if "timeout" in box:
        raise box["timeout"]
    out, err = box["out"]
    return subprocess.CompletedProcess(argv, proc.returncode, out, err), seen


def stop(pids):
    """Stop each process and its children; returns the PIDs the OS reported as stopped."""
    done = []
    for pid in pids:
        cmd = ["taskkill", "/PID", str(pid), "/T", "/F"] if os.name == "nt" else ["kill", "-TERM", str(pid)]
        if subprocess.run(cmd, capture_output=True).returncode == 0:
            done.append(pid)
    return done
