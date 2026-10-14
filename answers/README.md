# 首次答案

20 份 JSONL 合计 **11,281 条记录**。其中七模型完整 Low / 极高总榜采用 8,596 份首答，后续三组 Max 采用 1,842 份首答；其他历史试跑、小样本或暂停记录不计入全量排名。`firstAnswer` 为首次最终答案，`checks` 为原始逐项规则结果。

| 文件 | 记录数 |
|---|---:|
| [20261009-gpt-6.1-sol-max.jsonl](20261009-gpt-6.1-sol-max.jsonl) | 614 |
| [20261009-gpt-6-sol-max.jsonl](20261009-gpt-6-sol-max.jsonl) | 614 |
| [20261009-gpt-6-luna-max.jsonl](20261009-gpt-6-luna-max.jsonl) | 614 |
| [20260928-claude-opus-5-5-high-sample.jsonl](20260928-claude-opus-5-5-high-sample.jsonl) | 30 |
| [20260928-grok-4.7-high-sample.jsonl](20260928-grok-4.7-high-sample.jsonl) | 6 |
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

从仓库根目录运行 `python verify_all_models.py` 核验七模型总榜，运行 `python verify_gpt61.py` 核验 GPT-6.1 Sol 答卷，运行 `python verify_results.py` 核验原有历史轮次，运行 `python verify_additional_results.py` 核验后续 Max 与 Cursor 样本。均不调用模型。
