# EmbedEval 614 题：已测模型单题耗时与网站输出速度

整理日期：2026-10-09。七个模型的 Low、Xhigh 和已跑满的三个 Max 都列在下表；每行 614 题。成绩只计首次答案。

**本地耗时**从单题调用开始，到首次答案保存并完成本地评分为止，包含 Codex CLI 启动、网络传输、首 token 等待、生成及本地评分，不含任务排队。P90 是按最邻近秩计算的第 90 百分位，约 90% 的题目不超过该时间。**本地全程 token/s** = 总输出 token（含推理 token）÷ 总单题耗时。**网站输出 token/s**取 [Artificial Analysis](https://artificialanalysis.ai/) 2026-10-09 对相同推理档位的 OpenAI API 测量；它统计首个流式片段到达后的生成速度，和本地全程速度不是同一指标。

| 模型 | 档位 | 本地分数 | 单题中位数 | 单题平均 | P90 | 平均输出 token/题 | 本地全程 token/s | 网站输出 token/s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| [GPT-6 Astra](https://artificialanalysis.ai/models/gpt-6-astra-low) | Low | 91.04 | 63.62 秒 | 64.05 秒 | 88.55 秒 | 412 | 6.43 | 42.0 |
| [GPT-6 Astra](https://artificialanalysis.ai/models/gpt-6-astra-xhigh) | Xhigh | 91.86 | 48.63 秒 | 50.52 秒 | 69.30 秒 | 575 | 11.39 | 43.0 |
| [GPT-6.1 Sol](https://artificialanalysis.ai/models/gpt-6-1-sol-low) | Low | 90.72 | 55.26 秒 | 54.64 秒 | 74.48 秒 | 416 | 7.62 | 47.1 |
| [GPT-6.1 Sol](https://artificialanalysis.ai/models/gpt-6-1-sol-xhigh) | Xhigh | 91.37 | 59.87 秒 | 59.96 秒 | 79.05 秒 | 615 | 10.26 | 53.2 |
| [GPT-6.1 Sol](https://artificialanalysis.ai/models/gpt-6-1-sol) | Max | 91.86 | 63.97 秒 | 66.33 秒 | 94.24 秒 | 729 | 11.00 | 55.5 |
| [GPT-6 Sol](https://artificialanalysis.ai/models/gpt-6-sol-low) | Low | 86.81 | 53.52 秒 | 54.38 秒 | 75.22 秒 | 428 | 7.87 | 90.4 |
| [GPT-6 Sol](https://artificialanalysis.ai/models/gpt-6-sol-xhigh) | Xhigh | 88.27 | 44.27 秒 | 46.31 秒 | 66.55 秒 | 623 | 13.45 | 85.3 |
| [GPT-6 Sol](https://artificialanalysis.ai/models/gpt-6-sol) | Max | 89.74 | 53.19 秒 | 55.74 秒 | 79.97 秒 | 725 | 13.00 | 86.4 |
| [GPT-5.5](https://artificialanalysis.ai/models/gpt-5-5-low) | Low | 84.85 | 53.17 秒 | 54.15 秒 | 74.52 秒 | 527 | 9.73 | 78.5 |
| [GPT-5.5](https://artificialanalysis.ai/models/gpt-5-5) | Xhigh | 88.11 | 47.40 秒 | 53.02 秒 | 77.72 秒 | 1402 | 26.44 | 87.6 |
| [GPT-5.6 Sol](https://artificialanalysis.ai/models/gpt-5-6-sol-low) | Low | 83.88 | 54.62 秒 | 55.18 秒 | 75.67 秒 | 454 | 8.22 | 69.3 |
| [GPT-5.6 Sol](https://artificialanalysis.ai/models/gpt-5-6-sol-xhigh) | Xhigh | 86.81 | 44.00 秒 | 43.33 秒 | 55.92 秒 | 557 | 12.84 | 72.8 |
| [GPT-6 Luna](https://artificialanalysis.ai/models/gpt-6-luna-low) | Low | 80.29 | 36.32 秒 | 39.10 秒 | 60.42 秒 | 381 | 9.75 | 124.7 |
| [GPT-6 Luna](https://artificialanalysis.ai/models/gpt-6-luna-xhigh) | Xhigh | 81.11 | 43.11 秒 | 44.92 秒 | 64.75 秒 | 867 | 19.30 | 116.4 |
| [GPT-6 Luna](https://artificialanalysis.ai/models/gpt-6-luna) | Max | 81.76 | 58.90 秒 | 57.80 秒 | 76.76 秒 | 983 | 17.01 | 126.5 |
| [GPT-5.6 Luna](https://artificialanalysis.ai/models/gpt-5-6-luna-low) | Low | 78.18 | 49.78 秒 | 50.90 秒 | 71.72 秒 | 506 | 9.95 | 111.8 |
| [GPT-5.6 Luna](https://artificialanalysis.ai/models/gpt-5-6-luna-xhigh) | Xhigh | 79.15 | 49.59 秒 | 52.49 秒 | 76.88 秒 | 894 | 17.02 | 109.6 |

## 对比结论

- 网站显示 GPT-6 Luna Max 的流式输出最快，为 126.5 token/s；本地整题中位数却是 58.90 秒，GPT-6 Sol Max 为 53.19 秒。Luna Max 平均每题输出约 983 token，Sol Max 约 725 token，生成量和等待时间都会影响整题耗时。
- Luna 的本地中位耗时从 Low 的 36.32 秒、Xhigh 的 43.11 秒升到 Max 的 58.90 秒；分数仅从 80.29 升至 81.76。就这套短代码修复题而言，Max 的额外耗时换来的加分较少。
- 个别档位的本地耗时顺序与推理档位直觉不同，例如 Astra Xhigh 快于 Astra Low。各轮测试的日期、并发和服务负载不同，不能把差异全归因于模型或档位。
- GPT-5.5、GPT-5.6 Sol 与 GPT-5.6 Luna 在 Artificial Analysis 上已标为旧模型；网站只继续更新其默认 10k 输入 token 工作负载的性能，其他负载的数据可能是历史值。

本地 Low/Xhigh 成绩及原始答案文件索引见[七模型存档](seven-models-low-xhigh-20261008.json)，Max 的逐题核验见[Luna](max-614-20261009.json)和[两款 Sol](max-614-20261009.json)。本题库仅执行固定 L0/L3 规则检查，未编译、仿真或实机验证。
