"""Optional stable-ts adapter for word-level audio transcription."""

from __future__ import annotations

from pathlib import Path


def transcribe(audio: Path, output: Path, *, model_name: str = "large-v3", language: str = "ja") -> None:
    try:
        import stable_whisper
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "stable-ts is optional. Install it with `uv sync --extra alignment`."
        ) from exc

    output.parent.mkdir(parents=True, exist_ok=True)
    model = stable_whisper.load_model(model_name)
    result = model.transcribe(str(audio), language=language, word_timestamps=True)
    result.save_as_json(str(output))
