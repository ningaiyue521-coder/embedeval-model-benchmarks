# 2026-11-06：补齐九个嵌入式跑分档位

同一冻结的 614 道题，每题独立临时会话，只计首次最终答案，不提供工具、参考答案或评分反馈。新增 9 组，共 5,526 份首答；核对原始事件、模型档位、独立会话、数据库和哈希，并逐题按冻结 L0/L3 规则复评分一致。

| 模型 | 档位 | 通过 / 614 | 分数 | 单题中位数（秒） | 首答 |
|---|---|---:|---:|---:|---|
| GPT-5.6 Luna | high | 474 | 77.20 | 29.94 | [614 份](../answers/20261106-gpt-5.6-luna-high.jsonl) |
| GPT-5.6 Sol | high | 523 | 85.18 | 27.44 | [614 份](../answers/20261106-gpt-5.6-sol-high.jsonl) |
| GPT-6 Luna | high | 503 | 81.92 | 54.57 | [614 份](../answers/20261106-gpt-6-luna-high.jsonl) |
| GPT-5.6 Luna | max | 484 | 78.83 | 36.53 | [614 份](../answers/20261106-gpt-5.6-luna-max.jsonl) |
| GPT-5.6 Sol | max | 538 | 87.62 | 29.78 | [614 份](../answers/20261106-gpt-5.6-sol-max.jsonl) |
| GPT-6 Astra | high | 560 | 91.21 | 37.50 | [614 份](../answers/20261106-gpt-6-astra-high.jsonl) |
| GPT-6 Sol | high | 545 | 88.76 | 36.66 | [614 份](../answers/20261106-gpt-6-sol-high.jsonl) |
| GPT-6.1 Sol | high | 559 | 91.04 | 37.90 | [614 份](../answers/20261106-gpt-6.1-sol-high.jsonl) |
| GPT-6 Astra | max | 564 | 91.86 | 43.99 | [614 份](../answers/20261106-gpt-6-astra-max.jsonl) |

限流等传输失败未产出答案时允许补发；已有首答不替换，不根据分数重答。总并发 64，无单款并发限制。单题耗时包含 CLI 启动、等待、传输和评分，不是纯模型生成速度。

**只运行 L0 静态检查和 L3 启发式规则，未编译、仿真或实机验证。规则分不等于真实工程修复率。**

[完整汇总 JSON](missing-nine-tiers-20261106.json) · [全部模型总表](all-models-summary-20261106.json)。运行 `python verify_missing_results.py` 核对公开首答与分数；安装冻结检查器后可加 `--regrade`，均不调用模型。
