# 首次答案

21 份 JSONL 合计 **11,895 条记录**。其中七模型完整 Low / 极高总榜采用 8,596 份首答，后续三组 Max 采用 1,842 份首答。新增 Grok 停止轮次包含 611 份首答和 3 条无最终答案的异常记录；其前 6 份答卷与历史样本重复，不作为新增模型答案计数。其他历史试跑、小样本或暂停记录不计入全量排名。

`firstAnswer` 为首次最终答案，`checks` 为原始逐项规则结果。Grok 的 3 条异常记录中 `firstAnswer`、`answerHash` 和 `passed` 均为 `null`，不会冒充已评分失败答卷。

汇总计分时，这 3 次无有效最终答案的尝试计 0 分，分母仍为 614；Grok 4.7 High 的 **87.95 分**纳入首页主表。原始状态为 null 表示没有答卷和检查结果，不能据此从计分分母中移除。

| 文件 | 记录数 |
|---|---:|
| [20261014-grok-4.7-high-stopped.jsonl](20261014-grok-4.7-high-stopped.jsonl) | 614（611 首答 + 3 异常） |
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

从仓库根目录运行 `python verify_all_models.py` 核验七模型总榜，运行 `python verify_gpt61.py` 核验 GPT-6.1 Sol 答卷，运行 `python verify_results.py` 核验原有历史轮次，运行 `python verify_additional_results.py` 核验后续 Max 与 Cursor 样本，运行 `python verify_grok_stopped.py` 核验本轮 Grok 记录。均不调用模型。
