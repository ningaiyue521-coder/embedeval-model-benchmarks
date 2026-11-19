# GPT-6.2 Sol 与 Astra 嵌入式跑分

2026-11-18 开始实测，末题完成于 2026-11-19。沿用同一套 614 道冻结 Bugfix 题。每题独立临时会话，只计首答。两款模型均已完成 Low、High、XHigh 和 Max 四档。本次补齐 Astra 的 High 和 Max。

| 模型 | 档位 | 通过 / 614 | 规则分 | 对照型号同档分 | 变化（百分点） | 首答 |
|:---|:---|---:|---:|---:|---:|:---|
| GPT-6.2 Sol | Low | 530 | 86.32 | GPT-6.1 Sol 90.72 | -4.40 | [614 份](../answers/20261118-gpt-6.2-sol-low.jsonl) |
| GPT-6.2 Sol | High | 555 | 90.39 | GPT-6.1 Sol 91.04 | -0.65 | [614 份](../answers/20261118-gpt-6.2-sol-high.jsonl) |
| GPT-6.2 Sol | XHigh | 558 | 90.88 | GPT-6.1 Sol 91.37 | -0.49 | [614 份](../answers/20261118-gpt-6.2-sol-xhigh.jsonl) |
| GPT-6.2 Sol | Max | 565 | 92.02 | GPT-6.1 Sol 91.86 | +0.16 | [614 份](../answers/20261118-gpt-6.2-sol-max.jsonl) |
| GPT-6.2 Astra | Low | 554 | 90.23 | GPT-6 Astra 91.04 | -0.81 | [614 份](../answers/20261118-gpt-6.2-astra-low.jsonl) |
| GPT-6.2 Astra | High | 563 | 91.69 | GPT-6 Astra 91.21 | +0.48 | [614 份](../answers/20261118-gpt-6.2-astra-high.jsonl) |
| GPT-6.2 Astra | XHigh | 568 | 92.51 | GPT-6 Astra 91.86 | +0.65 | [614 份](../answers/20261118-gpt-6.2-astra-xhigh.jsonl) |
| GPT-6.2 Astra | Max | 573 | 93.32 | GPT-6 Astra 91.86 | +1.46 | [614 份](../answers/20261118-gpt-6.2-astra-max.jsonl) |

## 主榜名次

- GPT-6.2 Astra 的 Max 成绩为 **93.32** 分，排第 1。
- GPT-6.2 Sol 的 Max 成绩为 **92.02** 分，排第 2。

## 核验

逐题核验了 4,912 份首答及其独立会话。冻结 L0 静态检查和 L3 规则检查的复评分结果与初判一致。

有 84 次调用发生传输失败或停滞且未生成首答，确认后补发。本地保留原始传输记录。

[机器可读成绩](gpt-6.2-sol-astra-20261118.json) · [模型成绩总表](../README.md#模型成绩总表)

运行 `python verify_gpt62_results.py` 核验公开数据。配置冻结检查器后可加 `--regrade` 复评分。
