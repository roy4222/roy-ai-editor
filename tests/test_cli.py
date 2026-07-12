from roy_ai_editor.cli import build_parser, main


def test_parser_exposes_concert_workflow() -> None:
    args = build_parser().parse_args(["concert", "https://example.com/live"])
    assert args.command == "concert"
    assert args.url == "https://example.com/live"


def test_root_command_prints_help(capsys) -> None:
    assert main([]) == 0
    assert "Local-first AI video editing workflows" in capsys.readouterr().out
