# 冻结题库与协议

- `catalog.json`：614 道 Bugfix 题面，包含原有 Bug Hint、题目 ID、提示哈希与检查器哈希。
- `protocols.json`：五个轮次的题目顺序、模型档位及原始候选模型指令。

只把所选题面的 `prompt` 字段交给参测模型；答案目录和评分检查不应提供给参测模型。完整评测方法见 `../docs/methodology.md`。
