import contextlib
import datetime as dt
import fnmatch
import io
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import check_fedramp_schema_changelog as watch  # noqa: E402

OVERVIEW = "fedramp-certification-package-overview-schema-2026-06-24.json"
SUCCESSOR = "fedramp-certification-package-overview-schema-2027-01-01.json"
ADVISOR = "fedramp-advisor-information-schema-2026-06-24.json"
PUBLISH_WORKFLOW_NAME = "Publish FedRAMP Certification Package Overview"

# Shaped like the real https://github.com/FedRAMP/schemas CHANGELOG: newest first,
# a bulleted multi-line body, a major bump, and a trailing "###" section that the
# parser attaches to the last release entry.
SAMPLE_CHANGELOG = f"""# Changelog

All notable changes to the FedRAMP CR26 JSON Schemas are documented in this file.

## 2026-09-23 — {OVERVIEW} → 0.1.6 (patch)

Reformat schemas with prettier (was 0.1.5).

## 2026-09-23 — {ADVISOR} → 2.0.0 (major)

Replace contactInformation string array with the shared object (was 1.0.1).

## 2026-09-23 — {OVERVIEW} → 0.1.5 (patch)

Add optional 'advisors' array to FRC-CSO-PKG schema. (was 0.1.4).

## 2026-08-11 — {OVERVIEW} → 0.1.10 (minor)

Add four fields:

- `alpha` — first.
- `beta` — second.

**Breaking:** none.

## 2026-07-14 — {OVERVIEW} → 0.1.1 (patch)

Initial fix (was 0.1.0).

### Prior history (pre-versioning), summarized

- **Origins.** Two files.
"""


def entry(
    version="0.1.7",
    file=OVERVIEW,
    bump="patch",
    date="2026-10-01",
    body="Tighten a pattern (was 0.1.6).",
):
    return watch.ChangelogEntry(
        date=dt.date.fromisoformat(date),
        file=file,
        version=version,
        bump=bump,
        heading=f"{date} — {file} → {version} ({bump})",
        body=body,
    )


class ParseChangelogTests(unittest.TestCase):
    def setUp(self):
        self.entries, self.unparsed = watch.parse_changelog(SAMPLE_CHANGELOG)

    def test_parses_every_release_heading(self):
        self.assertEqual(
            [(e.file, e.version, e.bump) for e in self.entries],
            [
                (OVERVIEW, "0.1.6", "patch"),
                (ADVISOR, "2.0.0", "major"),
                (OVERVIEW, "0.1.5", "patch"),
                (OVERVIEW, "0.1.10", "minor"),
                (OVERVIEW, "0.1.1", "patch"),
            ],
        )
        self.assertEqual(self.entries[0].date, dt.date(2026, 9, 23))
        self.assertEqual(self.unparsed, [])

    def test_keeps_multiline_bodies_including_bullets(self):
        body = self.entries[3].body
        self.assertIn("- `alpha` — first.", body)
        self.assertIn("**Breaking:** none.", body)
        self.assertTrue(body.startswith("Add four fields:"))

    def test_trailing_section_stays_in_last_entry_body(self):
        self.assertIn("### Prior history", self.entries[-1].body)

    def test_non_release_headings_are_ignored_silently(self):
        entries, unparsed = watch.parse_changelog(
            "## Baseline frozen\n\nNotes.\n\n"
            f"## 2026-01-01 — {OVERVIEW} → 0.1.0 (patch)\n\nBody.\n"
        )
        self.assertEqual([e.version for e in entries], ["0.1.0"])
        self.assertEqual(unparsed, [])
        self.assertNotIn("Notes.", entries[0].body)

    def test_heading_naming_a_schema_but_unparseable_is_reported(self):
        heading = f"## 2027-01-01 — {SUCCESSOR} released as 1.0.0"
        _, unparsed = watch.parse_changelog(f"{heading}\n\nBody.\n")
        self.assertEqual(unparsed, [heading])

    def test_accepts_hyphen_and_ascii_arrow_variants(self):
        entries, unparsed = watch.parse_changelog(
            f"## 2026-02-02 - {OVERVIEW} -> 0.2.0 (minor)\n\nBody.\n"
            f"## 2026-03-03 – {OVERVIEW} → 0.3.0 (minor)\n\nBody.\n"
        )
        self.assertEqual([e.version for e in entries], ["0.2.0", "0.3.0"])
        self.assertEqual(unparsed, [])

    def test_key_and_marker(self):
        e = entry()
        self.assertEqual(e.key, f"{OVERVIEW}@0.1.7")
        self.assertEqual(e.marker, f"<!-- fedramp-schema-watch: {OVERVIEW}@0.1.7 -->")
        self.assertEqual(watch.MARKER_RE.search(e.marker).group("key"), e.key)


class UnrecognizedHeadingTests(unittest.TestCase):
    def test_only_headings_for_watched_schemas_are_returned(self):
        unparsed = [
            f"## 2027-01-01 — {SUCCESSOR} released as 1.0.0",
            f"## 2027-01-01 — {ADVISOR} released as 3.0.0",
        ]
        self.assertEqual(
            watch.unrecognized_for_pattern(unparsed, watch.DEFAULT_PATTERN), [unparsed[0]]
        )


class SelectEntriesTests(unittest.TestCase):
    def test_glob_matches_current_file_and_dated_successor_but_not_other_schemas(self):
        entries = [entry(), entry(file=SUCCESSOR, version="1.0.0"), entry(file=ADVISOR)]
        selected = watch.select_entries(entries, watch.DEFAULT_PATTERN, None)
        self.assertEqual({e.file for e in selected}, {OVERVIEW, SUCCESSOR})

    def test_since_is_inclusive(self):
        entries = [
            entry(version="0.1.5", date="2026-09-23"),
            entry(version="0.1.6", date="2026-09-24"),
            entry(version="0.1.7", date="2026-09-25"),
        ]
        selected = watch.select_entries(entries, watch.DEFAULT_PATTERN, dt.date(2026, 9, 24))
        self.assertEqual([e.version for e in selected], ["0.1.6", "0.1.7"])

    def test_orders_oldest_first_and_versions_numerically(self):
        entries = [
            entry(version="0.1.10", date="2026-10-01"),
            entry(version="0.1.9", date="2026-10-01"),
            entry(version="0.1.8", date="2026-09-30"),
        ]
        selected = watch.select_entries(entries, watch.DEFAULT_PATTERN, None)
        self.assertEqual([e.version for e in selected], ["0.1.8", "0.1.9", "0.1.10"])

    def test_version_key_compares_mixed_numeric_and_text_parts_without_error(self):
        # A text part where another version has a number must not raise TypeError.
        ordered = sorted(["1.0.0-rc.1", "1.0.0-1", "0.9.0"], key=watch.version_key)
        self.assertEqual(ordered[0], "0.9.0")


class CurrentSchemaFileTests(unittest.TestCase):
    def write(self, text):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "publish.yml"
        path.write_text(text, encoding="utf-8")
        return path

    def test_reads_file_name_from_schema_url(self):
        path = self.write(f"env:\n  SCHEMA_URL: https://www.fedramp.gov/schemas/{OVERVIEW}\n")
        self.assertEqual(watch.current_schema_file(path), OVERVIEW)

    def test_returns_none_when_schema_url_is_missing(self):
        self.assertIsNone(watch.current_schema_file(self.write("env:\n  OTHER: 1\n")))

    def test_returns_none_when_file_is_missing(self):
        self.assertIsNone(watch.current_schema_file(Path("/nonexistent/publish.yml")))


class IssueTextTests(unittest.TestCase):
    def body(self, e=None, current_file=OVERVIEW):
        return watch.issue_body(e or entry(), PUBLISH_WORKFLOW_NAME, current_file)

    def test_title_names_file_version_bump_and_date(self):
        self.assertEqual(
            watch.issue_title(entry()),
            f"FedRAMP schema change: {OVERVIEW} → 0.1.7 (patch) [2026-10-01]",
        )

    def test_marker_is_the_first_line(self):
        self.assertEqual(self.body().splitlines()[0], entry().marker)

    def test_quotes_changelog_text_and_preserves_blank_lines(self):
        body = self.body(entry(body="Line one.\n\nLine two."))
        self.assertIn("> Line one.\n>\n> Line two.", body)
        self.assertIn(f"> ### {entry().heading}", body)

    def test_links_repository_and_published_copies(self):
        body = self.body()
        self.assertIn(f"https://github.com/FedRAMP/schemas/blob/main/{OVERVIEW}", body)
        self.assertIn(f"https://www.fedramp.gov/schemas/{OVERVIEW}", body)

    def test_major_bump_carries_a_breaking_warning(self):
        self.assertIn("major version bump", self.body(entry(version="1.0.0", bump="major")))
        self.assertNotIn("major version bump", self.body())

    def test_same_file_next_steps_say_to_rerun_publish_and_verify_published_version(self):
        body = self.body()
        self.assertIn(f"Re-run the **{PUBLISH_WORKFLOW_NAME}** workflow", body)
        self.assertIn("$schemaVersion", body)
        self.assertNotIn("SCHEMA_URL", body)

    def test_different_file_is_flagged_as_possible_successor_needing_schema_url_update(self):
        body = self.body(entry(file=SUCCESSOR, version="1.0.0", bump="major"))
        self.assertIn(f"not `{OVERVIEW}`", body)
        self.assertIn("update `SCHEMA_URL`", body)
        self.assertIn("`$schema`", body)
        self.assertIn(watch.DEFAULT_PUBLISH_WORKFLOW_FILE, body)

    def test_unknown_current_file_falls_back_to_same_file_guidance(self):
        body = self.body(entry(file=SUCCESSOR), current_file=None)
        self.assertNotIn("SCHEMA_URL", body)

    def test_long_bodies_are_truncated(self):
        body = self.body(entry(body="x" * (watch.MAX_QUOTED_BODY_CHARS * 3)))
        self.assertIn("(truncated", body)
        self.assertLess(len(body), watch.MAX_QUOTED_BODY_CHARS + 3000)


class ExistingKeysTests(unittest.TestCase):
    def keys_for(self, issues):
        with mock.patch.object(watch, "run_gh", return_value=json.dumps(issues)) as run:
            keys = watch.existing_keys("o/r", "fedramp-schema-watch")
        args = run.call_args.args[0]
        self.assertIn("--state", args)
        self.assertEqual(args[args.index("--state") + 1], "all")
        return keys

    def test_collects_markers_from_open_and_closed_issues(self):
        keys = self.keys_for(
            [{"body": entry().marker + "\nx"}, {"body": entry(version="0.1.8").marker}]
        )
        self.assertEqual(keys, {f"{OVERVIEW}@0.1.7", f"{OVERVIEW}@0.1.8"})

    def test_ignores_issues_without_a_marker_or_body(self):
        self.assertEqual(self.keys_for([{"body": "hello"}, {"body": None}, {}]), set())

    def test_empty_output_is_no_keys(self):
        with mock.patch.object(watch, "run_gh", return_value=""):
            self.assertEqual(watch.existing_keys("o/r", "l"), set())


class RunGhTests(unittest.TestCase):
    def test_appends_repo_and_returns_stdout(self):
        done = mock.Mock(returncode=0, stdout="ok\n", stderr="")
        with mock.patch.object(watch.subprocess, "run", return_value=done) as run:
            self.assertEqual(watch.run_gh(["issue", "list"], "o/r"), "ok\n")
        self.assertEqual(run.call_args.args[0], ["gh", "issue", "list", "--repo", "o/r"])

    def test_raises_with_stderr_on_failure(self):
        done = mock.Mock(returncode=1, stdout="", stderr="boom")
        with mock.patch.object(watch.subprocess, "run", return_value=done):
            with self.assertRaisesRegex(RuntimeError, "boom"):
                watch.run_gh(["issue", "list"], "o/r")


class MainTests(unittest.TestCase):
    """Drives main() end to end with a fake gh and a local CHANGELOG."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.publish = self.tmp / "publish.yml"
        self.publish.write_text(
            f"env:\n  SCHEMA_URL: https://www.fedramp.gov/schemas/{OVERVIEW}\n", encoding="utf-8"
        )
        self.calls = []
        self.existing = []

    def fake_gh(self, args, repo):
        self.calls.append(args)
        if args[:2] == ["issue", "list"]:
            return json.dumps([{"body": b} for b in self.existing])
        if args[:2] == ["issue", "create"]:
            return f"https://github.com/{repo}/issues/{len(self.calls)}\n"
        return ""

    def run_main(self, changelog, *extra):
        path = self.tmp / "CHANGELOG.md"
        path.write_text(changelog, encoding="utf-8")
        argv = [
            "--repo", "o/r",
            "--changelog", str(path),
            "--since", "2026-09-24",
            "--publish-workflow-file", str(self.publish),
            *extra,
        ]  # fmt: skip
        out = io.StringIO()
        with mock.patch.object(watch, "run_gh", side_effect=self.fake_gh):
            with contextlib.redirect_stdout(out):
                code = watch.main(argv)
        return code, out.getvalue()

    def created(self):
        return [c for c in self.calls if c[:2] == ["issue", "create"]]

    def release(self, version, date="2026-10-01", file=OVERVIEW, bump="patch"):
        return f"## {date} — {file} → {version} ({bump})\n\nChange {version}.\n\n"

    def test_files_one_issue_per_new_entry_oldest_first(self):
        code, _ = self.run_main(
            "# Changelog\n\n"
            + self.release("0.1.10", "2026-10-03")
            + self.release("0.1.7", "2026-10-01")
            + self.release("0.1.9", "2026-10-02")
        )
        self.assertEqual(code, 0)
        titles = [c[c.index("--title") + 1] for c in self.created()]
        self.assertEqual(
            [re.search(r"→ (\S+)", t).group(1) for t in titles], ["0.1.7", "0.1.9", "0.1.10"]
        )

    def test_labels_and_assigns_each_issue_and_ensures_label_exists_first(self):
        self.run_main("# C\n\n" + self.release("0.1.7"), "--assignee", "robert")
        self.assertEqual(self.calls[1][:2], ["label", "create"])
        (create,) = self.created()
        self.assertEqual(create[create.index("--label") + 1], "fedramp-schema-watch")
        self.assertEqual(create[create.index("--assignee") + 1], "robert")

    def test_omits_assignee_when_not_configured(self):
        self.run_main("# C\n\n" + self.release("0.1.7"))
        self.assertNotIn("--assignee", self.created()[0])

    def test_skips_entries_already_filed_even_if_the_issue_is_closed(self):
        self.existing = [entry(version="0.1.7").marker]
        code, out = self.run_main(
            "# C\n\n" + self.release("0.1.7") + self.release("0.1.8", "2026-10-02")
        )
        self.assertEqual(code, 0)
        self.assertEqual(len(self.created()), 1)
        self.assertIn("0.1.7 (2026-10-01, patch): already filed", out)

    def test_nothing_new_files_nothing_and_creates_no_label(self):
        self.existing = [entry(version="0.1.7").marker]
        code, out = self.run_main("# C\n\n" + self.release("0.1.7"))
        self.assertEqual(code, 0)
        self.assertIn("No new CHANGELOG entries to file.", out)
        self.assertEqual([c[:2] for c in self.calls], [["issue", "list"]])

    def test_ignores_entries_before_the_baseline_and_for_other_schemas(self):
        code, out = self.run_main(
            "# C\n\n"
            + self.release("0.1.6", "2026-09-23")
            + self.release("2.0.1", "2026-10-01", file=ADVISOR)
        )
        self.assertEqual(code, 0)
        self.assertEqual(self.created(), [])
        self.assertIn("0 match", out)

    def test_dry_run_prints_the_issue_but_creates_nothing(self):
        code, out = self.run_main("# C\n\n" + self.release("0.1.7"), "--dry-run")
        self.assertEqual(code, 0)
        self.assertEqual([c[:2] for c in self.calls], [["issue", "list"]])
        self.assertIn("Dry run: would file 1 issue(s).", out)
        self.assertIn(entry().marker, out)

    def test_successor_file_is_filed_and_flagged(self):
        self.run_main(
            "# C\n\n" + self.release("1.0.0", "2027-01-01", file=SUCCESSOR, bump="major")
        )
        (create,) = self.created()
        body = create[create.index("--body") + 1]
        self.assertIn("update `SCHEMA_URL`", body)
        self.assertIn("major version bump", body)

    def test_missing_publish_workflow_warns_but_still_files(self):
        self.publish.unlink()
        code, out = self.run_main("# C\n\n" + self.release("0.1.7"))
        self.assertEqual(code, 0)
        self.assertIn("::warning::Could not read SCHEMA_URL", out)
        self.assertEqual(len(self.created()), 1)

    def test_fails_when_no_release_headings_parse(self):
        code, out = self.run_main("# Changelog\n\nNothing here.\n")
        self.assertEqual(code, 1)
        self.assertIn("::error::No release headings could be parsed", out)
        self.assertEqual(self.calls, [])

    def test_fails_but_still_files_parseable_entries_when_a_watched_heading_is_unparseable(self):
        code, out = self.run_main(
            "# C\n\n"
            + self.release("0.1.7")
            + f"## 2027-01-01 — {SUCCESSOR} released as 1.0.0\n\nBody.\n"
        )
        self.assertEqual(code, 1)
        self.assertIn("::error::CHANGELOG heading names a watched schema", out)
        self.assertEqual(len(self.created()), 1)

    def test_unparseable_heading_for_an_unwatched_schema_does_not_fail(self):
        code, _ = self.run_main(
            "# C\n\n"
            + self.release("0.1.7")
            + f"## 2027-01-01 — {ADVISOR} released as 3.0.0\n\nBody.\n"
        )
        self.assertEqual(code, 0)

    def test_unparseable_heading_fails_even_when_nothing_new_to_file(self):
        self.existing = [entry(version="0.1.7").marker]
        code, _ = self.run_main(
            "# C\n\n"
            + self.release("0.1.7")
            + f"## 2027-01-01 — {SUCCESSOR} released as 1.0.0\n\nBody.\n"
        )
        self.assertEqual(code, 1)

    def test_requires_a_repo(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    watch.main(["--changelog", str(self.tmp / "x.md")])


class RepositoryConfigurationTests(unittest.TestCase):
    """Guards that keep the watch pointed at the schema this repo really validates against."""

    publish_text = (
        ROOT / ".github/workflows/publish-fedramp-certification-package-overview.yml"
    ).read_text(encoding="utf-8")
    watch_text = (ROOT / ".github/workflows/watch-fedramp-schema-changelog.yml").read_text(
        encoding="utf-8"
    )

    publish_path = ROOT / watch.DEFAULT_PUBLISH_WORKFLOW_FILE

    def env_value(self, text, name):
        match = re.search(rf"^\s*{name}:\s*(.+?)\s*$", text, re.MULTILINE)
        self.assertIsNotNone(match, f"{name} not found")
        return match.group(1).strip("\"'")

    def test_publish_workflow_schema_url_is_readable(self):
        self.assertEqual(watch.current_schema_file(self.publish_path), OVERVIEW)

    def test_watch_pattern_covers_the_schema_file_being_validated(self):
        pattern = self.env_value(self.watch_text, "SCHEMA_FILE_PATTERN")
        self.assertEqual(pattern, watch.DEFAULT_PATTERN)
        self.assertTrue(fnmatch.fnmatch(OVERVIEW, pattern))
        self.assertTrue(fnmatch.fnmatch(SUCCESSOR, pattern))

    def test_watch_workflow_points_at_the_publish_workflow(self):
        self.assertEqual(
            self.env_value(self.watch_text, "PUBLISH_WORKFLOW_FILE"),
            watch.DEFAULT_PUBLISH_WORKFLOW_FILE,
        )
        self.assertTrue(self.publish_path.is_file())
        workflow_name = re.match(r"name:\s*(.+?)\s*$", self.publish_text, re.MULTILINE)
        self.assertEqual(workflow_name.group(1), watch.DEFAULT_PUBLISH_WORKFLOW_NAME)
        self.assertEqual(
            self.env_value(self.watch_text, "PUBLISH_WORKFLOW_NAME"),
            watch.DEFAULT_PUBLISH_WORKFLOW_NAME,
        )

    def test_readme_schema_matches_publish_workflow_schema(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        declared = re.search(r'"\$schema":\s*"[^"]*/schemas/([^"/]+\.json)"', readme)
        self.assertIsNotNone(declared)
        self.assertEqual(declared.group(1), watch.current_schema_file(self.publish_path))

    def test_baseline_is_a_valid_iso_date(self):
        dt.date.fromisoformat(self.env_value(self.watch_text, "WATCH_SINCE"))


if __name__ == "__main__":
    unittest.main()
