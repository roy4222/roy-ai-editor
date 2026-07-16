import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_repository_integrity_gate_passes() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/check_repo_integrity.py"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    report = json.loads(result.stdout)
    assert report["status"] == "passed"
    assert report["tracked_files"] > 0
    assert report["largest_file_bytes"] < 10 * 1024 * 1024
