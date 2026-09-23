# tests/conftest.py 用于存放可复用的测试工具；其中以 @pytest.fixture 标记的函数，可以按名字注入测试函数

import pytest

# 导入 FastAPI 的测试客户端 在 Python 内部模拟浏览器发送
from fastapi.testclient import TestClient

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import get_db
from backend.main import app
from backend.models import Base

@pytest.fixture
def repository_client(tmp_path):
    database_path = tmp_path / "test-codeatlas.db"
    test_engine = create_engine(f"sqlite:///{database_path}")
    Base.metadata.create_all(test_engine)
    
    TestSessionLocal = sessionmaker(bind=test_engine)
    
    def override_get_db():
        with TestSessionLocal() as db:
            yield db
    '''
    dependency_overrides 可以理解为 FastAPI 的“测试替换表”：
    正常情况: Depends(get_db) → get_db
    测试情况: Depends(get_db) → override_get_db
    这里的 get_db 和 override_get_db 都没有 ()，因为放进去的是函数本身，不是在这一行立刻调用它。
'''
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()