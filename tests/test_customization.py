import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_public_customization_is_safe_and_versioned() -> None:
    profile_path = REPO_ROOT / "profiles" / "roy-public.example.json"
    workflow_path = REPO_ROOT / "workflows" / "concert-live.json"
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))

    assert profile["profile_id"] == "roy-public-example"
    assert workflow["workflow_id"] == "concert-live"
    assert workflow["required_review_gates"] == ["lyrics"]

    public_text = (profile_path.read_text(encoding="utf-8") + workflow_path.read_text(encoding="utf-8")).lower()
    for prohibited in ("api_key", "password", "cookie", "private_key", "bearer "):
        assert prohibited not in public_text


def test_private_customization_is_ignored_but_public_profile_is_not() -> None:
    private = subprocess.run(
        ["git", "check-ignore", "-q", "profiles/private/example.json"],
        cwd=REPO_ROOT,
        check=False,
    )
    local = subprocess.run(
        ["git", "check-ignore", "-q", "profiles/roy.local.md"],
        cwd=REPO_ROOT,
        check=False,
    )
    public = subprocess.run(
        ["git", "check-ignore", "-q", "profiles/roy-public.example.json"],
        cwd=REPO_ROOT,
        check=False,
    )

    assert private.returncode == 0
    assert local.returncode == 0
    assert public.returncode == 1
