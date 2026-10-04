from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.models import Base, Repository, SourceFile

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


def test_source_file_is_saved_and_loaded_with_repository():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        repository = Repository(
            name="CodeAtlas",
            source_url=None,
        )
        session.add(repository)
        session.commit()
        repository_id = repository.id

        source_file = SourceFile(
            repository_id=repository_id,
            path="src/main.py",
            content="print('你好')\n",
        )
        session.add(source_file)
        session.commit()
        source_file_id = source_file.id

    # 使用新的 Session，确认数据可从数据库重新读回。
    with Session() as session:
        saved_file = session.get(SourceFile, source_file_id)

        assert saved_file is not None
        assert saved_file.repository_id == repository_id
        assert saved_file.path == "src/main.py"
        assert saved_file.content == "print('你好')\n"
        saved_repository = session.get(Repository, saved_file.repository_id)
        assert saved_repository is not None
        assert saved_repository.source_url is None
