import json
from scanner import (
    count_directory_extensions,
    count_extensions,
    write_counts_to_json
)

def test_counts_extensions_and_ignores_extensions_files():
    filenames = ["main.py", "README.md", "LICENSE", "api.py"]
    result = count_extensions(filenames)
    assert result == {".py":2, ".md": 1}

# tmp_path / "main.py"：拼出临时目录下的文件路径
# .write_text("")：创建一个空文本文件
def test_counts_directory_extensions_recursively(tmp_path):
    (tmp_path / "main.py").write_text("")
    (tmp_path / "LICENSE").write_text("")
    src_directory = tmp_path / "src"
    src_directory.mkdir()
    (src_directory / "api.py").write_text("")
    (src_directory / "README.md").write_text("")
    
    result = count_directory_extensions(tmp_path)
    
    assert result == {".py": 2, ".md": 1}
    
def test_writes_counts_to_json(tmp_path):
    counts = {".py": 2, ".md": 1}
    output_path = tmp_path / "counts.json"
    
    write_counts_to_json(counts, output_path)
    
    saved_counts = json.loads(output_path.read_text(encoding="utf-8"))
    assert saved_counts == counts
    
