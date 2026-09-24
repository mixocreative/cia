"""Fail loudly when a fixture moves under its own answer key.

## Why this exists

`EXPECTED-fixture-service.md` grades a run by whether its `path:line` falls inside a cited range.
On 2026-09-25 three of those ranges were stale by twenty lines, because the fixture had grown and
the key had not. Nothing said so. A run reporting the race at `runner/scheduler.py:68` - which is
where the race actually is - would have been scored a MISS against a key still pointing at 48-63,
and the regression would have been recorded against whatever doctrine change happened to be under
test that day.

That is the fixture harness committing the doctrine's own S21 shape 14, the vacuous failure: an
instrument reporting red for a reason that is not a reason. The fix is the one the peer session
proved for a different guard on the same day - **a stale pin makes the check red rather than
silently permissive** - so this refuses to pass rather than quietly grading against fiction.

## What it checks

Every `path:line` and `path:line-line` citation anywhere in the key resolves: the file exists, and
the line numbers are within it. That is deliberately weaker than "the defect is still on that
line", which no checker can know, and deliberately stronger than nothing - a file that shrinks or
disappears under its key is the common case and it is caught.

Beyond that, it pins the sha256 of every file the key cites. A cited file that changed content
means the ranges must be re-read by a person; the checker says which files and stops. Re-pin with
`--repin` after checking the ranges by hand, never as a reflex.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEYS = {
    "tests/EXPECTED-fixture-service.md": "tests/fixture-service",
}
PIN_MARKER = "<!-- site-pins (tools/check_key_lines.py) -->"

CITATION = re.compile(r"`([A-Za-z0-9_./-]+\.(?:py|js|yaml|yml|json|md)):(\d+)(?:-(\d+))?")


def pins_from(text: str) -> dict[str, str]:
    block = text.split(PIN_MARKER)
    if len(block) < 2:
        return {}
    return dict(
        re.findall(r"^-\s+`([^`]+)`\s+([0-9a-f]{64})$", block[1], re.MULTILINE)
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repin", action="store_true", help="rewrite the pins after a human re-read")
    args = parser.parse_args()

    failures: list[str] = []

    for key_rel, fixture_rel in KEYS.items():
        key_path = ROOT / key_rel
        fixture = ROOT / fixture_rel
        text = key_path.read_text(encoding="utf-8")
        recorded = pins_from(text)
        seen: dict[str, str] = {}

        for rel, start, end in CITATION.findall(text):
            target = fixture / rel
            if not target.is_file():
                failures.append(f"{key_rel}: cites `{rel}` which does not exist under {fixture_rel}/")
                continue

            lines = len(target.read_text(encoding="utf-8").splitlines())
            for label, number in (("start", start), ("end", end)):
                if number and int(number) > lines:
                    failures.append(
                        f"{key_rel}: `{rel}:{number}` is past the end of the file ({lines} lines) "
                        f"- the key's {label} of a range has drifted"
                    )

            seen[rel] = hashlib.sha256(target.read_bytes()).hexdigest()

        for rel, digest in sorted(seen.items()):
            if rel not in recorded:
                failures.append(f"{key_rel}: `{rel}` is cited but not pinned - run --repin once the ranges are read")
            elif recorded[rel] != digest:
                failures.append(
                    f"{key_rel}: `{rel}` has changed since its ranges were last read by a person. "
                    f"Re-read every citation into it, then --repin."
                )

        if args.repin:
            body = text.split(PIN_MARKER)[0].rstrip()
            pinned = "\n".join(f"- `{rel}` {digest}" for rel, digest in sorted(seen.items()))
            key_path.write_text(
                f"{body}\n\n{PIN_MARKER}\n\n## Site pins\n\n"
                "Every file this key cites, with the sha256 it had when a person last read the "
                "ranges against it. A changed digest fails `tools/check_key_lines.py` — re-read, "
                "then re-pin.\n\n"
                f"{pinned}\n",
                encoding="utf-8",
                newline="\n",
            )
            print(f"{key_rel}: pinned {len(seen)} cited files")
            return 0

    if failures:
        print("key-line check FAILED:")
        for line in failures:
            print(f"  - {line}")
        return 1

    print(f"key lines: every citation resolves and every cited file matches its pin")
    return 0


if __name__ == "__main__":
    sys.exit(main())
