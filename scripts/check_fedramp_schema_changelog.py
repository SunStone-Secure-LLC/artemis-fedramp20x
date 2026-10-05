#!/usr/bin/env python3
"""Watch the FedRAMP schemas CHANGELOG for releases of the schema this repo validates against.

Fetches https://github.com/FedRAMP/schemas/blob/main/CHANGELOG.md, parses its
per-release headings, keeps the entries whose schema file matches a glob
(default: fedramp-certification-package-overview-schema*), and files one GitHub
issue per new entry in this repository. The default glob covers both new
versions of the schema file we validate against today and any dated successor
file (for example ``...-schema-2027-01-01.json``) FedRAMP releases later.

Each issue carries a hidden marker comment keyed on ``<schema file>@<version>``;
on later runs an entry whose marker already appears in an existing issue (open
or closed) is skipped, so the check is idempotent and safe to run daily.

The schema file currently validated against is read from ``SCHEMA_URL`` in the
publish workflow, so an entry for a *different* file can be called out as a
likely successor that needs ``SCHEMA_URL`` and ``$schema`` updated.

The run exits non-zero when the CHANGELOG format can no longer be trusted (no
release headings parse, or a heading naming a watched schema does not parse), so
a format change fails loudly instead of silently disabling the watch.

Requires the ``gh`` CLI, authenticated with a token that can read and create
issues in the target repository (GITHUB_TOKEN inside Actions).
"""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import json
import os
import re
import subprocess
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

CHANGELOG_RAW_URL = "https://raw.githubusercontent.com/FedRAMP/schemas/main/CHANGELOG.md"
CHANGELOG_HTML_URL = "https://github.com/FedRAMP/schemas/blob/main/CHANGELOG.md"
SCHEMA_REPO_BLOB_URL = "https://github.com/FedRAMP/schemas/blob/main/{file}"
SCHEMA_PUBLISHED_URL = "https://www.fedramp.gov/schemas/{file}"

DEFAULT_PATTERN = "fedramp-certification-package-overview-schema*"
DEFAULT_LABEL = "fedramp-schema-watch"
DEFAULT_PUBLISH_WORKFLOW_NAME = "Publish FedRAMP Certification Package Overview"
DEFAULT_PUBLISH_WORKFLOW_FILE = (
    ".github/workflows/publish-fedramp-certification-package-overview.yml"
)

MARKER_PREFIX = "fedramp-schema-watch:"
MARKER_RE = re.compile(r"<!--\s*fedramp-schema-watch:\s*(?P<key>\S+)\s*-->")

# "## 2026-08-11 — fedramp-advisor-information-schema-2026-06-24.json → 1.0.1 (patch)"
HEADING_RE = re.compile(
    r"^##\s+(?P<date>\d{4}-\d{2}-\d{2})\s+[—–-]+\s+"
    r"(?P<file>\S+\.json)\s+(?:→|->)\s+(?P<version>\S+)\s+\((?P<bump>[a-z]+)\)\s*$"
)
SCHEMA_FILE_TOKEN_RE = re.compile(r"[\w.-]+\.json")
# "  SCHEMA_URL: https://www.fedramp.gov/schemas/<file>.json" in the publish workflow.
SCHEMA_URL_RE = re.compile(
    r"^\s*SCHEMA_URL:\s*\S*?/schemas/(?P<file>[^\s/]+\.json)\s*$", re.MULTILINE
)

# The last entry in the real CHANGELOG is followed by a long "prior history"
# section; cap what is quoted into an issue so a body can never run away.
MAX_QUOTED_BODY_CHARS = 3000


@dataclass
class ChangelogEntry:
    date: dt.date
    file: str
    version: str
    bump: str
    heading: str
    body: str

    @property
    def key(self) -> str:
        return f"{self.file}@{self.version}"

    @property
    def marker(self) -> str:
        return f"<!-- {MARKER_PREFIX} {self.key} -->"


def fetch_changelog(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "fedramp-schema-watch"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8")


def parse_changelog(markdown: str) -> tuple[list[ChangelogEntry], list[str]]:
    """Return ``(entries, unparsed)``.

    ``unparsed`` holds ``## `` headings that name a ``.json`` file but do not
    match the release format; non-release headings (e.g. "Baseline frozen") are
    expected and are not reported.
    """
    entries: list[ChangelogEntry] = []
    unparsed: list[str] = []
    current: ChangelogEntry | None = None
    body_lines: list[str] = []

    def flush() -> None:
        if current is not None:
            current.body = "\n".join(body_lines).strip()
            entries.append(current)

    for line in markdown.splitlines():
        if line.startswith("## "):
            flush()
            body_lines = []
            match = HEADING_RE.match(line)
            if match:
                current = ChangelogEntry(
                    date=dt.date.fromisoformat(match.group("date")),
                    file=match.group("file"),
                    version=match.group("version"),
                    bump=match.group("bump"),
                    heading=line[3:].strip(),
                    body="",
                )
            else:
                if ".json" in line:
                    unparsed.append(line)
                current = None
            continue
        if current is not None:
            body_lines.append(line)
    flush()
    return entries, unparsed


def unrecognized_for_pattern(unparsed: list[str], pattern: str) -> list[str]:
    """Unparsed headings that name a schema file we are watching."""
    return [
        heading
        for heading in unparsed
        if any(fnmatch.fnmatch(token, pattern) for token in SCHEMA_FILE_TOKEN_RE.findall(heading))
    ]


def version_key(version: str) -> tuple[tuple[int, int, str], ...]:
    """Sort key that orders ``0.1.9`` before ``0.1.10`` (a plain string sort does not)."""
    return tuple(
        (0, int(part), "") if part.isdigit() else (1, 0, part)
        for part in re.split(r"[.+-]", version)
    )


def select_entries(
    entries: list[ChangelogEntry], pattern: str, since: dt.date | None
) -> list[ChangelogEntry]:
    selected = [e for e in entries if fnmatch.fnmatch(e.file, pattern)]
    if since is not None:
        selected = [e for e in selected if e.date >= since]
    # Oldest first so issue numbers ascend chronologically.
    return sorted(selected, key=lambda e: (e.date, e.file, version_key(e.version)))


def current_schema_file(workflow_path: Path) -> str | None:
    """File name of the schema the publish workflow validates against, if readable."""
    try:
        text = workflow_path.read_text(encoding="utf-8")
    except OSError:
        return None
    match = SCHEMA_URL_RE.search(text)
    return match.group("file") if match else None


def run_gh(args: list[str], repo: str) -> str:
    command = ["gh", *args, "--repo", repo]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"gh {' '.join(args)} failed ({result.returncode}):\n{result.stderr.strip()}"
        )
    return result.stdout


def existing_keys(repo: str, label: str) -> set[str]:
    output = run_gh(
        [
            "issue",
            "list",
            "--label",
            label,
            "--state",
            "all",
            "--limit",
            "500",
            "--json",
            "body",
        ],
        repo,
    )
    keys: set[str] = set()
    for issue in json.loads(output or "[]"):
        for match in MARKER_RE.finditer(issue.get("body") or ""):
            keys.add(match.group("key"))
    return keys


def ensure_label(repo: str, label: str) -> None:
    run_gh(
        [
            "label",
            "create",
            label,
            "--description",
            "Automated notice of a FedRAMP schema CHANGELOG entry that affects this repo",
            "--color",
            "D93F0B",
            "--force",
        ],
        repo,
    )


def issue_title(entry: ChangelogEntry) -> str:
    return f"FedRAMP schema change: {entry.file} → {entry.version} ({entry.bump}) [{entry.date}]"


def quote_body(body: str) -> str:
    if len(body) > MAX_QUOTED_BODY_CHARS:
        body = body[:MAX_QUOTED_BODY_CHARS].rstrip() + "\n\n… (truncated; see the CHANGELOG link below)"
    return "\n".join(f"> {line}" if line else ">" for line in body.splitlines())


def issue_body(
    entry: ChangelogEntry,
    publish_workflow_name: str,
    current_file: str | None = None,
    publish_workflow_file: str = DEFAULT_PUBLISH_WORKFLOW_FILE,
) -> str:
    is_other_file = bool(current_file) and entry.file != current_file

    notices = ""
    if entry.bump == "major":
        notices += (
            "> **Warning:** this is a major version bump. Documents published against the "
            "previous version are likely invalid until they are updated.\n\n"
        )
    if is_other_file:
        notices += (
            f"> **Note:** this entry is for `{entry.file}`, not `{current_file}`, the schema "
            f"this repository currently validates against. If it is a successor, this repository "
            f"must move to it; re-running the publish workflow alone will keep validating "
            f"against `{current_file}` and can pass misleadingly.\n\n"
        )

    if is_other_file:
        steps = f"""1. Read the entry above and decide whether `{entry.file}` supersedes `{current_file}`.
2. If it does, update `SCHEMA_URL` in `{publish_workflow_file}` and the `$schema` value in the `FEDRAMP_20X_SOURCE_OF_TRUTH` block of `README.md` to `{entry.file}`. If the schema was renamed rather than re-dated, also update `SCHEMA_FILE_PATTERN` in `.github/workflows/watch-fedramp-schema-changelog.yml`.
3. Update `README.md` metadata or `scripts/build_fedramp_certification_package_overview.py` for any changed requirements.
4. Run the **{publish_workflow_name}** workflow (workflow_dispatch). It validates the generated JSON against `SCHEMA_URL` and fails if the schema rejects it.
5. Close this issue once the published JSON validates against `{entry.file}` {entry.version}, or once you have decided it does not apply."""
    else:
        steps = f"""1. Read the entry above and decide whether `README.md` metadata or `scripts/build_fedramp_certification_package_overview.py` need to change.
2. Confirm the published schema is at `{entry.version}`: `curl -fsS {SCHEMA_PUBLISHED_URL.format(file=entry.file)} | jq -r '."$schemaVersion"'`. The CHANGELOG can land before the published copy updates, and validating against the old copy would pass misleadingly.
3. Re-run the **{publish_workflow_name}** workflow (workflow_dispatch). It validates the generated JSON against the live schema and fails if the new version rejects it.
4. Close this issue once the published JSON validates against `{entry.version}`."""

    return f"""{entry.marker}
The FedRAMP schemas CHANGELOG recorded a new release of a schema this repository publishes against.

{notices}## CHANGELOG entry

> ### {entry.heading}
>
{quote_body(entry.body)}

Source: [CHANGELOG.md]({CHANGELOG_HTML_URL})

## Schema

- Repository copy: {SCHEMA_REPO_BLOB_URL.format(file=entry.file)}
- Published copy: {SCHEMA_PUBLISHED_URL.format(file=entry.file)}

## Next steps

{steps}

_Filed automatically by the FedRAMP schema CHANGELOG watch workflow._
"""


def create_issue(
    repo: str,
    entry: ChangelogEntry,
    label: str,
    assignee: str,
    publish_workflow_name: str,
    current_file: str | None,
    publish_workflow_file: str,
) -> str:
    args = [
        "issue",
        "create",
        "--title",
        issue_title(entry),
        "--body",
        issue_body(entry, publish_workflow_name, current_file, publish_workflow_file),
        "--label",
        label,
    ]
    if assignee:
        args += ["--assignee", assignee]
    return run_gh(args, repo).strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        default=os.environ.get("GITHUB_REPOSITORY", ""),
        help="owner/name of the repository to file issues in",
    )
    parser.add_argument(
        "--pattern",
        default=os.environ.get("SCHEMA_FILE_PATTERN", DEFAULT_PATTERN),
        help="fnmatch glob applied to the schema file name in each CHANGELOG heading",
    )
    parser.add_argument(
        "--since",
        default=os.environ.get("WATCH_SINCE") or None,
        help="ignore CHANGELOG entries dated before this ISO date (baseline)",
    )
    parser.add_argument("--label", default=os.environ.get("ISSUE_LABEL", DEFAULT_LABEL))
    parser.add_argument("--assignee", default=os.environ.get("ISSUE_ASSIGNEE", ""))
    parser.add_argument(
        "--publish-workflow-name",
        default=os.environ.get("PUBLISH_WORKFLOW_NAME", DEFAULT_PUBLISH_WORKFLOW_NAME),
        help="display name of the publish workflow, quoted in the issue's next steps",
    )
    parser.add_argument(
        "--publish-workflow-file",
        default=os.environ.get("PUBLISH_WORKFLOW_FILE", DEFAULT_PUBLISH_WORKFLOW_FILE),
        help="publish workflow whose SCHEMA_URL names the schema file validated against today",
    )
    parser.add_argument(
        "--changelog",
        type=Path,
        help="read the CHANGELOG from a local file instead of fetching it (testing)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report what would be filed without creating labels or issues",
    )
    args = parser.parse_args(argv)

    if not args.repo:
        parser.error("--repo is required (or set GITHUB_REPOSITORY)")
    since = dt.date.fromisoformat(args.since) if args.since else None

    markdown = (
        args.changelog.read_text(encoding="utf-8")
        if args.changelog
        else fetch_changelog(CHANGELOG_RAW_URL)
    )
    entries, unparsed = parse_changelog(markdown)
    if not entries:
        print(
            "::error::No release headings could be parsed from the FedRAMP schemas CHANGELOG; "
            "its format may have changed, so this watch cannot be trusted until it is updated."
        )
        return 1

    exit_code = 0
    for heading in unrecognized_for_pattern(unparsed, args.pattern):
        print(
            f"::error::CHANGELOG heading names a watched schema but does not match the "
            f"release format, so it was not checked: {heading}"
        )
        exit_code = 1

    current_file = current_schema_file(Path(args.publish_workflow_file))
    if current_file is None:
        print(
            f"::warning::Could not read SCHEMA_URL from {args.publish_workflow_file}; "
            "entries for other schema files will not be flagged as possible successors."
        )

    matching = select_entries(entries, args.pattern, since)
    print(
        f"Parsed {len(entries)} CHANGELOG entries; {len(matching)} match "
        f"'{args.pattern}'"
        + (f" on/after {since}" if since else "")
        + (f"; validating against {current_file}" if current_file else "")
    )

    known = existing_keys(args.repo, args.label)
    new_entries = [e for e in matching if e.key not in known]
    for entry in matching:
        status = "new" if entry in new_entries else "already filed"
        print(f"  - {entry.key} ({entry.date}, {entry.bump}): {status}")

    if not new_entries:
        print("No new CHANGELOG entries to file.")
        return exit_code

    if args.dry_run:
        print(f"Dry run: would file {len(new_entries)} issue(s).")
        for entry in new_entries:
            print("\n" + "=" * 72)
            print(issue_title(entry))
            print("-" * 72)
            print(
                issue_body(
                    entry,
                    args.publish_workflow_name,
                    current_file,
                    args.publish_workflow_file,
                )
            )
        return exit_code

    ensure_label(args.repo, args.label)
    for entry in new_entries:
        url = create_issue(
            args.repo,
            entry,
            args.label,
            args.assignee,
            args.publish_workflow_name,
            current_file,
            args.publish_workflow_file,
        )
        print(f"Filed {url} for {entry.key}")

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as summary:
            summary.write(
                f"Filed {len(new_entries)} FedRAMP schema change issue(s): "
                + ", ".join(e.key for e in new_entries)
                + "\n"
            )
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
