# 大模型嵌入式代码修复实测

基于 [EmbedEval](https://github.com/Ecro/embedeval) 的固定版本 Bugfix 题库，对 614 道公开变体进行逐题新会话测试。每题只采纳模型首次完整答案；通过固定 L0 静态检查和 L3 规则检查计 10 分，否则 0 分，最终折算为百分制。**没有编译、仿真或实机验证，规则分不能等同真实修复率。** 这不是 EmbedEval 官方榜单。[判题器局限](docs/grader-limitations.md)

## 七模型 Low 与极高档：各 614 题

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

[七模型完整对比](results/seven-models-low-xhigh-20261008.md) · [合并数据与答卷来源](results/seven-models-low-xhigh-20261008.json) · [GPT-6.1 Sol 详细成绩](results/gpt-6.1-sol-low-xhigh-20261008.md)。运行 `python verify_all_models.py` 可从原始答卷检查 14 组成绩与总榜，**不调用模型**。不同批次并发与环境有差异，耗时不宜直接解释为模型本身速度差。

**首次答案存档：**原有五个 Low 组合共 3,070 份；[七个后续组合](results/six-models-answer-audit-20260928.json)共 4,298 份；GPT-6.1 Sol 新增 1,228 份。此前暂停的 Sol/Astra 极高 300 份保留作历史审计，已被完整轮次覆盖，**不重复计入 8,596**。

GPT-5.6 Terra Low 曾按用户要求停止，只留下 [127 份首次答案](results/partial-terra-low-20260928.json)，没有全量成绩，不进入七模型排行。

另有独立的 [10 题试跑矩阵](results/starter-10.json)：38 个模型与档位组合、380 份首次答案。这一小样本不与 614 题结果混排。早期 SVG 动画与嵌入式问答综合题库未计入本仓库成绩。

## 在另一台电脑继续跑新测试

需要 Python 3.12+、已登录的 Codex CLI，以及固定版本的上游检查器。下载仓库后，在仓库目录执行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python setup_upstream.py
python verify_results.py
python verify_six_models.py
python verify_gpt61.py
python verify_all_models.py
python batch_runner.py doctor
python batch_runner.py prepare --run my-new-round --models gpt-6-luna --efforts low
python batch_runner.py run --run my-new-round --workers 4
python batch_runner.py status --run my-new-round
```

macOS/Linux 用 `source .venv/bin/activate` 激活环境。`prepare` 只建一个全新的本地轮次，不导入历史答案，也不调用模型；`run` 才会消耗 Codex 账户额度。每题启动独立临时会话，第一次尝试即锁定，错误须检查，不能重答刷分。结果写入被 Git 忽略的 `.runs/`。调用前先确认该账户支持指定模型与推理档位。详细说明见 [复现与运行方法](docs/reproduce.md)；也可以用 [网页评分器](server.py) 手动录入其他模型的首次答案。

## 核验与边界

`verify_results.py` 检查原有存档；`verify_six_models.py` 检查新增 4,298 份答案的文件哈希、题目顺序、答案哈希和分数。`verify_gpt61.py` 检查本次 1,228 份首答；`verify_all_models.py` 从 8,596 份完整轮次首答核验七模型总榜。四个命令均不调用模型。安装上游依赖后可用 `python verify_results.py --regrade` 对旧存档复评分。题库与规则固定为上游提交 [`fdbcb9b93476149cce2d395532bf5164811fe053`](https://github.com/Ecro/embedeval/tree/fdbcb9b93476149cce2d395532bf5164811fe053)，对应 219 个基础案例生成的 614 个 Bugfix 变体。参见 [方法](docs/methodology.md)、[题库](data/catalog.json)、[原有轮次协议](data/protocols.json)。

本仓库沿用 Apache-2.0，见 [LICENSE](LICENSE) 与 [NOTICE](NOTICE)。
