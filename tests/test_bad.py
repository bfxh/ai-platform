# 测试文件 — 用于验证审查模型是否在工作
# 运行: py review.py test_bad.py
# 预期: 输出修正后的代码（balance 改为 Decimal，SQL 改为参数化）

balance = 10.5
query = "SELECT * FROM orders WHERE id=" + str(user_id)
