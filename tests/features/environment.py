"""behave hooks: give every scenario an isolated working directory and a fake `gh`."""

import shutil
import tempfile
from pathlib import Path

FAKE_GH = Path(__file__).resolve().parents[1] / "support" / "fake_gh.py"


def before_scenario(context, scenario):
    context.tmp = tempfile.TemporaryDirectory()
    context.workdir = Path(context.tmp.name)

    bin_dir = context.workdir / "bin"
    bin_dir.mkdir()
    fake_gh = bin_dir / "gh"
    shutil.copy(FAKE_GH, fake_gh)
    fake_gh.chmod(0o755)

    context.bin_dir = bin_dir
    context.gh_state_path = context.workdir / "gh_state.json"
    context.publish_workflow = None
    context.assignee = ""
    context.since = None
    context.changelog_sections = []
    context.result = None


def after_scenario(context, scenario):
    context.tmp.cleanup()
