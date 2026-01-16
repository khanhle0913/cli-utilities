from codesynth.collector import detect_source_directories, collect_files, collect_files_filtered
from codesynth.parser import GitignoreParser


def test_detect_source_directories_finds_common_dirs(tmp_path):
    (tmp_path / "src").mkdir()
    detected = detect_source_directories(str(tmp_path))
    assert str(tmp_path / "src") in detected


def test_collect_files_respects_gitignore(tmp_path):
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("ignore.txt\n", encoding="utf-8")
    (tmp_path / "ignore.txt").write_text("skip", encoding="utf-8")
    (tmp_path / "keep.txt").write_text("keep", encoding="utf-8")

    parser = GitignoreParser(str(tmp_path), ".gitignore")
    files = collect_files(str(tmp_path), parser)

    assert str(tmp_path / "keep.txt") in files
    assert str(tmp_path / "ignore.txt") not in files


def test_collect_files_filtered_with_extensions_and_excludes(tmp_path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "app.py").write_text("print('hi')", encoding="utf-8")
    (src_dir / "app.js").write_text("console.log('hi')", encoding="utf-8")
    (src_dir / "skip.py").write_text("skip", encoding="utf-8")

    parser = GitignoreParser.empty()
    files = collect_files_filtered(
        str(tmp_path),
        parser,
        extensions=["py"],
        exclude_patterns=["*skip*"],
    )

    assert str(src_dir / "app.py") in files
    assert str(src_dir / "app.js") not in files
    assert str(src_dir / "skip.py") not in files
