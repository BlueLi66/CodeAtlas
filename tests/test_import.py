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


def test_list_files_returns_only_requested_repository(
    repository_client, tmp_path
):
    """导入两个仓库后分别查清单：归属正确、有序、不带正文、不改数据。"""
    # 故意按与路径排序不同的顺序写入，避免测试只依赖插入顺序。
    first_response = upload_zip(
        repository_client,
        make_zip({
            "src/main.py": "print('你好')\n",
            "README.md": "# 示例\n",
        }),
    )
    assert first_response.status_code == 201
    first_id = first_response.json()["id"]

    # 两个仓库都有 src/main.py，文件仍应由 repository_id 区分归属。
    second_response = upload_zip(
        repository_client,
        make_zip({
            "src/main.py": "print('另一仓库')\n",
            "only-other.py": "print('other')\n",
        }),
    )
    assert second_response.status_code == 201
    second_id = second_response.json()["id"]
    assert second_id != first_id

    before = read_database(tmp_path)

    # 同一个测试对两个仓库分别验证，不只检查第一份清单。
    for repository_id, expected_paths in [
        (first_id, ["README.md", "src/main.py"]),
        (second_id, ["only-other.py", "src/main.py"]),
    ]:
        response = repository_client.get(
            f"/repositories/{repository_id}/files"
        )
        assert response.status_code == 200
        files = response.json()
        assert [item["path"] for item in files] == expected_paths

        # 每项必须是文件清单的三个字段，而不是带 content 的完整正文。
        for item in files:
            assert set(item) == {"id", "repository_id", "path"}
            assert isinstance(item["id"], int)
            assert item["id"] > 0
            assert item["repository_id"] == repository_id
        assert len({item["id"] for item in files}) == len(files)

    # GET 查询只读：原有仓库和文件内容都不能被改变。
    assert read_database(tmp_path) == before


def test_list_files_distinguishes_empty_and_missing_repository(
    repository_client, tmp_path
):
    """有仓库但没有文件返回 200 和 []；仓库不存在返回 404。"""
    created = repository_client.post(
        "/repositories",
        json={
            "name": "空仓库",
            "source_url": "https://example.com/empty",
        },
    )
    assert created.status_code == 201
    repository_id = created.json()["id"]
    before = read_database(tmp_path)

    response = repository_client.get(
        f"/repositories/{repository_id}/files"
    )
    assert response.status_code == 200
    assert response.json() == []

    # 独立临时数据库里只有上面创建的一条仓库；这个 ID 一定不存在。
    response = repository_client.get(
        f"/repositories/{repository_id + 1000}/files"
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Repository not found"}
    assert read_database(tmp_path) == before


def test_read_file_returns_saved_content(repository_client, tmp_path):
    """导入后经清单取得文件 ID，再读回中文、换行与空文件正文。"""
    expected_contents = {
        "src/main.py": "print('你好')\n\n# 中文注释\n",
        "EMPTY.md": "",
    }
    imported = upload_zip(repository_client, make_zip(expected_contents))
    assert imported.status_code == 201
    repository_id = imported.json()["id"]

    # 使用清单返回的真实文件 ID，不猜测文件和仓库的主键相同。
    listed = repository_client.get(
        f"/repositories/{repository_id}/files"
    )
    assert listed.status_code == 200
    files = listed.json()
    assert len(files) == len(expected_contents)
    assert {item["path"] for item in files} == set(expected_contents)
    before = read_database(tmp_path)

    for item in files:
        response = repository_client.get(
            f"/repositories/{repository_id}/files/{item['id']}"
        )
        assert response.status_code == 200
        # 核对完整响应，不能只检查接口是否说读取成功。
        assert response.json() == {
            "id": item["id"],
            "repository_id": repository_id,
            "path": item["path"],
            "content": expected_contents[item["path"]],
        }

    assert read_database(tmp_path) == before


def test_read_file_rejects_another_repository(repository_client, tmp_path):
    """两个仓库都有同名文件，不能用仓库 A 的路径读取仓库 B 的正文。"""
    first = upload_zip(
        repository_client,
        make_zip({"main.py": "仓库 A 的正文"}),
    )
    assert first.status_code == 201
    first_id = first.json()["id"]

    second = upload_zip(
        repository_client,
        make_zip({"main.py": "仓库 B 的正文"}),
    )
    assert second.status_code == 201
    second_id = second.json()["id"]
    assert first_id != second_id

    listed = repository_client.get(f"/repositories/{second_id}/files")
    assert listed.status_code == 200
    second_file_id = listed.json()[0]["id"]
    before = read_database(tmp_path)

    # 故意混用 A 的仓库 ID 和 B 的文件 ID，必须返回 404 而不是正文。
    response = repository_client.get(
        f"/repositories/{first_id}/files/{second_file_id}"
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Source file not found"}
    assert read_database(tmp_path) == before


@pytest.mark.parametrize("missing_kind", ["file", "repository"])
def test_read_file_returns_404_for_missing_record(
    repository_client, tmp_path, missing_kind
):
    """分别测试仓库存在但文件不存在，以及文件存在但仓库不存在。"""
    imported = upload_zip(
        repository_client,
        make_zip({"main.py": "print('hello')\n"}),
    )
    assert imported.status_code == 201
    repository_id = imported.json()["id"]

    listed = repository_client.get(f"/repositories/{repository_id}/files")
    assert listed.status_code == 200
    file_id = listed.json()[0]["id"]
    before = read_database(tmp_path)

    # 每次测试有独立临时数据库，其中只有一条仓库和一条文件记录。
    if missing_kind == "file":
        file_id += 1000
        expected_detail = "Source file not found"
    else:
        repository_id += 1000
        expected_detail = "Repository not found"

    response = repository_client.get(
        f"/repositories/{repository_id}/files/{file_id}"
    )
    assert response.status_code == 404
    assert response.json() == {"detail": expected_detail}
    assert read_database(tmp_path) == before
