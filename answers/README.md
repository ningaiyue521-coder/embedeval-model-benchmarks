# 首次答案

15 份 JSONL 合计 **9,403 条记录**。其中七模型完整 Low / 极高总榜采用 8,596 份首答；其他历史试跑或暂停记录不计入全量排名。`firstAnswer` 为首次最终答案，`checks` 为原始逐项规则结果。

| 文件 | 记录数 |
|---|---:|
| [20260928-gpt-5.5-xhigh.jsonl](20260928-gpt-5.5-xhigh.jsonl) | 614 |
| [20260928-gpt-5.6-luna-low.jsonl](20260928-gpt-5.6-luna-low.jsonl) | 614 |
| [20260928-gpt-5.6-luna-xhigh.jsonl](20260928-gpt-5.6-luna-xhigh.jsonl) | 614 |
| [20260928-gpt-5.6-sol-xhigh.jsonl](20260928-gpt-5.6-sol-xhigh.jsonl) | 614 |
| [20260928-gpt-5.6-terra-low-partial.jsonl](20260928-gpt-5.6-terra-low-partial.jsonl) | 127 |
| [20260928-gpt-6-astra-xhigh.jsonl](20260928-gpt-6-astra-xhigh.jsonl) | 614 |
| [20260928-gpt-6-luna-xhigh.jsonl](20260928-gpt-6-luna-xhigh.jsonl) | 614 |
| [20260928-gpt-6-sol-xhigh.jsonl](20260928-gpt-6-sol-xhigh.jsonl) | 614 |
| [20261008-gpt-6.1-sol-low.jsonl](20261008-gpt-6.1-sol-low.jsonl) | 614 |
| [20261008-gpt-6.1-sol-xhigh.jsonl](20261008-gpt-6.1-sol-xhigh.jsonl) | 614 |
| [56sol-low-614.jsonl](56sol-low-614.jsonl) | 614 |
| [luna-low-614.jsonl](luna-low-614.jsonl) | 614 |
| [paused-xhigh-614.jsonl](paused-xhigh-614.jsonl) | 300 |
| [sol55astra-low-614.jsonl](sol55astra-low-614.jsonl) | 1,842 |
| [starter-10.jsonl](starter-10.jsonl) | 380 |

从仓库根目录运行 `python verify_all_models.py` 核验七模型总榜，运行 `python verify_gpt61.py` 核验 GPT-6.1 Sol 答卷，运行 `python verify_results.py` 核验原有历史轮次。均不调用模型。
