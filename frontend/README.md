# CodeAtlas 前端

使用 React、TypeScript 和 Vite，已接入后端仓库列表、新增、删除和健康检查接口。

ZIP 上传目前通过后端 API 文档操作；前端尚无上传按钮，目录树、代码阅读和问答区域仍是静态示例。

## 本地开发

先按 [项目 README](../README.md) 启动后端。在项目根目录另开终端运行：

```bash
npm --prefix frontend ci
npm --prefix frontend run dev
```

打开 Vite 终端输出的页面地址，检查仓库列表和后端状态。

开发服务器将 `/health` 和 `/repositories` 请求代理到 `http://127.0.0.1:8000`。这只是开发环境代理，生产环境转发尚未配置。

## 构建与代码检查

同样在项目根目录执行：

```bash
npm --prefix frontend run build
npm --prefix frontend run lint
```

构建结果输出到 `frontend/dist/`。构建成功不等于 API 连通；接口交互仍需在后端运行时通过页面验证。
