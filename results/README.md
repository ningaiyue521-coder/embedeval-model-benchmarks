# 成绩与报告索引

| 状态 | 报告 | 机器可读数据 |
|---|---|---|
| 主表：8 模型、18 组档位 | [返回首页](../README.md) | [统一分母 614 的汇总](all-models-summary-20261014.json) |
| 完整：14 组 × 614 题 | [七模型 Low/Xhigh](seven-models-low-xhigh-20261008.md) | [JSON](seven-models-low-xhigh-20261008.json) |
| 完整：3 组 × 614 题 | [三模型 Max](max-614-20261009.md) | [JSON](max-614-20261009.json) |
| 主表计分：614 次尝试 | [Grok 4.7 High · 2026-10-14](grok-4.7-high-stopped-20261014.md) | [JSON](grok-4.7-high-stopped-20261014.json) |
| 小样本与历史暂停 | [Cursor 试跑](cursor-samples-20260928.md) | [JSON](cursor-samples-20260928.json) |

Grok 采用统一分母 614，3 次无有效最终答案计 0 分，成绩 **87.95**，纳入主表与图表。88.38 仅保留为已答题审计比例，不作为排名成绩。早期 Grok 6 题记录作为历史快照保留。

## 历史文件与辅助对比

- [max-614-20261009.json](max-614-20261009.json)：三组完整 Max 的 1,842 份首答、成绩与存档哈希。[报告](max-614-20261009.md)
- [cursor-samples-20260928.json](cursor-samples-20260928.json)：Opus 30 题、Grok 暂停 6 题，以及无答案启动失败记录。[报告](cursor-samples-20260928.md)
- [seven-models-low-xhigh-20261008.json](seven-models-low-xhigh-20261008.json)：七模型 Low/Xhigh 全量对比。
- [seven-models-scores-prices-20261009.md](seven-models-scores-prices-20261009.md)：成绩与 2026-10-09 历史价格。
- [seven-models-speed-20261009.md](seven-models-speed-20261009.md)：本地耗时及注明日期的外部测速记录。
- `low-614.json`：五个模型完整 Low 结果。
- `starter-10.json`：首轮 10 题、38 个模型与档位组合。
- `paused-xhigh.json`：尚未完成的极高档，最终分为 null，不自动恢复。
- `timing-and-usage.json`：批次耗时与共享账户额度变化。
- `export-audit.json`：原始记录导出核验及 JSONL 文件 SHA-256。

规则分不包含编译、仿真或硬件验证。所有分数均可从 `../answers/` 的原始逐项结果重新汇总。
