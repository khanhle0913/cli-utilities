from codesynth.reverse import parse_codesynth_markdown, reverse_codesynth, _safe_join


def test_parse_codesynth_markdown_warns_on_missing_fence():
    content = "## File: missing.txt\n\nno fence here\n"
    files, warnings = parse_codesynth_markdown(content)
    assert files == []
    assert any("Missing code fence" in warning for warning in warnings)


def test_reverse_codesynth_writes_files(tmp_path):
    markdown = (
        "## File: foo.txt\n\n"
        "```\nhello\n```\n\n---\n\n"
        "## File: skip.txt\n\n"
        "**Status:** Skipped (binary)\n\n"
        "```\nskip\n```\n\n---\n"
    )
    input_path = tmp_path / "codesynth.md"
    output_dir = tmp_path / "out"
    input_path.write_text(markdown, encoding="utf-8")

    stats = reverse_codesynth(str(input_path), str(output_dir), quiet=True)

    assert stats["written_files"] == 1
    assert stats["skipped_files"] == 1
    assert (output_dir / "foo.txt").read_text(encoding="utf-8") == "hello\n"
    assert not (output_dir / "skip.txt").exists()


def test_safe_join_rejects_traversal(tmp_path):
    assert _safe_join(str(tmp_path), "../oops") is None
    assert _safe_join(str(tmp_path), "nested/file.txt") == str(
        tmp_path / "nested" / "file.txt"
    )
