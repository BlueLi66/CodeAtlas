# CodeAtlas

CodeAtlas 是一个帮助初学者理解陌生代码仓库的学习导航器。

目前已实现仓库记录的新增、列表展示和删除，前端通过 API 展示真实文件清单，并支持点击文件查看正文。

后端已支持通过 API 上传 ZIP，检查路径与大小、筛选并按 UTF-8 读取 `.py` 和 `.md` 文件，在同一个数据库事务中保存仓库及文件。删除仓库时也会清理所属文件；数据库结构由 Alembic 迁移管理。这是本地学习版，不代表完整的生产级上传防护。

文件阅读支持加载、失败与空文件提示；切换仓库或成功删除当前仓库时会清除旧正文。前端 ZIP 上传按钮、层级目录树、带源码引用的代码问答和学习进度尚未实现。

## 后端本地运行

以下命令适用于 Linux、macOS 和 WSL。在项目**根目录**执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m alembic upgrade head
python -m uvicorn backend.main:app --reload
```

Windows PowerShell 可用 `py -m venv .venv` 创建虚拟环境，再用 `.\.venv\Scripts\Activate.ps1` 激活；之后同样在项目根目录执行安装依赖、数据库迁移和启动命令。

全新数据库可直接按上述流程初始化；已经有 Alembic 版本记录的数据库应先备份，再执行升级。如果数据库由旧版 `create_all()` 创建、尚无迁移版本记录，需要先核对实际结构并建立匹配的迁移起点，不要直接运行 `stamp`、重复建表或删除数据库。

打开 [健康检查接口](http://127.0.0.1:8000/health)，应看到 `{"status":"ok"}`。

## ZIP 导入验证

打开 [API 文档](http://127.0.0.1:8000/docs)，展开 `POST /repositories/import` 并点击 `Try it out`。填写 `name`，在 `archive` 中选择包含 UTF-8 `.py` 或 `.md` 文件的小 ZIP。

成功时返回 201，响应包含仓库 ID、名称、`source_url: null` 和 `file_count`。可通过 `GET /repositories` 确认仓库出现；本地 ZIP 没有来源网址，前端会显示“未提供来源地址”。原有手动创建仓库接口仍要求填写来源网址。

非 ZIP、不安全路径、大小超限、候选文件不能按 UTF-8 读取或没有候选文件时，导入会被拒绝。已覆盖的数据库保存失败场景会回滚本次导入，不影响此前已保存的数据。

## 测试

在项目根目录、激活虚拟环境后执行：

```bash
python -m pytest tests/test_import.py -q
python -m pytest -q
```

测试使用临时数据库，不修改本地 `codeatlas.db`。

## 前端本地运行

保持后端服务运行。在同一运行环境中另开一个终端，从项目根目录执行：

```bash
cd frontend
npm ci
npm run dev
```

打开 [前端页面](http://localhost:5173/)，应看到仓库页面和“后端状态：在线”。
