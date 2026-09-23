from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./codeatlas.db"

engine = create_engine(DATABASE_URL)

# 数据库工作会话
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    
    # yield 会话暂时交给路由，但函数暂不结束
    try:
        yield db
    finally:
        db.close()