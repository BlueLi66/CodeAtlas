from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import ForeignKey
# Base: 所有数据库模型的共同父类
class Base(DeclarativeBase):
    pass
class Repository(Base):
    __tablename__ = "repositories"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    source_url: Mapped[str | None]
    
class SourceFile(Base):
    __tablename__ = "source_files"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id"))
    path: Mapped[str]
    content: Mapped[str]
    
