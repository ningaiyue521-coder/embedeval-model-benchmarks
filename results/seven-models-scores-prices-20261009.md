# EmbedEval 614 题：七模型成绩与价格对比

整理日期：2026-10-09（北京时间）。成绩取自同一冻结题库、固定 L0 静态检查与 L3 规则检查。每题只计首次答案，通过得 10 分，否则 0 分；表中成绩为通过题数除以 614 后折算的百分制分数。Low 和 Xhigh 来自[七模型存档](seven-models-low-xhigh-20261008.md)；Max 已跑满 GPT-6 Sol、GPT-6.1 Sol 与 GPT-6 Luna，分别见[Sol 完整性核验](max-614-20261009.json)和[Luna 完整性核验](max-614-20261009.json)。

**价格口径：**OpenAI 官方标准 API 的短上下文文本价格，美元 / 100 万 token，依次为「输入 / 缓存输入 / 输出」。这不是本次使用 ChatGPT 登录运行 Codex CLI 的实际账单。价格以 2026-10-09 查到的官方模型页为准；Batch、Flex、Fast、Ultrafast、长上下文、地区处理及工具调用可能另有价格。

全部已跑满档位的单题耗时、P90 和测速网站 token/s 见[速度明细](seven-models-speed-20261009.md)。

| 模型 | Low 通过数·分数 | Xhigh 通过数·分数 | Max 通过数·分数 | API 价格：输入 / 缓存 / 输出 |
| --- | ---: | ---: | ---: | ---: |
| [GPT-6 Astra](https://developers.openai.com/api/docs/models/gpt-6-astra) | 559 · 91.04 | **564 · 91.86** | 未测 | **$10 / $1 / $50** |
| [GPT-6.1 Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol) | 557 · 90.72 | 561 · 91.37 | **564 · 91.86** | **$2 / $0.10 / $10** |
| [GPT-6 Sol](https://developers.openai.com/api/docs/models/gpt-6-sol) | 533 · 86.81 | 542 · 88.27 | **551 · 89.74** | **$2 / $0.20 / $10** |
| [GPT-5.5](https://developers.openai.com/api/docs/models/gpt-5.5) | 521 · 84.85 | 541 · 88.11 | 未测 | **$5 / $0.50 / $30** |
| [GPT-5.6 Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol) | 515 · 83.88 | 533 · 86.81 | 未测 | **$4 / $0.40 / $20** |
| [GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna) | 493 · 80.29 | 498 · 81.11 | **502 · 81.76** | **$0.10 / $0.01 / $0.50** |
| [GPT-5.6 Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna) | 480 · 78.18 | 486 · 79.15 | 未测 | **$0.20 / $0.02 / $1.20** |

## 读表结论

- **最高实测分数并列：**GPT-6 Astra Xhigh 与 GPT-6.1 Sol Max 均为 564/614、91.86。它们不是同一推理档位，也不是同一天测试；并列仅指本题库规则分。
- **两款 Sol 的 Max 均比本模型 Xhigh 提高：**GPT-6 Sol +9 题、+1.47 分；GPT-6.1 Sol +3 题、+0.49 分。
- **Luna Max 首答实测：**比 Luna Xhigh 多通过 4 题、+0.65 分；单题完成耗时中位数 58.90 秒，高于 Luna Xhigh 的 43.11 秒。详情见[Luna Max 报告](gpt-6-luna-max-614-20261009.md)。
- **价格与表现：**GPT-6.1 Sol 的官方标准 API 非缓存输入与输出单价均为 Astra 的五分之一；在这份题库上，其 Max 达到与 Astra Xhigh 相同的规则分。GPT-6.1 Sol 与 GPT-6 Sol 的非缓存输入和输出单价相同，缓存输入单价更低；本次 Max 多通过 13 题、领先 2.12 分。
- **低价档：**GPT-6 Luna 的官方标准 API 单价低于 GPT-5.6 Luna，在本题库的 Low 与 Xhigh 成绩也较高。

本题库来自 219 个基础案例的 614 个 Bugfix 变体，不等于 614 个独立工程任务。评分器只执行 L0 静态检查和 L3 启发式规则；没有编译、仿真、实机验证，不代表真实修复率，也不是 EmbedEval 官方榜单。不同日期、并发和推理档位的成绩适合做此题库内的参考比较，不宜推断稳定的总体能力差距。GPT-5.6 Terra 只有 127 题的局部首答，因此不进入全量排名。
