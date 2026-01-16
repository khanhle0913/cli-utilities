import sys
import types

from codesynth import main
from codesynth.interactive import interactive_mode


def test_main_scan_generates_output(tmp_path, monkeypatch):
    file_path = tmp_path / "app.py"
    file_path.write_text("print('hi')", encoding="utf-8")
    output_file = tmp_path / "codesynth.md"

    monkeypatch.setattr(sys, "argv", ["codesynth", str(tmp_path), "-o", str(output_file), "-q"])

    result = main()

    assert result == 0
    assert output_file.exists()


def test_main_list_files_outputs_paths(tmp_path, monkeypatch, capsys):
    file_path = tmp_path / "app.py"
    file_path.write_text("print('hi')", encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        ["codesynth", str(tmp_path), "--list-files", "-q"],
    )

    result = main()

    assert result == 0
    captured = capsys.readouterr()
    assert "app.py" in captured.out


def test_main_reverse_mode_restores_files(tmp_path, monkeypatch):
    markdown = "## File: foo.txt\n\n```\nhello\n```\n\n---\n"
    input_path = tmp_path / "codesynth.md"
    output_dir = tmp_path / "restored"
    input_path.write_text(markdown, encoding="utf-8")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "codesynth",
            "--reverse",
            str(input_path),
            "--output-dir",
            str(output_dir),
            "-q",
        ],
    )

    result = main()

    assert result == 0
    assert (output_dir / "foo.txt").read_text(encoding="utf-8") == "hello\n"


def test_main_files_mode_returns_error_on_missing_files(tmp_path, monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        ["codesynth", str(tmp_path), "-f", "missing.txt", "-q"],
    )

    result = main()

    assert result == 1


def test_interactive_mode_builds_args(monkeypatch, tmp_path):
    select_responses = iter([".", True, "clipboard"])

    class FakeSelect:
        def execute(self):
            return next(select_responses)

    def fake_select(*_args, **_kwargs):
        return FakeSelect()

    fake_module = types.SimpleNamespace(
        inquirer=types.SimpleNamespace(select=fake_select)
    )

    monkeypatch.setitem(sys.modules, "InquirerPy", fake_module)
    monkeypatch.chdir(tmp_path)

    args = interactive_mode()

    assert args == [".", "-t", "--clipboard"]
