# GPT-6.2 Sol 与 Astra 嵌入式跑分

2026-11-18 开始实测，末题完成于 2026-11-18。沿用同一套 614 道冻结 Bugfix 题。每题独立临时会话，只计首答。两款模型的 Low、XHigh 沿用同日已完成的首答，Sol 的 High、Max 为本次补测。

| 模型 | 档位 | 通过 / 614 | 规则分 | 对照型号同档分 | 变化（百分点） | 首答 |
|:---|:---|---:|---:|---:|---:|:---|
| GPT-6.2 Sol | Low | 530 | 86.32 | GPT-6.1 Sol 90.72 | -4.40 | [614 份](../answers/20261118-gpt-6.2-sol-low.jsonl) |
| GPT-6.2 Sol | High | 555 | 90.39 | GPT-6.1 Sol 91.04 | -0.65 | [614 份](../answers/20261118-gpt-6.2-sol-high.jsonl) |
| GPT-6.2 Sol | XHigh | 558 | 90.88 | GPT-6.1 Sol 91.37 | -0.49 | [614 份](../answers/20261118-gpt-6.2-sol-xhigh.jsonl) |
| GPT-6.2 Sol | Max | 565 | 92.02 | GPT-6.1 Sol 91.86 | +0.16 | [614 份](../answers/20261118-gpt-6.2-sol-max.jsonl) |
| GPT-6.2 Astra | Low | 554 | 90.23 | GPT-6 Astra 91.04 | -0.81 | [614 份](../answers/20261118-gpt-6.2-astra-low.jsonl) |
| GPT-6.2 Astra | XHigh | 568 | 92.51 | GPT-6 Astra 91.86 | +0.65 | [614 份](../answers/20261118-gpt-6.2-astra-xhigh.jsonl) |

## 主榜名次

- GPT-6.2 Astra 以 XHigh 的 **92.51** 分排第 1。
- GPT-6.2 Sol 以 Max 的 **92.02** 分排第 2。

## 核验

逐题核验了 3,684 份原始答卷和独立会话。有评分结果的答卷全部通过冻结 L0/L3 复评分核验。测试涵盖静态检查和启发式规则，未做编译、仿真或实机验证。

有 1 次调用发生传输失败或停滞且未生成首答，确认后补发。本地保留原始传输记录。

[机器可读成绩](gpt-6.2-sol-astra-20261118.json) · [模型成绩总表](../README.md#模型成绩总表)

运行 `python verify_gpt62_results.py` 核验公开数据。配置冻结检查器后可加 `--regrade` 复评分。
