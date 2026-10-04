"""ZIP 导入的行为测试；由 repository_client 使用临时数据库隔离真实数据。"""

import sqlite3
from io import BytesIO
from zipfile import ZipFile

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.models import SourceFile


def make_zip(files):
    """在内存中制作 ZIP：传入 {相对路径: 内容}，返回可以上传的字节。"""
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        for path, content in files.items():
            archive.writestr(path, content)
    # 离开 with 后 ZIP 已写完，包括文件清单；不用在磁盘创建练习文件。
    return buffer.getvalue()


def upload_zip(client, content):
    """模拟在 /docs 中填写名称并选择 ZIP 文件。"""
    return client.post(
        "/repositories/import",
        data={"name": " ZIP 示例 "},
        # archive 必须与接口参数同名；元组依次是文件名、字节、媒体类型。
        files={"archive": ("sample.zip", content, "application/zip")},
    )


def read_database(tmp_path):
    """新建连接读回 fixture 的临时数据库，检查数据确实保存而非仅存在于 Session。"""
    connection = sqlite3.connect(tmp_path / "test-codeatlas.db")
    try:
        return {
            "repositories": connection.execute(
                "SELECT id, name, source_url "
                "FROM repositories ORDER BY id"
            ).fetchall(),
            "files": connection.execute(
                "SELECT repository_id, path, content "
                "FROM source_files ORDER BY path"
            ).fetchall(),
        }
    finally:
        connection.close()


def test_import_saves_files_and_delete_cleans_them(
    repository_client, tmp_path
):
    """正常导入保存路径和正文，忽略非候选文件；删除时不留孤立文件。"""
    content = make_zip({
        "src/main.py": "print('你好')\n",
        "README.md": "# 示例\n",
        "logo.png": b"ignored",
    })

    response = upload_zip(repository_client, content)
    assert response.status_code == 201

    result = response.json()
    assert result["id"] > 0
    assert result["name"] == "ZIP 示例"
    assert result["source_url"] is None
    assert result["file_count"] == 2

    # 核对数据库里的内容，而不只是相信接口返回的数量。
    repository_id = result["id"]
    saved = read_database(tmp_path)
    assert saved["repositories"] == [
        (repository_id, "ZIP 示例", None)
    ]
    assert saved["files"] == [
        (repository_id, "README.md", "# 示例\n"),
        (repository_id, "src/main.py", "print('你好')\n"),
    ]

    response = repository_client.delete(
        f"/repositories/{repository_id}"
    )
    assert response.status_code == 204
    assert read_database(tmp_path) == {
        "repositories": [],
        "files": [],
    }


# 同一套失败检查使用四种输入执行；不是只检查文件扩展名是否为 .zip。
@pytest.mark.parametrize("content", [
    b"not a zip",
    make_zip({"bad.py": b"\xff"}),
    make_zip({"../secret.py": "secret"}),
    make_zip({"logo.png": b"image"}),
], ids=["not-zip", "invalid-utf8", "unsafe-path", "no-candidates"])
def test_invalid_import_leaves_database_unchanged(
    repository_client, tmp_path, content
):
    """非法输入不得新增残留，也不得改变原有仓库。"""
    response = repository_client.post(
        "/repositories",
        json={"name": "原有仓库", "source_url": "https://example.com"},
    )
    assert response.status_code == 201
    before = read_database(tmp_path)

    response = upload_zip(repository_client, content)

    assert response.status_code == 400
    assert read_database(tmp_path) == before


def test_database_failure_rolls_back_import(
    repository_client, tmp_path, monkeypatch
):
    """仓库已 flush、文件保存失败时，本次导入仍要整体回滚。"""
    response = repository_client.post(
        "/repositories",
        json={"name": "原有仓库", "source_url": "https://example.com"},
    )
    assert response.status_code == 201
    before = read_database(tmp_path)

    original_flush = Session.flush

    def fail_when_saving_files(session, *args, **kwargs):
        # session.new 是这个 Session 中待插入的对象集合。
        # 允许仓库先 flush；出现 SourceFile 时才模拟数据库错误。
        if any(
            isinstance(item, SourceFile) for item in session.new
        ):
            raise SQLAlchemyError("模拟文件保存失败")
        return original_flush(session, *args, **kwargs)

    # 临时替换 flush；pytest 会在本测试结束后自动恢复原方法。
    monkeypatch.setattr(Session, "flush", fail_when_saving_files)

    response = upload_zip(
        repository_client,
        make_zip({"main.py": "print('hello')"}),
    )

    assert response.status_code == 500
    assert read_database(tmp_path) == before
