# 首次答案

五份 JSONL 合计 3,750 条记录。`firstAnswer` 为首次最终答案，`checks` 为原始逐项规则结果。

| 文件 | 记录数 |
|---|---:|
| starter-10.jsonl | 380 |
| luna-low-614.jsonl | 614 |
| sol55astra-low-614.jsonl | 1,842 |
| 56sol-low-614.jsonl | 614 |
| paused-xhigh-614.jsonl | 300 |

从仓库根目录运行 `python verify_results.py` 核验哈希及成绩；运行 `python verify_results.py --regrade` 使用固定上游检查器复核原答卷，两者均不调用模型。
