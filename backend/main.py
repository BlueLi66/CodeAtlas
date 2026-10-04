from fastapi import Depends, FastAPI, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Repository, SourceFile
from backend.archive import inspect_candidate_entries, read_entry_text
class RepositoryCreate(BaseModel):
    name: str
    source_url: str

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/repositories", status_code=201)
def create_repository(
    repository: RepositoryCreate,
    db: Session = Depends(get_db),
 ):
    db_repository = Repository(
        name=repository.name,
        source_url=repository.source_url,
    )
    
    db.add(db_repository)
    db.commit()
    
    db.refresh(db_repository)
    
    return {
        "id": db_repository.id,
        "name": db_repository.name,
        "source_url": db_repository.source_url,
    }
    
@app.get("/repositories")
def list_repositories(db: Session = Depends(get_db)):
    # db.scalars(...) 得到 Repository 对象, .all() 收集成 Python 列表
    stored_repositories = db.scalars(select(Repository)).all()
    
    results = []
    
    for repository in stored_repositories:
        results.append(
            {
                "id": repository.id,
                "name": repository.name,
                "source_url": repository.source_url,
            }
        )
    return results

@app.delete("/repositories/{repository_id}", status_code=204)
def delete_repository(
    repository_id:int, 
    db: Session = Depends(get_db),
):
    db_repository = db.get(Repository, repository_id)
    
    if db_repository is None:
        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )
        
    # 先删除这个仓库所属的文件，避免删除仓库后留下没有归属的文件。
    # where(...) 限定仓库 ID，不会删除其他仓库的文件。
    db.execute(
        delete(SourceFile).where(
            SourceFile.repository_id == repository_id
        )
    )
    db.delete(db_repository)
    # 文件和仓库在同一个事务里一起提交。
    db.commit()


@app.post("/archives/inspect")
def inspect_archive(archive: UploadFile):
    try:
        entries = inspect_candidate_entries(
            archive.file,
            max_file_bytes=1_000_000,
            max_total_bytes=10_000_000,
        )
        for entry in entries:
            read_entry_text(archive.file, entry, max_file_bytes=1_000_000)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    return {"candidate_files": [entry.filename for entry in entries]}


@app.post("/repositories/import", status_code=201)
def import_repository(
    archive: UploadFile,
    name: str = Form(...),
    db: Session = Depends(get_db),
):
    """检查 ZIP，并在同一个事务中保存仓库及候选文件。"""
    # Form(...) 表示名称来自必填表单字段；UploadFile 接收同一表单里的 ZIP。
    # strip() 去掉两端空白，也能识别只填写了空格的名称。
    repository_name = name.strip()
    if not repository_name:
        raise HTTPException(status_code=400, detail="仓库名称不能为空")

    # 第一阶段：检查并读完所有候选文件，暂不写数据库。
    # 复用现有的路径、大小、类型筛选和 UTF-8 读取规则。
    try:
        entries = inspect_candidate_entries(
            archive.file,
            max_file_bytes=1_000_000,
            max_total_bytes=10_000_000,
        )
        if not entries:
            raise ValueError("ZIP 中没有可导入的 .py 或 .md 文件")

        # 每一项保存一个文件的相对路径和正文，供下一阶段使用。
        parsed_files = []
        for entry in entries:
            content = read_entry_text(
                archive.file, entry, max_file_bytes=1_000_000
            )
            parsed_files.append({
                "path": entry.filename,
                "content": content,
            })
    except ValueError as error:
        # 文件检查失败属于请求内容问题，返回 400；此时还没有保存任何数据。
        raise HTTPException(status_code=400, detail=str(error)) from error

    # 第二阶段：仓库和文件使用同一个 Session、同一个事务。
    try:
        # 本地上传没有来源网址，用 None 表示；创建对象本身不会执行 INSERT。
        db_repository = Repository(
            name=repository_name,
            source_url=None,
        )

        # 把仓库加入 Session，然后 flush 获取仓库 ID。
        # flush 执行待保存操作，但不提交，所以之后仍然能回滚。
        db.add(db_repository)
        db.flush()

        # 遍历读取结果，创建并添加每个文件模型对象。
        # repository_id 使用 db_repository.id；path 和 content 取自当前字典。
        # 循环内只添加文件，不要 commit，以免保存一半后无法整体回滚。
        for parsed_file in parsed_files:
            source_file = SourceFile(
                repository_id=db_repository.id,
                path=parsed_file["path"],
                content=parsed_file["content"],
            )
            db.add(source_file)

        # 在提交前保存 ID，避免响应时再依赖提交后的 ORM 对象读取。
        repository_id = db_repository.id
        # 只提交一次：仓库和全部文件一起保存；commit 会自动 flush 待保存操作。
        db.commit()
    except SQLAlchemyError as error:
        # 数据库保存出错时，撤销本次事务，不影响此前已经提交的仓库。
        db.rollback()
        # 对外不返回数据库内部错误细节。
        raise HTTPException(
            status_code=500,
            detail="导入保存失败，请重试",
        ) from error

    # Python 的 None 会在 JSON 响应中成为 null；不在响应中发送全部源码。
    return {
        "id": repository_id,
        "name": repository_name,
        "source_url": None,
        "file_count": len(parsed_files),
    }

@app.get("/repositories/{repository_id}/files")
def list_repository_files(
    repository_id: int,
    db: Session = Depends(get_db),
):
    """返回指定仓库的文件清单，不包含文件正文。"""
    # 先区分“仓库不存在”和“仓库存在但没有文件”。
    repository = db.get(Repository, repository_id)
    if repository is None:
        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )
    # 注意筛选的是文件的所属仓库 ID，而不是文件自己的 ID
    statement = (
        select(SourceFile)
        .where(SourceFile.repository_id == repository_id)
        .order_by(SourceFile.path, SourceFile.id)
    )
    stored_files = db.scalars(statement).all()

    results = []
    for source_file in stored_files:
        results.append({
            "id": source_file.id,
            "repository_id": source_file.repository_id,
            "path": source_file.path,
        })

    return results

@app.get("/repositories/{repository_id}/files/{file_id}")
def get_repository_file(
    repository_id: int,
    file_id: int,
    db: Session = Depends(get_db),
):
    """读取指定仓库中的一个文件，返回路径和完整正文。"""
    repository = db.get(Repository, repository_id)
    if repository is None:
        raise HTTPException(
            status_code=404,
            detail="Repository not found",
        )

    statement = select(SourceFile).where(
        SourceFile.id == file_id,
        SourceFile.repository_id == repository_id,
    )
    source_file = db.scalar(statement)

    if source_file is None:
        raise HTTPException(
            status_code=404,
            detail="Source file not found",
        )

    return {
        "id": source_file.id,
        "repository_id": source_file.repository_id,
        "path": source_file.path,
        "content": source_file.content,
    }
