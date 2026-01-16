from codesynth.parser import GitignoreParser


def test_gitignore_parser_respects_patterns(tmp_path):
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("*.log\nbuild/\nlogs/ignore.txt\n", encoding="utf-8")

    parser = GitignoreParser(str(tmp_path), ".gitignore")

    assert parser.should_ignore("debug.log") is True
    assert parser.should_ignore("build", is_dir=True) is True
    assert parser.should_ignore("logs/ignore.txt") is True
    assert parser.should_ignore("src/app.py") is False


def test_empty_gitignore_includes_default_dirs():
    parser = GitignoreParser.empty()
    assert ".git" in parser.dir_patterns


def test_gitignore_parser_supports_negation_and_anchoring(tmp_path):
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text(
        "\n".join(
            [
                "*.log",
                "!important.log",
                "build/",
                "logs/*.txt",
                "!logs/keep.txt",
                "/only-root.txt",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    parser = GitignoreParser(str(tmp_path), ".gitignore")

    assert parser.should_ignore("debug.log") is True
    assert parser.should_ignore("important.log") is False
    assert parser.should_ignore("build", is_dir=True) is True
    assert parser.should_ignore("build/app.py") is True
    assert parser.should_ignore("logs/ignore.txt") is True
    assert parser.should_ignore("logs/keep.txt") is False
    assert parser.should_ignore("only-root.txt") is True
    assert parser.should_ignore("nested/only-root.txt") is False
