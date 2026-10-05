Feature: Watch for FedRAMP certification package overview schema changes
  As a SunStone Secure maintainer
  I want to be told when FedRAMP releases a new version or a successor of the
  certification package overview schema
  So that the published FedRAMP 20x JSON keeps validating against the schema FedRAMP expects

  Background:
    Given the repository validates against the overview schema dated 2026-06-24
    And the watch is configured to assign issues to "sunstonesecure-robert"
    And the watch baseline is 2026-09-24

  Scenario: A new version of the current schema is filed as an issue
    Given the upstream CHANGELOG lists these releases:
      | date       | schema              | version | bump  | note                                            |
      | 2026-10-01 | overview 2026-06-24 | 0.1.7   | patch | Tighten the dateAvailable pattern (was 0.1.6). |
    When the watch runs
    Then the run succeeds
    And 1 issue exists
    And the issue for overview schema 2026-06-24 version 0.1.7 is labeled "fedramp-schema-watch" and assigned to "sunstonesecure-robert"
    And the issue for overview schema 2026-06-24 version 0.1.7 quotes "Tighten the dateAvailable pattern (was 0.1.6)."
    And the issue for overview schema 2026-06-24 version 0.1.7 tells the maintainer to re-run the "Publish FedRAMP Certification Package Overview" workflow
    And the issue for overview schema 2026-06-24 version 0.1.7 does not tell the maintainer to update SCHEMA_URL

  Scenario: A dated successor schema is filed and flagged for a SCHEMA_URL update
    Given the upstream CHANGELOG lists these releases:
      | date       | schema              | version | bump  | note                                        |
      | 2027-01-01 | overview 2027-01-01 | 1.0.0   | major | First release of the 2027-01-01 schema file. |
    When the watch runs
    Then the run succeeds
    And 1 issue exists
    And the issue for overview schema 2027-01-01 version 1.0.0 tells the maintainer to update SCHEMA_URL
    And the issue for overview schema 2027-01-01 version 1.0.0 warns of a major version bump

  Scenario: A breaking release of the current schema is called out
    Given the upstream CHANGELOG lists these releases:
      | date       | schema              | version | bump  | note                          |
      | 2026-10-01 | overview 2026-06-24 | 1.0.0   | major | Make advisors a required field. |
    When the watch runs
    Then 1 issue exists
    And the issue for overview schema 2026-06-24 version 1.0.0 warns of a major version bump

  Scenario: A release is not filed twice
    Given the upstream CHANGELOG lists these releases:
      | date       | schema              | version | bump  | note                  |
      | 2026-10-01 | overview 2026-06-24 | 0.1.7   | patch | Tighten a pattern.    |
    When the watch runs
    And the watch runs again
    Then the run succeeds
    And 1 issue exists

  Scenario: A release whose issue was already closed is not filed again
    Given an issue labeled "fedramp-schema-watch" already records overview schema 2026-06-24 version 0.1.7
    And the upstream CHANGELOG lists these releases:
      | date       | schema              | version | bump  | note               |
      | 2026-10-01 | overview 2026-06-24 | 0.1.7   | patch | Tighten a pattern. |
      | 2026-10-02 | overview 2026-06-24 | 0.1.8   | patch | Fix a description. |
    When the watch runs
    Then 2 issues exist
    And the issue for overview schema 2026-06-24 version 0.1.8 is labeled "fedramp-schema-watch" and assigned to "sunstonesecure-robert"

  Scenario: Several new releases are filed oldest first, with same-day versions ordered numerically
    Given the upstream CHANGELOG lists these releases:
      | date       | schema              | version | bump  | note    |
      | 2026-10-02 | overview 2026-06-24 | 0.1.10  | patch | Third.  |
      | 2026-10-02 | overview 2026-06-24 | 0.1.9   | patch | Second. |
      | 2026-10-01 | overview 2026-06-24 | 0.1.7   | patch | First.  |
    When the watch runs
    Then the issues were filed for these versions in order:
      | version |
      | 0.1.7   |
      | 0.1.9   |
      | 0.1.10  |

  Scenario: A release dated on the baseline day is included
    Given the upstream CHANGELOG lists these releases:
      | date       | schema              | version | bump  | note               |
      | 2026-09-24 | overview 2026-06-24 | 0.1.7   | patch | Tighten a pattern. |
    When the watch runs
    Then 1 issue exists

  Scenario Outline: Releases outside the watch are ignored
    Given the upstream CHANGELOG lists these releases:
      | date   | schema   | version | bump  | note              |
      | <date> | <schema> | 2.0.1   | patch | Not for this repo. |
    When the watch runs
    Then the run succeeds
    And no issues exist

    Examples:
      | reason                       | date       | schema                        |
      | a different FedRAMP schema   | 2026-10-01 | advisor 2026-06-24            |
      | dated before the baseline    | 2026-09-23 | overview 2026-06-24           |

  Scenario: A dry run reports what would be filed without filing it
    Given the upstream CHANGELOG lists these releases:
      | date       | schema              | version | bump  | note               |
      | 2026-10-01 | overview 2026-06-24 | 0.1.7   | patch | Tighten a pattern. |
    When the watch runs in dry-run mode
    Then the run succeeds
    And the run reports "Dry run: would file 1 issue(s)."
    And no issues exist
    And the label "fedramp-schema-watch" was not created

  Scenario: A CHANGELOG heading for the watched schema that cannot be parsed fails the run
    Given the upstream CHANGELOG lists these releases:
      | date       | schema              | version | bump  | note               |
      | 2026-10-01 | overview 2026-06-24 | 0.1.7   | patch | Tighten a pattern. |
    And the upstream CHANGELOG has the heading "## 2027-01-01 — fedramp-certification-package-overview-schema-2027-01-01.json released as 1.0.0"
    When the watch runs
    Then the run fails
    And the run reports "does not match the release format"
    And 1 issue exists

  Scenario: A CHANGELOG with no release headings fails the run
    Given the upstream CHANGELOG has no release entries
    When the watch runs
    Then the run fails
    And the run reports "No release headings could be parsed"
    And no issues exist
