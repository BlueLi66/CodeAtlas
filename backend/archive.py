from pathlib import PurePosixPath, PureWindowsPath, Path
from zipfile import ZipFile, ZipInfo, BadZipFile
from typing import BinaryIO

def is_safe_entry_name(name:str) -> bool:
    """检查 ZIP 内的路径名；这只是路径规则，不代表整个 ZIP 安全。"""
    posix_path = PurePosixPath(name)
    windows_path = PureWindowsPath(name)

    return (
        bool(name)
        and "\\" not in name
        and not posix_path.is_absolute()
        and not windows_path.anchor
        and ".." not in posix_path.parts
    )

def list_archive_entries(archive_path: Path | BinaryIO) -> list[ZipInfo]:
    """读取 ZIP 条目清单，不解压文件内容。"""
    try:
        with ZipFile(archive_path, "r") as archive:
            return archive.infolist()
    except BadZipFile as error:
        raise ValueError("无效的 ZIP 文件") from error

def validate_archive_entry_names(entries: list[ZipInfo]) -> None:
    """逐项检查路径名；遇到不允许的名字就拒绝清单。"""
    for entry in entries:
        if not is_safe_entry_name(entry.filename):
            raise ValueError(f"不安全的 ZIP 路径: {entry.filename}")

def validate_archive_entry_sizes(entries: list[ZipInfo], max_file_bytes: int) -> None:
    """按清单记录的未压缩大小初筛；实际读取内容时仍需限量。"""
    for entry in entries:
        if entry.file_size > max_file_bytes:
            raise ValueError(f"ZIP 文件过大: {entry.filename}")

def validate_archive_total_size(entries: list[ZipInfo], max_total_bytes:int) -> None:
    """保证清单所有文件大小不超过最大限制"""
    total_bytes = 0
    for entry in entries:
        total_bytes += entry.file_size
        if total_bytes > max_total_bytes:
            raise ValueError("ZIP 文件总大小超限")

def is_candidate_source_entry(entry: ZipInfo) -> bool:
    """ 按拓展名初筛文件，目前仅支持.py 和 .md """
    suffix = PurePosixPath(entry.filename).suffix.lower()
    return not entry.is_dir() and suffix in (".py", ".md")

def inspect_candidate_entries(
    archive_path: Path | BinaryIO, max_file_bytes: int, max_total_bytes: int
) -> list[ZipInfo]:
    """检查 ZIP 清单并返回候选源码条目；还没读取文件内容。"""
    entries = list_archive_entries(archive_path)
    validate_archive_entry_names(entries)
    validate_archive_entry_sizes(entries, max_file_bytes)
    validate_archive_total_size(entries, max_total_bytes)
    return [entry for entry in entries if is_candidate_source_entry(entry)]

def read_entry_bytes(
    archive_path: Path | BinaryIO, entry: ZipInfo, max_file_bytes: int
) -> bytes:
    with ZipFile(archive_path, "r") as archive:
        with archive.open(entry, "r") as source:
            content = source.read(max_file_bytes + 1)
    if len(content) > max_file_bytes:
        raise ValueError(f"ZIP 文件实际内容过大: {entry.filename}")
    return content

def read_entry_text(
    archive_path: Path | BinaryIO, entry: ZipInfo, max_file_bytes: int
) -> str:
    content = read_entry_bytes(archive_path, entry, max_file_bytes)
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"无法按 UTF-8 读取文件: {entry.filename}") from error
