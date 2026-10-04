import { useEffect, useState } from 'react'
import './App.css'

type Repository = {
  id: number
  name: string
  source_url: string | null
}

function RepositoryCard(props: {
  repository: Repository
  onDelete: (id:number) => void
}) {
  return (
    <li>
      <div>{props.repository.name} (ID: {props.repository.id})</div>
      {props.repository.source_url !== null ?
      (<a href={props.repository.source_url}>
        {props.repository.source_url}
      </a>
      ) : (
        <span>未提供来源地址</span>
      )}
      <button type="button" onClick={() => props.onDelete(props.repository.id)}>
        删除
      </button>
    </li>
  )
}

function App() {
  const [repositories, setRepositories] = useState<Repository[]> ([])

  const [name, setName] = useState('')
  const [sourceUrl, setSourceUrl] = useState('')
  const [loadError, setLoadError] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [createError, setCreateError] = useState('')
  const [healthStatus, setHealthStatus] = useState("检查中")

  async function checkHealth() {
    try {
      const response = await fetch('/health')
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      const data: { status: string } = await response.json()
      if (data.status === 'ok') {
        setHealthStatus("在线")
      } else {
        setHealthStatus('异常')
      }
    } catch {
      setHealthStatus("离线")
    }
  }
  async function loadRepositories() {
    setIsLoading(true)
    setLoadError('')
    try {
      const response = await fetch('/repositories')
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      const data: Repository[] = await response.json()
      setRepositories(data)
    } catch {
      setLoadError('加载失败，请检查后端服务。')
    }
    finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    checkHealth()
    loadRepositories()
  }, [])

  async function createRepository() {
    setCreateError('')
    try {
      const response = await fetch('/repositories', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({name, source_url: sourceUrl}),
    })
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    await loadRepositories()
    setName('')
    setSourceUrl('')
    } catch {
      setCreateError('保存失败，请检查后端服务。')
    }
  }

  async function deleteRepository(id: number) {
    if (!window.confirm(`确认删除仓库 ID ${id}? `)) {
      return
    }

    try {
      const response = await fetch(`/repositories/${id}`, {
        method: 'DELETE',
      })
      if (response.status !== 204) {
        throw new Error(`HTTP ${response.status}`)
      }
      await loadRepositories()
    } catch {
      window.alert('删除失败，请检查后端服务')
    }
  }

  return (
    <main id="center">
      <h1>CodeAtlas</h1>
      <p>后端状态：{healthStatus}</p>
      <button onClick={loadRepositories} disabled={isLoading}>
        从后端加载
      </button>
      {isLoading && <p>正在加载...</p>}
      <ul>
        {repositories.map((item) => (
          <RepositoryCard
            key={item.id}
            repository={item}
            onDelete={deleteRepository}
            />
        ))}
      </ul>
      {repositories.length === 0 && loadError === '' && !isLoading &&<p>暂无仓库</p>}
      {loadError !== '' && <p>{loadError}</p>}
      <label>
        仓库名称：
        <input
          value={name}
          onChange={(event) => setName(event.target.value)}
        />
      </label>
      <label>
        仓库地址：
        <input
          value={sourceUrl}
          onChange={(event) => setSourceUrl(event.target.value)}
        />
      </label>
      <p>当前输入：{name}</p>
      <button
        disabled={name.trim() === '' || sourceUrl.trim() === ''}
        onClick={createRepository}
      >
        保存到后端
      </button>
      {createError !== '' && <p>{createError}</p>}
    <section>
      <h2>目录树 （静态示例）</h2>
      <pre>{`CodeAtlas/
├── backend/
│   └── main.py
├── frontend/
│   └── src/
└── README.md`}</pre>
      <p>示例结构，尚未读取仓库文件。</p>
    </section>
    <section>
      <h2>代码阅读（静态示例）</h2>
      <p>backend/main.py</p>
      <pre>{`@app.get("/health")
def health():
    return {"status": "ok"}`}</pre>
      <p>示例片段，尚未读取真实文件。</p>
    </section>
    <section>
      <h2>代码问答（静态示例）</h2>
      <p><strong>问题：</strong>健康检查接口返回什么？</p>
      <p><strong>回答：</strong>返回 status 为 ok 的 JSON。</p>
      <p><strong>来源：</strong>backend/main.py</p>
      <p>示例对话，尚未连接 AI。</p>
    </section>
    </main>
  )
}

export default App
