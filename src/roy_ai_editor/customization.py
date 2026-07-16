"""Public Customization and Editing Workflow configuration."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path

from .project import load_project


def _load_resource(directory: str, filename: str) -> dict:
    checkout_path = Path(__file__).resolve().parents[2] / directory / filename
    if checkout_path.is_file():
        return json.loads(checkout_path.read_text(encoding="utf-8"))

    packaged = resources.files("roy_ai_editor").joinpath("resources", directory, filename)
    return json.loads(packaged.read_text(encoding="utf-8"))


def load_workflow(workflow_id: str) -> dict:
    return _load_resource("workflows", f"{workflow_id}.json")


def load_public_profile(filename: str) -> dict:
    return _load_resource("profiles", filename)


def concert_live_status(project_dir: Path) -> dict:
    manifest = load_project(project_dir)
    workflow = load_workflow("concert-live")
    if manifest.get("workflow") != workflow["workflow_id"]:
        raise ValueError(f"Project is not a {workflow['workflow_id']} Media Project")
    if manifest.get("schema_version") != workflow["project_schema_version"]:
        raise ValueError("Project Manifest schema is not supported by the Concert Live Workflow")

    profile = load_public_profile(workflow["public_profile"])
    gates = manifest.get("review_gates", {})
    next_gate = next(
        (gate for gate in workflow["required_review_gates"] if gates.get(gate) != "approved"),
        None,
    )
    return {
        "workflow": workflow["workflow_id"],
        "project_id": manifest["project_id"],
        "stage": manifest["stage"],
        "review_gates": gates,
        "next_gate": next_gate,
        "approved_deliverables": manifest.get("approved_deliverables", []),
        "evidence_artifacts": manifest.get("evidence_artifacts", []),
        "public_profile": profile["profile_id"],
    }
