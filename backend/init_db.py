from backend.database import engine
from backend.models import Base

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    print("数据库表已就绪")