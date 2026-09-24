# 本地核验与评分

## 1. 仅核验已发布记录

Python 3.12+，不需要模型、密钥、上游代码或第三方依赖：

```bash
python verify_results.py
```

核验 614 个提示哈希、3,750 份答案哈希、唯一键、原始逐项通过结果、token 汇总、完整 Low 成绩、首轮矩阵、暂停状态和导出文件哈希。脚本不修改答案、分数或数据库。

## 2. 安装上游检查器，离线复评分

建议在虚拟环境运行。Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python setup_upstream.py
python verify_results.py --regrade
python -m unittest test_bench
```

macOS / Linux 的虚拟环境激活命令为 `source .venv/bin/activate`，其余命令相同。安装脚本从固定提交下载上游归档，只安装 `src/`、`cases/` 与 `LICENSE` 到 `.upstream/embedeval`，保留冻结评分所需的 CRLF 字节格式，随后逐案例校验规则哈希。评分时不联网、不执行提交的 C 代码。

如已保存固定版本归档，可使用 `python setup_upstream.py --archive /path/to/archive.tar.gz`。它也接受 `git archive` 生成的 TAR。安装目标必须为空，脚本不会覆盖现有上游目录。

已有**字节哈希匹配**的上游副本可以通过环境变量 `EMBEDEVAL_ROOT` 指定。未匹配的规则会使评分停止；不要重新生成题库或修改哈希来绕过检查。

`--regrade` 将已保存答案再次送入相同的本地检查函数，与全部逐项结果对照。这只是复核原答卷，不会调用模型，也不会替换历史分数。

## 3. 用网页保存新模型的首次答案

```bash
python server.py --port 8767
```

打开 <http://127.0.0.1:8767/>，填写“模型 + 档位 + 新轮次标识”，选择题目，复制题面到模型的**新会话**；只保存首次完整答案，粘贴或导入评分页。评分器不需要接入大模型 API。

每个模型标识、每题的第一次有效提交会写入本地 `answers.sqlite3` 并锁定；不同内容的覆盖请求会被拒绝，完全相同的重复提交返回旧记录。若首次输出格式不符合要求，保留原文，只能从原文提取完整源码；不要要求模型重新回答。

新轮次可使用独立数据库，例如 `python server.py --port 8767 --db my-new-round.sqlite3`。这是主动启动新的实验，不能用来为已经发布的一轮刷高分。网页只显示当前本地数据库，历史成绩通过 README 与 `results/` 查看。

## 4. 复现边界

评分器和数据核验可离线复现。历史模型响应、服务端快照、传输恢复、缓存和账户百分比不能离线重建。此发布包没有自动批量调用模型的入口；原批次运行方式记录在方法文档及协议中。下载或核验仓库不会恢复已暂停的 Xhigh 测试。
