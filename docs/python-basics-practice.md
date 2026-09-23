# CodeAtlas：Python 基础练习复习

这份笔记只复习目前为 CodeAtlas 文件类型统计器学过的内容。目标是理解每个小语法如何服务于“统计目录中的文件扩展名”。

## 1. 虚拟环境与 pytest

`.venv` 是项目专用的 Python 环境。它让 CodeAtlas 安装的包（例如 `pytest`）不影响系统 Python 或其他项目。

每次新开 WSL 终端后，先进入项目并激活它：

```bash
cd ~/projects/codeatlas
source .venv/bin/activate
```

提示符出现 `(.venv)` 后，确认当前 Python：

```bash
which python
python --version
```

`which python` 应指向项目的 `.venv/bin/python`。安装包时使用：

```bash
python -m pip install pytest
```

运行所有测试：

```bash
python -m pytest
```

测试文件通常放在 `tests/test_*.py`；以 `test_` 开头的函数会被 pytest 发现。`assert` 用来表达预期，例如：

```python
def test_pytest_is_working():
    assert 1 + 1 == 2
```

## 2. 变量、字符串和 `print`

变量是给一个值起名字。字符串是用单引号或双引号包住的文本：

```python
project_name = "CodeAtlas"
file_count = 3

print(project_name)
print(file_count)
```

变量名必须完全一致。`counts` 和 `count` 是两个不同的名字；使用尚未创建的变量会得到 `NameError`。

```python
extension = ".py"       # ".py" 是字符串
print(extension)         # extension 是变量，不能加引号
print("extension")      # 这是字面文本，不是变量的值
```

## 3. 函数：`def`、参数与 `return`

函数把可重复的操作命名。文件统计器将来是一个函数：传入数据，返回统计结果。

```python
def add_one(number):
    return number + 1

result = add_one(3)
print(result)  # 4
```

- `def`：定义函数。
- `number`：参数，代表调用者传入的输入。
- 缩进的代码属于函数；Python 通常使用 4 个空格。
- `return`：把结果交还给调用者。

## 4. 列表与 `for` 循环

列表用 `[]` 保存多个按顺序排列的值。`for` 会逐个取出列表中的值：

```python
filenames = ["main.py", "README.md", "config.json"]

for filename in filenames:
    print(filename)
```

每一轮中，`filename` 分别是 `main.py`、`README.md`、`config.json`。冒号 `:` 表示下面开始一个缩进代码块。

在早期练习中，可以用字符串切分得到简单文件名的扩展名：

```python
filename = "main.py"
parts = filename.split(".")
extension = "." + parts[-1]
print(extension)  # .py
```

真正处理路径时会使用后面的 `Path.suffix`，它更可靠。

## 5. 字典：用扩展名对应文件数量

字典用 `{键: 值}` 保存对应关系，正适合“扩展名 → 数量”：

```python
counts = {".py": 2, ".md": 1}

print(counts[".py"])  # 2
```

这等价于逐项创建：

```python
counts = {}
counts[".py"] = 2
counts[".md"] = 1
```

变量可以作为键：

```python
extension = ".md"
print(counts[extension])  # 等价于 counts[".md"]
```

`+= 1` 表示“取原值、加一、再存回去”：

```python
counts[".py"] += 1
```

统计某种扩展名时，先确保这个键存在，再增加数量：

```python
if extension not in counts:
    counts[extension] = 0

counts[extension] += 1
```

注意：最后一行在 `if` 块外面，才能让新旧扩展名每次都加一。

## 6. 条件判断：`if`、`==`、`in` 与 `not in`

`if` 只在条件为真时运行其缩进代码：

```python
extension = ".py"

if extension == ".py":
    print("python file")
```

- `==`：比较两边是否相等。
- `=`：赋值，不能代替 `==`。
- `in`：判断某项是否包含在另一个值中。
- `not in`：判断某项是否不在其中。

例如先用文件名判断没有点号的文件：

```python
filename = "LICENSE"

if "." not in filename:
    print("忽略：没有扩展名")
```

这对应统计器的规则：没有扩展名的文件不统计。

## 7. 从练习到一个小型统计函数

下面组合了循环、判断和字典累加。它目前接收文件名列表，还没有读取真实目录：

```python
def count_extensions(filenames):
    counts = {}

    for filename in filenames:
        if "." in filename:
            parts = filename.split(".")
            extension = "." + parts[-1]

            if extension not in counts:
                counts[extension] = 0

            counts[extension] += 1

    return counts
```

调用并查看结果：

```python
filenames = ["main.py", "README.md", "LICENSE", "api.py"]
result = count_extensions(filenames)
print(result)  # {'.py': 2, '.md': 1}
```

对应的测试可以写成：

```python
from scanner import count_extensions


def test_counts_extensions_and_ignores_extensionless_files():
    filenames = ["main.py", "README.md", "LICENSE", "api.py"]

    result = count_extensions(filenames)

    assert result == {".py": 2, ".md": 1}
```

## 8. REPL 常见情况与 VS Code 工作流

Python REPL 是在终端输入 `python` 后看到的 `>>>` 环境，适合尝试几行代码。

- `>>>` 和 `...` 是 Python 显示的提示符，不需要自己输入。
- 写完 `def`、`for` 或 `if` 的缩进代码后，输入一个空行才会执行整个块。
- 若还在 `...` 中但想取消未完成的代码块，按 `Ctrl+C` 回到 `>>>`。
- 语法错误（如漏掉 `:`、缩进错误）通常要从该代码块的第一行重新输入。
- 运行时错误（如变量拼错）发生前已执行的语句会保留，但要想完整重跑循环，重新运行整个循环最清楚。

日常写多行代码时，使用 VS Code 编辑 `.py` 文件更舒服：

```text
编辑 .py 文件 → Ctrl+S 保存 → 终端运行 python 文件名.py → 看错误 → 只修改对应行 → 再运行
```

虚拟环境仍然要保持激活；`.venv` 决定使用哪个 Python，`.py` 文件只是保存代码的位置。不要把练习或项目代码放进 `.venv`。

## 9. `pathlib.Path`：处理真实目录

`Path` 是 Python 处理路径的工具。普通字符串如 `"docs"` 没有 `.rglob()` 等路径方法；`Path("docs")` 才是路径对象：

```python
from pathlib import Path

docs_directory = Path("docs")
```

常用方法：

```python
project_root = Path(".")
print(project_root.resolve())  # 当前项目的绝对路径

for item in project_root.iterdir():
    print(item.name)           # 只列出当前目录的一层内容
```

递归查找会进入所有子目录。先只扫 `docs`，避免进入 `.venv` 后打印大量依赖文件：

```python
from pathlib import Path

docs_directory = Path("docs")

for item in docs_directory.rglob("*"):
    if item.is_file():
        print(item.name, "→", item.suffix)
```

- `.rglob("*")`：递归查找所有名称。
- `.is_file()`：只保留文件，忽略文件夹。
- `.name`：文件名，例如 `roadmap.md`。
- `.suffix`：扩展名，例如 `.md`；没有扩展名时返回空字符串 `""`。

`Path.suffix` 正是下一步将真实目录中的文件接入统计器时要使用的工具：空字符串就忽略，否则作为字典的键进行计数。

## 10. JSON：把统计字典保存成通用数据文件

JSON（JavaScript Object Notation）是一种只保存数据的纯文本格式。它常用于不同程序之间交换数据；Python、浏览器和后端服务都能读取它。

CodeAtlas 中的 Python 字典：

```python
{".py": 2, ".md": 1}
```

写成 JSON 文件后是：

```json
{
  ".py": 2,
  ".md": 1
}
```

JSON 的对象对应 Python 的字典，JSON 的数组对应 Python 的列表。当前的“扩展名 → 数量”字典可以直接保存为 JSON，因为键是字符串、值是整数。

Python 使用标准库 `json` 处理它：

```python
import json

json.dump(data, file)    # Python 数据 → 已打开的 JSON 文件
json.dumps(data)         # Python 数据 → JSON 字符串
json.load(file)          # 已打开的 JSON 文件 → Python 数据
json.loads(text)         # JSON 字符串 → Python 数据
```

名称中的 `s` 表示 string（字符串）。当前统计器写文件时使用 `dump`；测试读取文件内容后用 `loads` 解析回来，再比较字典，而不是比较空格和缩进。

JSON 的字符串和对象键必须使用双引号；最后一项后不能有逗号。Python 中的 `True`、`False`、`None` 在 JSON 中分别写作 `true`、`false`、`null`。

生成 JSON 后，可用下面的命令验证它是否是合法 JSON，并以易读格式显示：

```bash
python -m json.tool docs-stats.json
```

## 11. `with`：使用文件后自动关闭

文件打开后应在用完时关闭。`with` 是 Python 的上下文管理语法：进入缩进块时获得资源，离开缩进块时自动清理资源，即使中间发生错误也会关闭文件。

通用结构是：

```python
with 某个资源 as 临时变量:
    使用这个资源的代码
```

统计器中的 JSON 写入函数：

```python
def write_counts_to_json(counts, output_path):
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(counts, file, indent=2)
```

- `output_path.open(...)`：打开该路径的文件。
- `"w"`：写入模式；文件不存在时创建，已存在时覆盖原内容。
- `encoding="utf-8"`：使用 UTF-8 文本编码，能正常处理中文。
- `as file`：将打开后的文件对象命名为 `file`，供缩进块使用。
- `json.dump(...)`：将 `counts` 写入这个已打开的文件。
- `indent=2`：只影响显示格式，让 JSON 更易读。

读文件时也能用相同结构。例如 `readline()` 从当前读取位置读一行文本：

```python
from pathlib import Path

with Path("docs/roadmap.md").open(encoding="utf-8") as file:
    first_line = file.readline()

print(first_line)
```

## 12. 最小命令行参数：`sys.argv`

命令行参数是跟在命令后的额外文本。例如：

```bash
python scanner.py docs docs-stats.json
```

`sys.argv` 是 Python 提供的列表，保存这次运行命令的各部分：

```python
import sys

# 本例中：
# sys.argv[0] 是 "scanner.py"
# sys.argv[1] 是 "docs"
# sys.argv[2] 是 "docs-stats.json"
```

当前 `main()` 取出两个参数，把它们转换为 `Path`，然后完成扫描和写入：

```python
def main():
    directory = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    counts = count_directory_extensions(directory)
    write_counts_to_json(counts, output_path)

    print("Wrote statistics to", output_path)
```

目前只学习了最小用法：运行时必须按顺序提供“目录”和“输出 JSON 文件”。少传参数时还没有友好提示；这属于以后单独学习的错误处理范围。

## 13. `if __name__ == "__main__"`：只在直接运行时启动程序

同一个 `scanner.py` 有两种用途：它可以被直接运行，也可以被测试文件导入以使用其中的函数。

```bash
python scanner.py docs docs-stats.json
```

上面的直接运行会启动完整程序。测试中的导入则只想取得函数：

```python
from scanner import count_extensions
```

Python 会自动设置特殊变量 `__name__`：直接运行 `scanner.py` 时它是 `"__main__"`；导入 `scanner.py` 时它是 `"scanner"`。因此文件末尾写：

```python
if __name__ == "__main__":
    main()
```

它的意思是：只有执行 `python scanner.py ...` 时才调用 `main()`。pytest 导入 `scanner.py` 时条件为假，函数定义仍可被测试使用，但不会自动扫描目录或覆盖 JSON 文件。

`main` 是约定俗成的主入口函数名；`main()` 的括号表示真正调用它。只写 `main` 只是指向这个函数，不会执行。

## 14. API 请求模型和数据库模型：各自负责什么

当前后端用两个名字相近、但职责不同的类处理仓库信息：

```text
浏览器发送 JSON
      ↓
RepositoryCreate（Pydantic：接收并检查请求数据）
      ↓
Repository（SQLAlchemy：一条数据库记录的映射）
      ↓
repositories 表
```

在 `backend/main.py` 中：

```python
class RepositoryCreate(BaseModel):
    name: str
    source_url: str
```

`RepositoryCreate` 是 Pydantic 请求模型。FastAPI 用它说明 `POST /repositories` 期待收到的 JSON 形状：必须有文本类型的 `name` 和 `source_url`。它的工作是处理接口收到的数据；它本身不是数据库表。

在 `backend/models.py` 中：

```python
class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    source_url: Mapped[str]
```

`Repository` 是 SQLAlchemy ORM 模型。ORM 可以理解为“让 Python 类对应数据库表”的工具：这个类描述 `repositories` 表的一行应有哪些列。现在创建接口会把校验后的输入转换为 `Repository` 实例，再写入数据库；两者分开定义，避免把“接口输入”与“数据库记录”混在一起。

`__tablename__` 是**类的配置**，告诉 SQLAlchemy 这个类对应哪张表。它不是某一个仓库自己的数据，因此创建对象时不传它：

```python
# 创建的是一条准备保存的仓库记录
repository = Repository(
    name="CodeAtlas",
    source_url="https://example.com/codeatlas",
)
```

上面的 `name` 和 `source_url` 是实例数据；每个 `Repository(...)` 都可以有不同的值。`__tablename__` 则始终是类上的 `"repositories"`，相当于所有这些记录共同要放进的表名。

`id` 是主键，用来唯一标识一条记录。创建时通常不传 `id`，因为数据库会在真正插入记录时自动生成它；SQLite 的整数主键正适合这种情况。也就是说，上面的对象刚创建时可以还没有可用的 `id`，写入数据库后才得到例如 `1` 的值。当前创建接口会提交记录，再返回包含数据库 `id` 的 JSON。完整请求流程见 [第 2 周复盘](fastapi-sqlite-review.md)。
