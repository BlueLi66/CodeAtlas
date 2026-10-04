import pytest
from zipfile import ZipFile, ZipInfo
from backend.archive import (is_safe_entry_name,
                             list_archive_entries,
                             validate_archive_entry_names,
                             validate_archive_entry_sizes,
                             validate_archive_total_size,
                             is_candidate_source_entry,
                             inspect_candidate_entries,
                             read_entry_bytes,
                             read_entry_text,
                             )


def test_zip_entry_paths():
    assert is_safe_entry_name("src/main.py")
    assert not is_safe_entry_name("../secret.txt")
    assert not is_safe_entry_name("/tmp/evil.py")
    assert not is_safe_entry_name("C:/temp/evil.py")

def test_lists_archive_entries(tmp_path):
    archive_path = tmp_path / "sample.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("src/main.py", "print('hello')")
    entries = list_archive_entries(archive_path)
    assert [entry.filename for entry in entries] == ["src/main.py"]

def test_rejects_zip_with_unsafe_entry_name(tmp_path):
    archive_path = tmp_path / "unsave.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("src/main.py", "print('hello')")
        archive.writestr("../secret.py", "secret")

    entries = list_archive_entries(archive_path)
    # 预期异常检查器
    with pytest.raises(ValueError):
        validate_archive_entry_names(entries)

def test_rejects_oversized_entry(tmp_path):
    archive_path = tmp_path / "large.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("main.py", "abcdef")

    entries = list_archive_entries(archive_path)
    with pytest.raises(ValueError):
        validate_archive_entry_sizes(entries, max_file_bytes=5)

def test_rejects_oversized_archive_total(tmp_path):
    archive_path = tmp_path / "total.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("a.py", "abcd")
        archive.writestr("b.py", "efgh")
    entries = list_archive_entries(archive_path)
    validate_archive_entry_sizes(entries, max_file_bytes=5)
    with pytest.raises(ValueError):
        validate_archive_total_size(entries, max_total_bytes=7)

def test_identifies_candidate_source_entries():
    assert is_candidate_source_entry(ZipInfo("src/main.py"))
    assert is_candidate_source_entry(ZipInfo("README.md"))
    assert not is_candidate_source_entry(ZipInfo("assets/logo.png"))
    assert not is_candidate_source_entry(ZipInfo("src/"))

def test_inspect_candidate_entries_filters_non_source_files(tmp_path):
    archive_path = tmp_path / "mixed.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("main.py", "aaaaa")
        archive.writestr("logo.png", "")

    result = inspect_candidate_entries(
        archive_path,
        max_file_bytes=10,
        max_total_bytes=20,
    )
    assert [entry.filename for entry in result] == ["main.py"]

def test_read_entry_bytes_enforces_limit(tmp_path):
    archive_path = tmp_path / "read.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("main.py", "abcdef")

    entry = list_archive_entries(archive_path)[0]

    assert read_entry_bytes(archive_path, entry, max_file_bytes=6) == b"abcdef"
    with pytest.raises(ValueError):
        read_entry_bytes(archive_path, entry, max_file_bytes=5)


def test_read_entry_text_decodes_utf8(tmp_path):
    archive_path = tmp_path / "text.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("README.md", "你好")

    entry = list_archive_entries(archive_path)[0]
    assert read_entry_text(archive_path, entry, max_file_bytes=6) == "你好"


def test_read_entry_text_reports_invalid_utf8_filename(tmp_path):
    archive_path = tmp_path / "invalid-text.zip"
    with ZipFile(archive_path, "w") as archive:
        archive.writestr("bad.py", b"\xff")

    entry = list_archive_entries(archive_path)[0]
    with pytest.raises(ValueError, match="bad.py"):
        read_entry_text(archive_path, entry, max_file_bytes=1)

def test_rejects_non_zip_file(tmp_path):
    archive_path  = tmp_path / "fake.zip"
    archive_path.write_bytes(b"not a zip")

    with pytest.raises(ValueError, match="无效的 ZIP 文件"):
        list_archive_entries(archive_path)