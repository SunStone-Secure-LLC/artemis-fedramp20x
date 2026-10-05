"""Step definitions for schema_changelog_watch.feature.

Each scenario runs the real scripts/check_fedramp_schema_changelog.py in a
subprocess, with a stand-in `gh` (tests/support/fake_gh.py) first on PATH.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

from behave import given, then, when

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "check_fedramp_schema_changelog.py"
REPO = "SunStone-Secure-LLC/artemis-fedramp20x"

SCHEMA_PREFIXES = {
    "overview": "fedramp-certification-package-overview-schema",
    "advisor": "fedramp-advisor-information-schema",
}


def schema_file(name: str, date: str) -> str:
    return f"{SCHEMA_PREFIXES[name]}-{date}.json"


def marker_for(date: str, version: str) -> str:
    return f"<!-- fedramp-schema-watch: {schema_file('overview', date)}@{version} -->"


def gh_state(context) -> dict:
    if not context.gh_state_path.exists():
        return {"issues": [], "labels": [], "calls": []}
    return json.loads(context.gh_state_path.read_text(encoding="utf-8"))


def save_gh_state(context, state: dict) -> None:
    context.gh_state_path.write_text(json.dumps(state), encoding="utf-8")


def find_issue(context, date: str, version: str) -> dict:
    marker = marker_for(date, version)
    matches = [i for i in gh_state(context)["issues"] if marker in i["body"]]
    assert len(matches) == 1, (
        f"expected exactly one issue for overview schema {date} version {version}, "
        f"found {len(matches)}; issues: {[i['title'] for i in gh_state(context)['issues']]}"
    )
    return matches[0]


def run_watch(context, *extra: str) -> None:
    changelog = context.workdir / "CHANGELOG.md"
    changelog.write_text(
        "# Changelog\n\n" + "".join(context.changelog_sections), encoding="utf-8"
    )
    argv = [
        sys.executable,
        str(SCRIPT),
        "--repo", REPO,
        "--changelog", str(changelog),
        "--publish-workflow-file", str(context.publish_workflow),
        "--assignee", context.assignee,
        *extra,
    ]  # fmt: skip
    if context.since:
        argv += ["--since", context.since]

    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"WATCH_SINCE", "SCHEMA_FILE_PATTERN", "ISSUE_LABEL", "GITHUB_STEP_SUMMARY"}
    }
    env["PATH"] = f"{context.bin_dir}{os.pathsep}{env.get('PATH', '')}"
    env["FAKE_GH_STATE"] = str(context.gh_state_path)

    completed = subprocess.run(argv, capture_output=True, text=True, env=env)
    context.result = completed
    context.output = completed.stdout + completed.stderr


# --- Given -----------------------------------------------------------------


@given("the repository validates against the overview schema dated {date}")
def step_repository_schema(context, date):
    context.publish_workflow = context.workdir / "publish.yml"
    context.publish_workflow.write_text(
        "env:\n"
        f"  SCHEMA_URL: https://www.fedramp.gov/schemas/{schema_file('overview', date)}\n",
        encoding="utf-8",
    )


@given('the watch is configured to assign issues to "{assignee}"')
def step_assignee(context, assignee):
    context.assignee = assignee


@given("the watch baseline is {since}")
def step_baseline(context, since):
    context.since = since


@given("the upstream CHANGELOG lists these releases:")
def step_changelog_releases(context):
    for row in context.table:
        name, schema_date = row["schema"].split()
        context.changelog_sections.append(
            f"## {row['date']} — {schema_file(name, schema_date)} → {row['version']} "
            f"({row['bump']})\n\n{row['note']}\n\n"
        )


@given('the upstream CHANGELOG has the heading "{heading}"')
def step_changelog_heading(context, heading):
    context.changelog_sections.append(f"{heading}\n\nBody.\n\n")


@given("the upstream CHANGELOG has no release entries")
def step_changelog_empty(context):
    context.changelog_sections = ["Nothing has been released yet.\n"]


@given(
    'an issue labeled "{label}" already records overview schema {date} version {version}'
)
def step_existing_issue(context, label, date, version):
    state = gh_state(context)
    state["issues"].append(
        {
            "number": len(state["issues"]) + 1,
            "title": "earlier notice",
            "body": marker_for(date, version) + "\nFiled earlier.",
            "labels": [label],
            "assignee": None,
        }
    )
    save_gh_state(context, state)


# --- When ------------------------------------------------------------------


@when("the watch runs")
def step_run(context):
    run_watch(context)


@when("the watch runs again")
def step_run_again(context):
    run_watch(context)


@when("the watch runs in dry-run mode")
def step_run_dry(context):
    run_watch(context, "--dry-run")


# --- Then ------------------------------------------------------------------


@then("the run succeeds")
def step_succeeds(context):
    assert context.result.returncode == 0, (
        f"exit {context.result.returncode}\n{context.output}"
    )


@then("the run fails")
def step_fails(context):
    assert context.result.returncode != 0, f"expected failure\n{context.output}"


@then('the run reports "{text}"')
def step_reports(context, text):
    assert text in context.output, f"{text!r} not in output:\n{context.output}"


@then("no issues exist")
def step_no_issues(context):
    assert gh_state(context)["issues"] == [], gh_state(context)["issues"]


@then("{count:d} issue exists")
@then("{count:d} issues exist")
def step_issue_count(context, count):
    issues = gh_state(context)["issues"]
    assert len(issues) == count, f"expected {count} issue(s), found {len(issues)}: {issues}"


@then('the label "{label}" was not created')
def step_label_not_created(context, label):
    assert label not in gh_state(context)["labels"]


@then(
    'the issue for overview schema {date} version {version} is labeled "{label}" '
    'and assigned to "{assignee}"'
)
def step_issue_label_assignee(context, date, version, label, assignee):
    issue = find_issue(context, date, version)
    assert label in issue["labels"], issue["labels"]
    assert issue["assignee"] == assignee, issue["assignee"]
    assert label in gh_state(context)["labels"], "label was never ensured to exist"


@then('the issue for overview schema {date} version {version} quotes "{text}"')
def step_issue_quotes(context, date, version, text):
    body = find_issue(context, date, version)["body"]
    assert f"> {text}" in body, body


@then(
    'the issue for overview schema {date} version {version} tells the maintainer '
    'to re-run the "{workflow}" workflow'
)
def step_issue_rerun(context, date, version, workflow):
    body = find_issue(context, date, version)["body"]
    assert f"Re-run the **{workflow}** workflow" in body, body


@then(
    "the issue for overview schema {date} version {version} tells the maintainer "
    "to update SCHEMA_URL"
)
def step_issue_update_schema_url(context, date, version):
    body = find_issue(context, date, version)["body"]
    assert "update `SCHEMA_URL`" in body, body


@then(
    "the issue for overview schema {date} version {version} does not tell the "
    "maintainer to update SCHEMA_URL"
)
def step_issue_no_schema_url(context, date, version):
    body = find_issue(context, date, version)["body"]
    assert "SCHEMA_URL" not in body, body


@then("the issue for overview schema {date} version {version} warns of a major version bump")
def step_issue_major(context, date, version):
    body = find_issue(context, date, version)["body"]
    assert "major version bump" in body, body


@then("the issues were filed for these versions in order:")
def step_issue_order(context):
    expected = [row["version"] for row in context.table]
    actual = []
    for issue in gh_state(context)["issues"]:
        # The marker is "<file>@<version> -->"; the version is what follows the "@".
        marker = issue["body"].splitlines()[0]
        actual.append(marker.split("@", 1)[1].split()[0])
    assert actual == expected, f"expected {expected}, filed {actual}"
