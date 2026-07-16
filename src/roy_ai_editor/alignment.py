"""Optional stable-ts adapter for word-level audio transcription."""

from __future__ import annotations

from pathlib import Path


def _load_model(model_name: str):
    try:
        import stable_whisper
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "stable-ts is optional. Install it with `uv sync --extra alignment`."
        ) from exc
    return stable_whisper.load_model(model_name)


def transcribe(audio: Path, output: Path, *, model_name: str = "large-v3", language: str = "ja") -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    model = _load_model(model_name)
    result = model.transcribe(str(audio), language=language, word_timestamps=True)
    result.save_as_json(str(output))


def force_align(
    audio: Path,
    approved_text: str,
    output: Path,
    *,
    model_name: str = "large-v3",
    language: str = "ja",
) -> None:
    """Align approved source-of-truth text to audio without ASR text replacement."""
    if not approved_text.strip():
        raise ValueError("approved_text must not be blank")
    output.parent.mkdir(parents=True, exist_ok=True)
    model = _load_model(model_name)
    result = model.align(
        str(audio),
        approved_text,
        language=language,
        original_split=True,
    )
    if result is None:
        raise RuntimeError("stable-ts forced alignment returned no result")
    result.save_as_json(str(output))
