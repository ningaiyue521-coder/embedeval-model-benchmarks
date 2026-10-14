# EmbedEval · 嵌入式代码修复实测

**固定题库 · 每题独立会话 · 只计首次尝试 · 原始答卷可核验**

[成绩总表](#模型成绩总表) · [报告导航](#报告导航) · [评分口径](#评分口径) · [本地核验](#本地核验)

| 题库 | 已测模型 | 已测档位组合 | 计分题次 |
|:---:|:---:|:---:|:---:|
| **614 题** | **8 款** | **18 组** | **11,052** |

> 冻结 **L0 静态检查 + L3 规则检查**；未编译、仿真或实机验证。规则分不等于真实修复率，本项目不是 EmbedEval 官方榜单。

## 模型成绩总表

所有已测档位统一以 **614 题为分母**。表格显示「百分制规则分 / 通过题数」；`—` 表示未测。按各模型**最高已测档位**排序，高亮该档成绩；High、Xhigh、Max 分列，不视作相同推理设置。

| 模型 | Low | High | Xhigh（极高） | Max |
|:---|---:|---:|---:|---:|---:|
| GPT-6 Astra | 91.04 / 559 | — | **91.86 / 564** | — |
| GPT-6.1 Sol | 90.72 / 557 | — | 91.37 / 561 | **91.86 / 564** |
| GPT-6 Sol | 86.81 / 533 | — | 88.27 / 542 | **89.74 / 551** |
| GPT-5.5 | 84.85 / 521 | — | **88.11 / 541** | — |
| Grok 4.7 | — | **87.95 / 540** | — | — |
| GPT-5.6 Sol | 83.88 / 515 | — | **86.81 / 533** | — |
| GPT-6 Luna | 80.29 / 493 | — | 81.11 / 498 | **81.76 / 502** |
| GPT-5.6 Luna | 78.18 / 480 | — | **79.15 / 486** | — |

![各模型最高已测规则分，统一以 614 题为分母，档位分别标注](assets/best-complete-scores.svg)

**2026-10-14 更新：**Grok 4.7 High 纳入总表，540 题通过，**87.95 分**。611 题有首答，3 次尝试无有效最终答案计 0 分，未重答。旧的 88.38 分只反映已答题比例，不作为本榜成绩。[Grok 详细报告](results/grok-4.7-high-stopped-20261014.md)

[总表机器可读数据](results/all-models-summary-20261014.json) · [Low/Xhigh 对比](results/seven-models-low-xhigh-20261008.md) · [三组 Max](results/max-614-20261009.md) · [历史价格](results/seven-models-scores-prices-20261009.md) · [耗时对比](results/seven-models-speed-20261009.md)

## 报告导航

| 内容 | 报告 | 口径 |
|:---|:---|:---|
| 八模型成绩总表 | [汇总数据](results/all-models-summary-20261014.json) | 18 个档位组合，统一分母 614 |
| Grok 4.7 High | [614 题成绩](results/grok-4.7-high-stopped-20261014.md) | 540 题通过，3 次无有效答案计 0 |
| 七模型 Low / Xhigh | [详细对比](results/seven-models-low-xhigh-20261008.md) | 14 组 × 614 题 |
| 三模型 Max | [详细成绩](results/max-614-20261009.md) | 3 组 × 614 题 |
| Claude Opus High | [Cursor 小样本](results/cursor-samples-20260928.md) | 30 题通过 29 题，样本不进入主表 |
| GPT-5.6 Terra Low | [暂停记录](results/partial-terra-low-20260928.json) | 127 题局部样本，无全量成绩 |
| 早期试跑 | [10 题矩阵](results/starter-10.json) | 38 组、380 份首答 |
| 原始答卷 | [首答与逐项评分](answers/README.md) | JSONL、哈希、异常状态 |
| 实验说明 | [题库](data/README.md) · [方法](docs/methodology.md) · [判题器局限](docs/grader-limitations.md) | 固定题面与评分规则 |

## 评分口径

- 每题只计第一次锁定尝试，不追问、重答或用后续修订刷分。
- 有效首答通过全部冻结 L0/L3 检查得 10 分，否则 0 分；没有有效最终答案的尝试也计 0 分。
- 主表分数 = 通过题数 ÷ **614** × 100。没有答案的记录保留原始状态，不伪造评分检查结果。
- 图表取各模型最高已测档位，属于不同设置的成绩对比；并非相同算力档位下的模型排名。

Grok 的三条异常分别是配置文件改名失败、TLS 连接断开和长时间未返回后停止，原因在报告中保留。Low/Xhigh、Max 和 Grok 来自不同日期、平台及并发条件，耗时不能直接解释为模型本身速度差。价格及外部测速报告保留注明的 **2026-10-09 历史口径**。

原有暂停 Sol/Astra 的 300 份答卷、Grok 早期 6 题快照保留作审计，不重复计入主表题次。早期 SVG 动画与嵌入式问答综合题库不计入本仓库。

## 本地核验

Python 3.12+，不需要密钥，不调用模型，也不改答案或分数。

```bash
python verify_results.py
python verify_six_models.py
python verify_gpt61.py
python verify_all_models.py
python verify_additional_results.py
python verify_grok_stopped.py
python verify_combined_summary.py
```

<details>
<summary><strong>继续跑新测试：安装与使用</strong></summary>

需要已登录的 Codex CLI 和固定版本上游检查器。Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python setup_upstream.py
python batch_runner.py doctor
python batch_runner.py prepare --run my-new-round --models gpt-6-luna --efforts low
python batch_runner.py run --run my-new-round --workers 4
python batch_runner.py status --run my-new-round
```

macOS/Linux 用 `source .venv/bin/activate` 激活。`run` 会消耗账户额度；结果保存至忽略上传的 `.runs/`。详见 [复现与运行方法](docs/reproduce.md)；也可以用 [网页评分器](server.py) 录入首答。

</details>

---

基于 [EmbedEval](https://github.com/Ecro/embedeval) 提交 [`fdbcb9b`](https://github.com/Ecro/embedeval/tree/fdbcb9b93476149cce2d395532bf5164811fe053)：219 个基础案例生成 614 个变体，并非 614 个独立工程任务。

Apache-2.0 · [LICENSE](LICENSE) · [NOTICE](NOTICE) · **2026-10-14**
