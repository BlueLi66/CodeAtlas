from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Base: 所有数据库模型的共同父类
class Base(DeclarativeBase):
    pass
class Repository(Base):
    __tablename__ = "repositories"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    source_url: Mapped[str]
    
    
    


