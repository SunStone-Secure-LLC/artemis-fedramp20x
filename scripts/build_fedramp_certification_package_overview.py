#!/usr/bin/env python3
"""Extract the FedRAMP package overview JSON embedded in README.md."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


START_MARKER = "<!-- FEDRAMP_20X_SOURCE_OF_TRUTH_BEGIN\n"
END_MARKER = "\nFEDRAMP_20X_SOURCE_OF_TRUTH_END -->"


def extract_package_overview(readme_path: Path) -> dict:
    text = readme_path.read_text(encoding="utf-8")

    try:
        payload = text.split(START_MARKER, 1)[1].split(END_MARKER, 1)[0]
    except IndexError as exc:
        raise SystemExit(
            f"Could not find FedRAMP source-of-truth markers in {readme_path}"
        ) from exc

    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Embedded FedRAMP JSON is invalid: {exc}") from exc

    if not isinstance(data, dict):
        raise SystemExit("Embedded FedRAMP JSON must be a JSON object")

    return data


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract FedRAMP certification package overview JSON from README.md."
    )
    parser.add_argument(
        "--readme",
        type=Path,
        default=Path("README.md"),
        help="Path to README.md containing the embedded source-of-truth JSON.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("dist/fedramp-certification-package-overview.json"),
        help="Path to write the extracted JSON artifact.",
    )
    args = parser.parse_args()

    data = extract_package_overview(args.readme)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
