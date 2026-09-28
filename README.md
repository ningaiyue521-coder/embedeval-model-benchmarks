# 大模型嵌入式代码修复实测

基于 [EmbedEval](https://github.com/Ecro/embedeval) 的固定版本 Bugfix 题库，对 614 道公开变体进行逐题新会话测试。每题只采纳模型首次完整答案；通过固定 L0 静态检查和 L3 规则检查计 10 分，否则 0 分，最终折算为百分制。**没有编译、仿真或实机验证，规则分不能等同真实修复率。** 这不是 EmbedEval 官方榜单。[判题器局限](docs/grader-limitations.md)

## 六模型 Low 与极高档：各 614 题

| 模型 | Low 通过 / 614 | Low 分 | 极高通过 / 614 | 极高分 |
|---|---:|---:|---:|---:|
| GPT-6 Astra | 559 | 91.04 | 564 | 91.86 |
| GPT-6 Sol | 533 | 86.81 | 542 | 88.27 |
| GPT-5.5 | 521 | 84.85 | 541 | 88.11 |
| GPT-5.6 Sol | 515 | 83.88 | 533 | 86.81 |
| GPT-6 Luna | 493 | 80.29 | 498 | 81.11 |
| GPT-5.6 Luna | 480 | 78.18 | 486 | 79.15 |

12 个模型与档位组合，共 **7,368 份完整轮次的首次答案**。GPT-6 Luna 极高有 1 份首次输出格式异常，保留原文并按 0 分计；没有向模型追问。完整的逐题变化、响应时间、token、分组统计、口径见 [对比文档](results/six-models-low-xhigh-20260928.md) 和 [机器可读结果](results/six-models-low-xhigh-20260928.json)。六模型数据包含 2026-09-24 与 2026-09-28 的运行批次；不同批次并发与环境有差异，响应时间不宜直接解释为模型本身速度差。

**首次答案存档：**原有 [五个 Low 组合](answers/) 共 3,070 份；新增 [七个组合](results/six-models-answer-audit-20260928.json) 共 4,298 份，每组一个 JSONL，保存原始最终答案、逐项判分、哈希与用量，不含账号快照、会话 ID、认证信息或原始传输日志。此前已暂停的 Sol/Astra 极高 300 份也保留作历史审计，已被完整轮次覆盖，**不重复计入 7,368**。

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
python batch_runner.py doctor
python batch_runner.py prepare --run my-new-round --models gpt-6-luna --efforts low
python batch_runner.py run --run my-new-round --workers 4
python batch_runner.py status --run my-new-round
```

macOS/Linux 用 `source .venv/bin/activate` 激活环境。`prepare` 只建一个全新的本地轮次，不导入历史答案，也不调用模型；`run` 才会消耗 Codex 账户额度。每题启动独立临时会话，第一次尝试即锁定，错误须检查，不能重答刷分。结果写入被 Git 忽略的 `.runs/`。调用前先确认该账户支持指定模型与推理档位。详细说明见 [复现与运行方法](docs/reproduce.md)；也可以用 [网页评分器](server.py) 手动录入其他模型的首次答案。

## 核验与边界

`verify_results.py` 检查原有存档；`verify_six_models.py` 检查新增 4,298 份答案的文件哈希、题目顺序、答案哈希和分数。这两个命令均不调用模型。安装上游依赖后可用 `python verify_results.py --regrade` 对旧存档复评分。题库与规则固定为上游提交 [`fdbcb9b93476149cce2d395532bf5164811fe053`](https://github.com/Ecro/embedeval/tree/fdbcb9b93476149cce2d395532bf5164811fe053)，对应 219 个基础案例生成的 614 个 Bugfix 变体。参见 [方法](docs/methodology.md)、[题库](data/catalog.json)、[原有轮次协议](data/protocols.json)。

本仓库沿用 Apache-2.0，见 [LICENSE](LICENSE) 与 [NOTICE](NOTICE)。
