from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Repository

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
        
    db.delete(db_repository)
    db.commit()
        