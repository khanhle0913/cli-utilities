import argparse

from codesynth.utils import (
    parse_size,
    format_size,
    get_fence,
    is_binary_file,
    read_file_content,
)


def test_parse_size_accepts_units():
    assert parse_size("1KB") == 1024
    assert parse_size("1.5KB") == 1536
    assert parse_size("2 MB") == 2 * 1024 * 1024
    assert parse_size("512") == 512


def test_parse_size_rejects_invalid():
    try:
        parse_size("not-a-size")
    except argparse.ArgumentTypeError as exc:
        assert "Invalid size" in str(exc)
    else:
        raise AssertionError("Expected ArgumentTypeError")


def test_format_size_outputs_human_readable():
    assert format_size(0) == "0 B"
    assert format_size(1023) == "1023 B"
    assert format_size(1024) == "1.0 KB"
    assert format_size(1024 * 1024) == "1.0 MB"


def test_get_fence_escapes_backticks():
    content = "````\ncode\n````"
    fence = get_fence(content)
    assert fence == "`````"


def test_is_binary_file_detects_by_extension(tmp_path):
    binary_file = tmp_path / "image.png"
    binary_file.write_bytes(b"not-really-binary")
    is_binary, reason = is_binary_file(str(binary_file))
    assert is_binary is True
    assert "binary extension" in reason


def test_is_binary_file_detects_null_bytes(tmp_path):
    binary_file = tmp_path / "data.txt"
    binary_file.write_bytes(b"text\x00more")
    is_binary, reason = is_binary_file(str(binary_file))
    assert is_binary is True
    assert "null bytes" in reason


def test_read_file_content_respects_max_size(tmp_path):
    data_file = tmp_path / "data.txt"
    data_file.write_text("a" * 10, encoding="utf-8")
    content, warning = read_file_content(str(data_file), max_size=4)
    assert "File skipped" in content
    assert warning == "size exceeds 4 B"
