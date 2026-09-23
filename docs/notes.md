pytest 的最小规则：
  |----|----|
  |tests/test_*.py|        → pytest 会自动发现|
  |test_开头的函数  |      → pytest 会执行|
  |assert 条件 |           → 条件为真通过；为假失败|

# 流程
项目环境先创建**venv**环境，然后**pytest**测试