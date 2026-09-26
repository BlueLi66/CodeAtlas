# 第 3 周复盘：React + TypeScript 的仓库清单

这一周的目标不是学完前端，而是让浏览器完成一次“输入 → 请求 → 后端保存 → 刷新列表”的闭环。当前页面还能读取列表、确认删除，并在读取或保存失败时给出提示。后端的数据库流程见 [第 2 周复盘](fastapi-sqlite-review.md)。

## 1. 先看完整数据流

```text
输入框 → name/sourceUrl 状态 → 点击“保存到后端”
       → POST /repositories → FastAPI 校验 → SQLite 保存
       → 前端再次 GET /repositories → setRepositories(新列表)
       → React 重新渲染 RepositoryCard
```

这里有两个不同的“保存”：后端的 `db.commit()` 保存到数据库；前端的 `setRepositories(...)` 只更新浏览器页面中的状态。POST 成功后若不重新读取或更新前端状态，数据已经入库，但当前列表不会立即变化；刷新页面时自动加载后才会看到它。

## 2. TypeScript：描述数据的形状

```tsx
type Repository = {
  id: number
  name: string
  source_url: string
}

const [repositories, setRepositories] = useState<Repository[]>([])
```

- `Repository` 描述一条仓库记录的字段及类型；`Repository[]` 表示由多条记录组成的数组。
- `useState<Repository[]>([])` 中，`<Repository[]>` 是类型参数，`(...)` 是函数调用，里面的 `[]` 是初始空数组。
- 左边的 `[repositories, setRepositories]` 是数组解构：分别取得当前值与更新函数，不是在读取数组下标。
- `const data: Repository[] = await response.json()` 是对预期结果的静态标注；TypeScript 不会在运行时检查后端 JSON 是否真的符合该类型。
- `sourceUrl` 是前端变量名，`source_url` 是 API 数据字段名；创建请求用 `source_url: sourceUrl` 把两者对应起来。

## 3. React：组件、Props、列表与事件

`App` 拥有仓库列表和请求函数；`RepositoryCard` 负责显示一条记录。`App` 通过 `repository={item}` 把当前数组项传给卡片，卡片用 `props.repository.name` 等字段读取它。

```tsx
{repositories.map((item) => (
  <RepositoryCard
    key={item.id}
    repository={item}
    onDelete={deleteRepository}
  />
))}
```

- `map` 把数组中的每一条记录变成一个组件。`key={item.id}` 帮助 React 区分列表项；`key` 是 React 的特殊属性，不会作为普通 `props.key` 传给卡片。
- `repository` 和 `onDelete` 是自己定义的 Props。`onDelete: (id: number) => void` 表示卡片拿到一个接收数字 ID、不要求返回值的函数；这里的 `void` 不是删除操作。
- 卡片按钮里的 `onClick={() => props.onDelete(props.repository.id)}` 把当前卡片 ID 传回 `App`。`onDelete={deleteRepository}` 把处理函数传给自定义组件；箭头函数让卡片在点击时才携带自己的 ID 调用它。
- `type="button"` 表示普通按钮；卡片本身不直接操作数据库，而是让 `App` 处理删除请求。

## 4. 状态、输入框与首次加载

`useState` 让组件记住会变化的数据。`setName(...)`、`setSourceUrl(...)` 改变输入状态，`setRepositories(...)` 改变列表状态；React 随后重新渲染。调用这些更新函数本身不会向数据库发送请求。

```tsx
<input value={name} onChange={(event) => setName(event.target.value)} />
```

输入框的值由 `name` 状态控制。用户打字 → `onChange` 读到 `event.target.value` → `setName` 更新状态 → 输入框显示新值。保存成功后调用 `setName('')` 和 `setSourceUrl('')`，两个输入框就会清空。

`useEffect(() => { loadRepositories() }, [])` 让页面出现后自动发起 GET；手动“从后端加载”按钮则由点击事件触发同一个函数。`isLoading` 初始设为 `true`，避免首次请求尚未开始时误显示“暂无仓库”。当前项目启用了 `StrictMode`，开发模式可能看到两次 GET；读取请求可以重复，POST 创建请求仍只放在点击事件里。

## 5. fetch、JSON、状态码和失败路径

| 请求 | 前端做什么 | 后端成功响应 |
| --- | --- | --- |
| `GET /repositories` | `await response.json()` 得到数组，更新列表 | `200`；没有记录时是 `[]` |
| `POST /repositories` | 用 `JSON.stringify({ name, source_url: sourceUrl })` 生成 JSON 请求体，并设置 `Content-Type: application/json` | `201`；创建记录 |
| `DELETE /repositories/${id}` | 先用 `window.confirm` 确认，再把卡片 ID 放进路径；成功后重新读取列表 | `204`；无响应内容，不调用 `response.json()` |

`fetch` 是异步请求；`await` 等待响应，`response` 是响应对象，不是解析后的数据。网络失败会使请求抛错；收到 `404`、`500` 等 HTTP 错误响应时，`fetch` 不会仅因状态码自动抛错，所以代码还检查 `response.ok` 或预期状态码。`try/catch` 将失败变为页面提示；`finally` 让读取请求结束后关闭加载状态。

前端请求写 `/repositories`，开发时由 `frontend/vite.config.ts` 的代理转发到 `127.0.0.1:8000`。这只是 Vite 开发服务器配置，不等于生产环境已经部署好代理。

## 6. 条件渲染与基础样式

`{isLoading && <p>正在加载...</p>}` 表示条件为真才显示提示；`{repositories.length === 0 && ...}` 用来显示空列表。`&&` 左边最好明确得到布尔值，不要直接写 `repositories.length && <p>...</p>`，否则长度为 `0` 时可能把数字 `0` 显示出来。

`disabled={name.trim() === '' || sourceUrl.trim() === ''}` 在任一输入为空或只有空格时禁用保存按钮；`||` 表示“或者”。这只检查非空，不验证 URL 格式或网址是否可访问。页面布局由 `App.css` 和 `index.css` 管理，例如 `#center` 选择 `id="center"` 的元素；样式与数据状态是不同职责。

## 7. 容易混淆的语法

- JavaScript/TypeScript 的反引号模板字符串会替换 `${id}`：`` `/repositories/${id}` ``。单引号 `'/repositories/${id}'` 只得到原样文字；这类似 Python 的 f-string，但写法不同。
- 小写 `response.status` 是这次 `fetch` 得到的响应状态；大写 `Response` 是浏览器提供的构造器，不是同一个变量。
- `{name}` 在 JSX 中插入 JavaScript 值；对象里的 `{ name: name }` 是“字段名对应变量值”，花括号用途不同。
- `[]` 既可表示空数组，也可出现在解构赋值左边；要结合位置判断。`useEffect(..., [])` 的空数组则是依赖列表。
- `[]`（成功返回空列表）与请求失败不同：前者显示“暂无仓库”，后者显示错误提示。

## 8. 在当前本机项目中验证

数据库表已在本机初始化的前提下，从项目根目录启动后端：

```bash
source .venv/bin/activate
python -m uvicorn backend.main:app --reload
```

另开终端，在 `frontend/` 目录启动页面：

```bash
cd frontend
npm run dev
```

开发服务器会持续运行。要检查构建，可另开一个位于 `frontend/` 的终端，或先按 `Ctrl+C` 停止开发服务器，再运行 `npm run build`。

浏览器查看 `http://localhost:5173/`；直接查看 API 列表可打开 `http://localhost:8000/repositories`。后端自动测试可在项目根目录运行 `python -m pytest tests/`。当前前端构建通过，后端测试为 `12 passed`；依赖弃用警告与失败不同。

## 9. 自测题

1. POST 已返回 `201`，但没有调用 `loadRepositories()`；数据库和当前页面列表分别会怎样？
2. 为什么 `onDelete={deleteRepository}` 不会在页面渲染时立刻删除？
3. `response.ok`、`response.json()`、`setRepositories(data)` 分别负责什么？
4. 为什么首次加载时 `isLoading` 的初始值是 `true`？
5. 为什么 DELETE 成功返回 `204` 后不能直接读取 JSON 响应体？

当前没有系统学习 React 路由、状态管理库或生产部署；`npm run lint` 尚有一条 Effect 中同步设置状态的警告。它不影响现有构建，但后续整理自动加载逻辑时需要处理。

## 10. 继续查阅的官方资料

- [TypeScript 日常类型与数组](https://www.typescriptlang.org/docs/handbook/2/everyday-types.html)
- [React：useState](https://react.dev/reference/react/useState) 与 [useEffect](https://react.dev/reference/react/useEffect)
- [MDN：使用 Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch)
- [Vite：开发服务器代理](https://vite.dev/config/server-options.html#server-proxy)
