# 七模型嵌入式代码修复对比 · 2026-10-08

沿用同一固定题库、逐题新会话与首次完整答案规则，按两档均分排序。均分从两档的原始通过题数计算后统一四舍五入，避免先舍入单档成绩带来的误差。

| 排名 | 模型 | Low 通过 / 614 | Low 分 | 极高通过 / 614 | 极高分 | 两档均分 |
|---:|---|---:|---:|---:|---:|---:|
| 1 | GPT-6 Astra | 559 | 91.04 | 564 | 91.86 | 91.45 |
| 2 | **GPT-6.1 Sol** | 557 | 90.72 | 561 | 91.37 | 91.04 |
| 3 | GPT-6 Sol | 533 | 86.81 | 542 | 88.27 | 87.54 |
| 4 | GPT-5.5 | 521 | 84.85 | 541 | 88.11 | 86.48 |
| 5 | GPT-5.6 Sol | 515 | 83.88 | 533 | 86.81 | 85.34 |
| 6 | GPT-6 Luna | 493 | 80.29 | 498 | 81.11 | 80.70 |
| 7 | GPT-5.6 Luna | 480 | 78.18 | 486 | 79.15 | 78.66 |

14 个模型与档位组合，共 **8,596 份完整轮次的首次答案**。GPT-6.1 Sol 为 2026-10-08 新增的 1,228 份答卷；此前六模型成绩来自 2026-09-24 / 2026-09-28 批次。本次合并只读取既有首答，不重新调用模型。GPT-6 Luna 极高保留 1 份首次输出格式异常，按 0 分计。

[合并数据与答卷来源](seven-models-low-xhigh-20261008.json) · [GPT-6.1 Sol 详细成绩](gpt-6.1-sol-low-xhigh-20261008.md)。运行 `python verify_all_models.py` 可从原始答卷检查 14 组成绩与总榜，**不调用模型**。不同批次并发与环境有差异，耗时不宜直接解释为模型本身速度差。

## GPT-6.1 Sol 相比上一代与 Astra

| 对比 | Low 通过题数差 | Low 分数差 | 极高通过题数差 | 极高分数差 | 两档均分差 |
|---|---:|---:|---:|---:|---:|
| 6.1 Sol − GPT-6 Sol | +24 | +3.91 | +19 | +3.10 | +3.50 |
| 6.1 Sol − GPT-6 Astra | -2 | -0.32 | -3 | -0.49 | -0.41 |

单档分数差按表中已显示的两位小数成绩相减。

## 答卷与核验

| 模型 | Low 答卷 | 极高答卷 |
|---|---|---|
| GPT-6 Astra | [614 份首答](../answers/sol55astra-low-614.jsonl) | [614 份首答](../answers/20260928-gpt-6-astra-xhigh.jsonl) |
| GPT-6.1 Sol | [614 份首答](../answers/20261008-gpt-6.1-sol-low.jsonl) | [614 份首答](../answers/20261008-gpt-6.1-sol-xhigh.jsonl) |
| GPT-6 Sol | [614 份首答](../answers/sol55astra-low-614.jsonl) | [614 份首答](../answers/20260928-gpt-6-sol-xhigh.jsonl) |
| GPT-5.5 | [614 份首答](../answers/sol55astra-low-614.jsonl) | [614 份首答](../answers/20260928-gpt-5.5-xhigh.jsonl) |
| GPT-5.6 Sol | [614 份首答](../answers/56sol-low-614.jsonl) | [614 份首答](../answers/20260928-gpt-5.6-sol-xhigh.jsonl) |
| GPT-6 Luna | [614 份首答](../answers/luna-low-614.jsonl) | [614 份首答](../answers/20260928-gpt-6-luna-xhigh.jsonl) |
| GPT-5.6 Luna | [614 份首答](../answers/20260928-gpt-5.6-luna-low.jsonl) | [614 份首答](../answers/20260928-gpt-5.6-luna-xhigh.jsonl) |

仅汇总 14 个已完成的 614 题组合。此前的 10 题试跑、暂停的 Sol/Astra 极高局部轮次、Terra Low 局部轮次均不进入此榜。

```bash
python verify_all_models.py
python verify_gpt61.py
```

两个命令均只核验已有存档。`verify_all_models.py` 检查答案文件和题面哈希、固定规则版本、逐题顺序、首次尝试标记、L0/L3 判分、完整性、汇总分数和均分排序。

## 测试范围

固定上游提交 `fdbcb9b93476149cce2d395532bf5164811fe053`，219 个基础案例生成 614 个 Bugfix 变体；其中 embedded-linux 569 题、Zephyr 43 题、ESP-IDF 2 题。分数仅代表 L0 静态检查和 L3 启发式规则检查通过率，未编译、未仿真、未实机验证。[判题器局限](../docs/grader-limitations.md)

历史批次与 6.1 批次日期、并发和 CLI 环境有差异。表中可比较同题库规则分，不用跨批次墙钟耗时推断模型速度。详细来源保留在[合并 JSON](seven-models-low-xhigh-20261008.json)与各轮原始结果中。
