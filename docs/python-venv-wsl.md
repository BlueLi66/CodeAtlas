# Python 虚拟环境（`.venv`）— Windows + WSL 速查

## 它解决什么问题？

`.venv` 是一个**项目专属**的 Python 环境。它包含自己的 Python 可执行文件和第三方包，避免 CodeAtlas 使用的依赖影响系统 Python 或其他项目。

```text
系统 Python
├── 项目 A/.venv：pytest、FastAPI ……
└── 项目 B/.venv：另一套独立依赖
```

## 在 CodeAtlas 中创建

在 WSL 终端进入项目根目录后执行：

```bash
cd ~/projects/codeatlas
python3 -m venv .venv
```

- `python3`：WSL 中的 Python；
- `-m venv`：运行 Python 自带的虚拟环境工具；
- `.venv`：创建出的环境目录名。

通常每个项目只需创建一次。若 `.venv` 已存在，不必重复创建。

## 激活与验证

每次新打开 WSL 终端，在项目目录执行：

```bash
source .venv/bin/activate
```

成功后，提示符前会出现 `(.venv)`。再运行：

```bash
which python
python --version
python -m pip --version
```

其中 `which python` 应指向类似下面的路径：

```text
/home/mrli/projects/codeatlas/.venv/bin/python
```

## 安装项目依赖

激活后，优先使用下面的形式安装包：

```bash
python -m pip install pytest
```

`python -m pip` 能确保安装器和当前的 `python` 是同一个虚拟环境，避免把包误装到系统 Python。

## 退出

不再需要该环境时，可以执行：

```bash
deactivate
```

这不是必须步骤；关闭终端也会结束激活状态。

## 一个容易误解的边界

激活只影响**当前终端会话**：它临时修改该终端的环境变量和 `PATH`。

- 新开一个终端标签、关闭后重开终端，或重新连接 WSL 后，都需要重新激活；
- 它不会永久修改系统 Python；
- 它不会自动影响 VS Code 的其他终端、Windows PowerShell 或 CMD；
- 子 agent 在自己的终端中激活，也不会影响你的终端。

## Windows + WSL 注意事项

- 在 WSL 中使用 `source .venv/bin/activate`，不要使用 Windows 的 `.venv\\Scripts\\activate`；
- 不要让同一个 `.venv` 同时被 Windows Python 和 WSL Python 使用；如需在 Windows 原生运行，应分别创建环境；
- `.venv` 不应提交到 Git。稍后在项目的 `.gitignore` 中加入：

```gitignore
.venv/
```

- 将来项目依赖应记录在 `requirements.txt` 或 `pyproject.toml`，而不是依赖某台机器上的 `.venv`。

## 日常最短流程

```bash
cd ~/projects/codeatlas
source .venv/bin/activate
python -m pip install <包名>
python <脚本名>.py
deactivate
```
