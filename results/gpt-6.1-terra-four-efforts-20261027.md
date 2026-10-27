# GPT-6.1 Terra 四档：614 题首次答案实测

测试日期：2026-10-27。沿用冻结题库、每题独立会话及 L0/L3 规则，未编译、仿真或实机验证。

| 档位 | 通过 / 614 | 规则分 / 100 | 含 CLI 传输重连记录的题次 | 首次答案 |
|---|---:|---:|---:|---|
| low | 522 | 85.02 | 301 | [答卷](../answers/20261027-gpt-6.1-terra-low.jsonl) |
| high | 527 | 85.83 | 298 | [答卷](../answers/20261027-gpt-6.1-terra-high.jsonl) |
| xhigh | 534 | 86.97 | 295 | [答卷](../answers/20261027-gpt-6.1-terra-xhigh.jsonl) |
| max | 543 | 88.44 | 299 | [答卷](../answers/20261027-gpt-6.1-terra-max.jsonl) |

每题只记录一次独立会话的首次最终答案，未按评分反馈重答。CLI 存在传输错误及内部重连，严格每题一次网络请求无法核实；详见机器可读记录中的 transportRetryWarning。

[机器可读汇总](gpt-6.1-terra-four-efforts-20261027.json)；运行 `python verify_terra_results.py` 核验答卷，配置固定上游规则后加 `--regrade` 离线复评。
