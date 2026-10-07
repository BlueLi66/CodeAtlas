import { useEffect, useState } from 'react'
import './App.css'

type Repository = {
  id: number
  name: string
  source_url: string | null
}

type SourceFile = {
  id: number
  repository_id: number
  path: string
}

type TreeNode =
  | {
      kind: 'directory'
      name: string
      children: TreeNode[]
    }
  | {
      kind: 'file'
      name: string
      file: SourceFile
    }

// 正文接口返回清单中的三个字段，并额外包含 content。
type SourceFileDetail = SourceFile & {
  content: string
}

type RepositoryImportResult = Repository & {
  file_count: number
}

function buildFileTree(files: SourceFile[]): TreeNode[] {
  const roots: TreeNode[] = []

  for (const file of files) {
    // 只整理显示层级，原始 file.path 和文件 ID 不变。
    const parts = file.path
      .split("/")
      .filter((part) => part !== '' && part !== ".")

    let children = roots

    for (let index = 0; index < parts.length; index += 1) {
      const name = parts[index]

      if (index === parts.length - 1) {
        children.push({
          kind: 'file',
          name,
          file,
        })
      } else {
        const existing = children.find(
          (node) =>
            node.kind === 'directory' && node.name === name,
        )

        if (existing?.kind === 'directory') {
          children = existing.children
        } else {
          const directory: TreeNode = {
            kind: 'directory',
            name,
            children: [],
          }

          children.push(directory)
          children = directory.children
        }
      }
    }
  }
  return roots
}

function FileTree(props: {
  nodes: TreeNode[]
  onSelect: (file: SourceFile) => void
  isBusy: boolean
}) {
  return (
    <ul className='file-tree'>
      {props.nodes.map((node) => (
        <li
          key={
            node.kind === 'directory'
             ? `directory:${node.name}`
             : `file:${node.file.id}`
          }
        >
          {node.kind === 'directory' ? (
            <>
              <span>{node.name}</span>

              <FileTree
                nodes={node.children}
                onSelect={props.onSelect}
                isBusy={props.isBusy}
              />
            </>
          ) : (
            <button
              type='button'
              disabled={props.isBusy}
              onClick={() => props.onSelect(node.file)}
            >
              {node.name}
            </button>
          )}
        </li>
      ))}
    </ul>
  )
}

function RepositoryCard(props: {
  repository: Repository
  onDelete: (id:number) => void
  onSelect: (repository: Repository) => void
  isBusy: boolean
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
      <button
        type="button"
        disabled={props.isBusy}
        onClick={() => props.onSelect(props.repository)}
      >
        查看文件
      </button>

      <button
        type="button"
        disabled={props.isBusy}
        onClick={() => props.onDelete(props.repository.id)}
      >
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

  const [selectedRepository, setSelectedRepository] = useState<Repository | null>(null)

  const [sourceFiles, setSourceFiles] = useState<SourceFile[]>([])
  const [isFilesLoading, setIsFilesLoading] = useState(false)
  const [filesError, setFilesError] = useState('')
  const [isDeletingRepository, setIsDeletingRepository] = useState(false)

  // null 表示还没有加载到文件正文；空正文则是 content 为 '' 的详情对象。
  const [selectedFile, setSelectedFile] =
    useState<SourceFileDetail | null>(null)
  const [isFileLoading, setIsFileLoading] = useState(false)
  const [fileError, setFileError] = useState('')

  const [importName, setImportName] = useState('')
  const [archiveFile, setArchiveFile] = useState<File | null>(null)
  const [isImporting, setIsImporting] = useState(false)
  const [importError, setImportError] = useState('')
  const [importSuccess, setImportSuccess] = useState('')
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
    // 导入期间不再创建另一条仓库记录，避免两次操作同时刷新列表。
    if (isImporting) {
      return
    }
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
    // 导入、清单／正文加载或删除期间暂不接受新操作。
    if (isImporting || isFilesLoading || isFileLoading || isDeletingRepository) {
      return
    }
    if (!window.confirm(`确认删除仓库 ID ${id}? `)) {
      return
    }

    setIsDeletingRepository(true)
    try {
      const response = await fetch(`/repositories/${id}`, {
        method: 'DELETE',
      })
      if (response.status !== 204) {
        throw new Error(`HTTP ${response.status}`)
      }

      // 后端确认删除成功后，只清空当前选中仓库对应的阅读状态。
      // 删除其他仓库时，保留正在查看的文件清单。
      if (selectedRepository?.id === id) {
        setSelectedRepository(null)
        setSourceFiles([])
        setFilesError('')
        setSelectedFile(null)
        setFileError('')
      }
      await loadRepositories()
    } catch {
      window.alert('删除失败，请检查后端服务')
    } finally {
      // 成功或失败都恢复按钮，允许继续选择仓库或重试删除。
      setIsDeletingRepository(false)
    }
  }

  async function selectRepository(repository: Repository) {
    if (isImporting || isFilesLoading || isFileLoading || isDeletingRepository) {
      return
    }

    setSelectedRepository(repository)
    setSourceFiles([])
    setFilesError('')
    // 仓库变化后，上一仓库的正文与阅读错误也必须清除。
    setSelectedFile(null)
    setFileError('')
    setIsFilesLoading(true)

    try {
      const response = await fetch(
        `/repositories/${repository.id}/files`,
      )
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data: SourceFile[] = await response.json()
      setSourceFiles(data)
    } catch {
      setFilesError(`文件清单加载失败，请检查后端服务后重试。`)
    } finally {
      setIsFilesLoading(false)
    }
  }

  async function selectFile(file: SourceFile) {
    // 只读取当前仓库的文件；其他选择或删除操作进行中时，不再发起请求。
    if (
      selectedRepository === null ||
      file.repository_id !== selectedRepository.id ||
      isImporting ||
      isFilesLoading ||
      isFileLoading ||
      isDeletingRepository
    ) {
      return
    }

    // 新请求开始时清除旧正文和错误，避免把上一份内容当成当前文件。
    setSelectedFile(null)
    setFileError('')
    setIsFileLoading(true)

    try {
      // repository_id 确定所属仓库，id 确定要读取的具体文件。
      const response = await fetch(
        `/repositories/${file.repository_id}/files/${file.id}`,
      )
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      // JSON 解析为一个详情对象；这里的类型标注不是运行时数据校验。
      const data: SourceFileDetail = await response.json()
      setSelectedFile(data)
    } catch {
      setFileError('正文加载失败，请检查后端服务后重试。')
    } finally {
      // 无论成功或失败，都结束加载状态。
      setIsFileLoading(false)
    }
  }

  async function importRepository() {
    if (
      isImporting ||
      isLoading ||
      isDeletingRepository ||
      // 这里 .trim() 是 JavaScript 的字符串方法，用来去掉开头和结尾的空白字符
      importName.trim() === '' ||
      archiveFile === null
    ) {
      return
    }
    setIsImporting(true)
    setImportError('')
    setImportSuccess('')

    const formData = new FormData()
    formData.append('name', importName.trim())
    formData.append('archive', archiveFile)

    try {
      const response = await fetch('/repositories/import', {
        method: 'POST',
        body: formData,
      })

      if (response.status !== 201) {
        const errorData: { detail?: unknown } =
          await response.json().catch(() => ({}))
        throw new Error(
          typeof errorData.detail === 'string'
            ? errorData.detail
            : `导入失败（HTTP ${response.status}）`,
        )
      }
      const data: RepositoryImportResult = await response.json()

      setImportSuccess(
        `仓库“${data.name}”导入成功，保存了 ${data.file_count} 个文件。`,
      )

      await loadRepositories()
    } catch(error) {
      setImportError(
        error instanceof TypeError
          ? '无法连接后端，请检查服务后重试。'
          : error instanceof Error
            ? error.message
            : '导入失败，请重试。',
      )
    } finally {
      setIsImporting(false)
    }
  }

  const fileTree = buildFileTree(sourceFiles)

  return (
    <main id="center">
      <h1>CodeAtlas</h1>
      <p>后端状态：{healthStatus}</p>
      <button onClick={loadRepositories} disabled={isLoading || isImporting}>
        从后端加载
      </button>
      {isLoading && <p>正在加载...</p>}
      <ul>
        {repositories.map((item) => (
          <RepositoryCard
            key={item.id}
            repository={item}
            onDelete={deleteRepository}
            onSelect={selectRepository}
            isBusy={isImporting || isFilesLoading || isFileLoading || isDeletingRepository}
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
        disabled={isImporting || name.trim() === '' || sourceUrl.trim() === ''}
        onClick={createRepository}
      >
        保存到后端
      </button>
      {createError !== '' && <p>{createError}</p>}

      <section>
        <h2>导入 ZIP 仓库</h2>

        <label>
          仓库名称：
            <input
              value={importName}
              disabled={isImporting}
              onChange={(event) => {
                setImportName(event.target.value)
                setImportError('')
                setImportSuccess('')
              }}
            />
        </label>

        <label>
          ZIP 文件：
          <input
            type="file"
            accept='.zip'
            disabled={isImporting}
            onChange={(event) => {
              const file = event.currentTarget.files?.[0] ?? null
                setArchiveFile(file)
                setImportError('')
                setImportSuccess('')
            }}
          />
        </label>
        <button
          type="button"
          disabled={
            isImporting ||
            isLoading ||
            isDeletingRepository ||
            importName.trim() === '' ||
            archiveFile === null
          }
          onClick={importRepository}
        >
          {isImporting ? '正在导入...' : '导入 ZIP'}
        </button>

        {importError !== '' && (
          <p role="alert">{importError}</p>
        )}

        {importSuccess !== '' && (
          <p role="status">{importSuccess}</p>
        )}
      </section>

      <section>
        <h2>文件清单</h2>

        {selectedRepository === null ? (
          <p>请选择一个仓库查看文件。</p>
        ) : (
          <>
            <p>当前仓库：{selectedRepository.name}</p>

            {isFilesLoading && <p>正在加载文件...</p>}
            {filesError !== '' && <p role="alert">{filesError}</p>}

            {!isFilesLoading && filesError === '' && (
              sourceFiles.length === 0 ? (
                <p>这个仓库没有可浏览的文件。</p>
              ) : (
                <FileTree
                  nodes={fileTree}
                  onSelect={selectFile}
                  isBusy={
                    isImporting ||
                    isFilesLoading ||
                    isFileLoading ||
                    isDeletingRepository
                  }
                />
              )
            )}
          </>
        )}
      </section>

      <section>
        <h2>代码阅读</h2>

        {isFileLoading && <p>正在加载正文...</p>}
        {fileError !== '' && <p role="alert">{fileError}</p>}

        {!isFileLoading && fileError === '' && (
          selectedFile === null ? (
            <p>请从文件清单中选择一个文件。</p>
          ) : (
            <>
              <p>{selectedFile.path}</p>
              {selectedFile.content === '' ? (
                <p>这是一个空文件。</p>
              ) : (
                // React 按文本显示源码，不把文件内容当成 HTML 或脚本执行。
                <pre><code>{selectedFile.content}</code></pre>
              )}
            </>
          )
        )}
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
