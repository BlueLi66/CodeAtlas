from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models import Base, Repository

# 测试 Repository 类 → 创建 Python 对象 → 对象保存字段值
def test_repository_model_keeps_its_fields():
    repository = Repository(
        name = "CodeAtlas",
        source_url = "https://github.com/example/codeatlas"
    )
    
    assert repository.name == "CodeAtlas"
    assert repository.source_url == "https://github.com/example/codeatlas"
    
# 临时内存数据库测试 add → commit → id 流程
def test_repository_gets_id_after_being_saved():
    # 只存在于内存中的临时 SQLite 数据库；测试结束就消失，不修改 codeatlas.db
    engine = create_engine("sqlite://")
    # 创建 repositories 表
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    
    with Session() as session:
        repository = Repository(
            name = "CodeAtlas",
            source_url = "https://github.com/example/codeatlas"
        )
        
        session.add(repository)
        session.commit()
        
        # id 作为主键会自动生成
        assert repository.id is not None