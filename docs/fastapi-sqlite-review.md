# 第 2 周复盘：FastAPI 与 SQLite

本周的小练习是“仓库清单 API”：创建、查询列表、按 ID 删除仓库记录。先记住这一条主线：

```text
浏览器或测试客户端 → HTTP 请求 → FastAPI 按方法和路径找到路由
                                   ↳ 校验请求数据；通过 get_db 提供 Session
                                   → 路由使用 SQLAlchemy 读写 SQLite
                                   → Python 返回值 → JSON 响应
```

## 1. HTTP 请求怎样找到函数

路由由“方法 + 路径”共同决定；同一路径的 `POST` 和 `GET` 可以执行不同函数：

| 请求 | 项目中的作用 | 成功响应 |
| --- | --- | --- |
| `POST /repositories` | 创建一条记录 | `201`，返回 `id`、`name`、`source_url` |
| `GET /repositories` | 读取列表 | `200`，返回数组；没有记录时是 `[]` |
| `DELETE /repositories/3` | 删除 ID 为 3 的记录 | `204`，没有响应内容 |

`POST` 的 JSON 是请求体，由 `RepositoryCreate` 接收。`DELETE` 中的 `3` 是路径参数，FastAPI 把它转换为 `int`。形如 `?limit=10` 的是查询参数；本周路线图提到了它，但当前项目尚未使用。

## 2. 请求模型、数据库模型和会话各管什么

- `RepositoryCreate(BaseModel)`：描述创建请求需要的 `name` 和 `source_url`。缺少必填字段时，FastAPI 返回 `422`，创建路由的函数体不执行。当前的 `source_url: str` 只要求字符串，并不保证网址可访问。
- `Repository(Base)`：对应 SQLite 的 `repositories` 表；每个实例代表一条记录。`__tablename__` 是类的表名配置，`id` 是数据库生成的主键。详见 [Python 基础笔记第 14 节](python-basics-practice.md#14-api-请求模型和数据库模型各自负责什么)。
- `engine`：SQLAlchemy 访问 SQLite 的入口；`SessionLocal` 是创建会话的工厂。`get_db()` 为请求提供一个 `Session`，路由结束后关闭它。`Depends(get_db)` 告诉 FastAPI 在调用路由时提供这个会话。

`codeatlas.db` 和 `repositories` 表已经在本机创建；`get_db()` 负责提供会话，不负责建表。

## 3. 三条数据流

创建：`RepositoryCreate` 校验请求 → `Repository(...)` 构造待保存对象 → `db.add()` 交给会话管理 → `db.commit()` 将改动提交到 SQLite → `db.refresh()` 从数据库重新读取该对象 → 返回包含 `id` 的字典。`add()` 本身不等于已保存；数据库生成的 `id` 可能在提交过程中的写入阶段就出现，不必理解成只能在 `refresh()` 时生成。

查询：`select(Repository)` 描述要查什么 → `db.scalars(...).all()` 执行查询，得到对象列表 → 路由把每个对象转成字典 → 返回 JSON 数组。只读查询不需要 `commit()`。

删除：路径参数转换为整数 → `db.get(Repository, repository_id)` 按主键查找 → 找不到则抛出 `HTTPException(404)` → 找到后 `db.delete()` 并 `db.commit()` → 返回 `204`。

## 4. 我们怎样验证它

`python -m pytest` 运行自动测试。测试里的 `repository_client` 使用 `tmp_path` 创建临时 SQLite 文件，并用 `app.dependency_overrides[get_db]` 让 API 请求使用测试会话；每条使用该 fixture 的测试都有独立的临时数据库，不会修改项目根目录的 `codeatlas.db`。测试客户端通过 `TestClient` 在进程内发送请求，不必启动 Uvicorn。

另外，我们用 `python -m uvicorn backend.main:app --reload` 启动服务，在 `/docs` 手动完成了创建 → 查询 → 删除。这一步访问的是真实开发数据库；自动测试访问的是临时数据库。最后一次完整测试结果为 `12 passed`；出现的两条依赖弃用警告没有导致测试失败。

## 5. 自测：能回答就可以进入下一阶段

1. `RepositoryCreate` 和 `Repository` 各处理哪一段数据？
2. `db.add()`、`db.commit()`、`db.refresh()` 分别做什么？
3. `404`、`422`、`204` 在当前接口中分别何时出现？
4. 为什么自动测试里的创建请求不会污染真实的 `codeatlas.db`？

本周目标是理解一次请求从浏览器到数据库再返回 JSON 的链路。下一阶段会用 React 页面调用已有 API；当前不需要先学习更复杂的数据库特性。
