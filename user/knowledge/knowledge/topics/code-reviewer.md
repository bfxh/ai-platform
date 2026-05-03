# 代码审查官系统

> 来源: \python\code_reviewer.py (370L) + \python\ai-plugin\rules\code_review_rules.md

## 架构

```
RulesLoader(文件→规则提取) → CodeReviewer(后端探测+负载均衡+审查) → Ollama(qwen2.5-coder:3b)
```

## 规则加载

从 `\python\ai-plugin\rules\code_review_rules.md` 按语言提取:
- 通用规则(所有语言)
- Python规则(Decimal/参数化SQL/snake_case/PascalCase)
- JavaScript/TypeScript规则(BigNumber/参数化SQL/camelCase/禁止any)
- Go规则(decimal.Decimal/参数化SQL/CamelCase/错误处理)
- Java规则(BigDecimal/PreparedStatement/PascalCase+camelCase/try-with-resources)

提取算法: Markdown `##` 标题分段, 正则匹配, 带缓存

## 后端探测

_probe_backends(): 每30秒socket探测可用后端, 自动跳过不可达节点
BACKENDS: ["http://192.168.1.6:11434","http://127.0.0.1:11434"]
_select_backend(): 从可用后端随机选择(负载均衡)

## Prompt模板

ChatML格式: `<|im_start|>system`(严格审查专家)→`<|im_start|>user`(规则+代码)→`<|im_start|>assistant`
temperature=0(确定性), num_predict=4096

## 语言检测

def→python, function/const/let→javascript, type/interface→typescript, package/func→go, class+public→java

## CLI

```bash
python code_reviewer.py --test          # 多语言测试
python code_reviewer.py --test-lang js  # 查看指定语言规则
echo "code" | python code_reviewer.py   # stdin模式(自动检测语言)
```
