import { useEffect, useState } from 'react'
import './App.css'

type Repository = {
  id: number
  name: string
  source_url: string
}

function RepositoryCard(props: {
  repository: Repository
  onDelete: (id:number) => void
}) {
  return (
    <li>
      <div>{props.repository.name} (ID: {props.repository.id})</div>
      <a href={props.repository.source_url}>
        {props.repository.source_url}
      </a>
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
    </main>
  )
}

export default App
