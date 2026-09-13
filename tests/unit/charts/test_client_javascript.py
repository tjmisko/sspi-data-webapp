"""
Run the plain-Node unit tests for client JavaScript under pytest, and check
that the minified bundle built from the sources still parses.

Both skip when node is not installed.
"""
import shutil
import subprocess
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
NODE_TEST_DIR = Path(__file__).resolve().parent
NODE_TEST_FILES = sorted(NODE_TEST_DIR.glob("test_*.js"))
NODE_EXECUTABLE = shutil.which("node")

requires_node = pytest.mark.skipif(NODE_EXECUTABLE is None, reason="node is not installed")


@requires_node
@pytest.mark.parametrize("node_test_file", NODE_TEST_FILES, ids=lambda path: path.name)
def test_should_pass_node_unit_tests_when_running_client_javascript(node_test_file):
    result = subprocess.run(
        [NODE_EXECUTABLE, str(node_test_file)],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@requires_node
def test_should_parse_minified_bundle_when_assets_are_built(app):
    bundle_path = REPOSITORY_ROOT / "sspi_flask_app" / "client" / "static" / "script.js"
    assert bundle_path.exists()
    result = subprocess.run(
        [NODE_EXECUTABLE, "--check", str(bundle_path)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
