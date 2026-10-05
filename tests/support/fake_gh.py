#!/usr/bin/env python3
"""Stand-in for the ``gh`` CLI, used by the BDD acceptance tests only.

Supports just the calls scripts/check_fedramp_schema_changelog.py makes:
``issue list``, ``issue create`` and ``label create``. State (issues, labels and
every call received) persists in the JSON file named by $FAKE_GH_STATE, so a
scenario can run the watch more than once against the same "repository".
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

STATE_PATH = Path(os.environ["FAKE_GH_STATE"])


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"issues": [], "labels": [], "calls": []}


def values(argv: list[str], flag: str) -> list[str]:
    return [argv[i + 1] for i, arg in enumerate(argv) if arg == flag and i + 1 < len(argv)]


def main(argv: list[str]) -> int:
    state = load_state()
    state["calls"].append(argv)
    command = argv[:2]
    output = ""

    if command == ["issue", "list"]:
        labels = values(argv, "--label")
        output = json.dumps(
            [
                {"body": issue["body"]}
                for issue in state["issues"]
                if all(label in issue["labels"] for label in labels)
            ]
        )
    elif command == ["issue", "create"]:
        number = len(state["issues"]) + 1
        assignees = values(argv, "--assignee")
        state["issues"].append(
            {
                "number": number,
                "title": values(argv, "--title")[0],
                "body": values(argv, "--body")[0],
                "labels": values(argv, "--label"),
                "assignee": assignees[0] if assignees else None,
            }
        )
        output = f"https://github.com/{values(argv, '--repo')[0]}/issues/{number}"
    elif command == ["label", "create"]:
        state["labels"].append(argv[2])
    else:
        print(f"fake gh: unsupported command: {argv}", file=sys.stderr)
        STATE_PATH.write_text(json.dumps(state), encoding="utf-8")
        return 2

    STATE_PATH.write_text(json.dumps(state), encoding="utf-8")
    if output:
        print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
