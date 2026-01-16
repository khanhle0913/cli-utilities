from codesynth.generator import generate_markdown


def test_generate_markdown_includes_tree_and_sizes(tmp_path):
    (tmp_path / "src").mkdir()
    file_path = tmp_path / "src" / "app.py"
    file_path.write_text("print('hi')", encoding="utf-8")

    stats = generate_markdown(
        [str(file_path)],
        str(tmp_path),
        str(tmp_path / "out.md"),
        show_tree=True,
        show_size=True,
        return_content=True,
    )

    content = stats["content"]
    assert "## Directory Structure" in content
    assert "## File: src/app.py (" in content
    assert stats["processed_files"] == 1


def test_generate_markdown_uses_safe_fence(tmp_path):
    file_path = tmp_path / "snippet.txt"
    file_path.write_text("````\ncontent\n````", encoding="utf-8")

    stats = generate_markdown(
        [str(file_path)],
        str(tmp_path),
        str(tmp_path / "out.md"),
        return_content=True,
    )

    content = stats["content"]
    assert "`````" in content


def test_generate_markdown_skips_oversized(tmp_path):
    file_path = tmp_path / "big.txt"
    file_path.write_text("a" * 20, encoding="utf-8")

    stats = generate_markdown(
        [str(file_path)],
        str(tmp_path),
        str(tmp_path / "out.md"),
        max_file_size=4,
        return_content=True,
    )

    assert stats["skipped_files"] == 1
    assert "**Status:** Skipped" in stats["content"]
