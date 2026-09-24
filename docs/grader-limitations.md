# 判题器局限与首次答案中的例子

本轮固定使用上游提交 `fdbcb9b93476149cce2d395532bf5164811fe053` 的 L0/L3 检查。以下问题是在收到模型的首次答案后发现的。原始题面、答卷和规则分均保留；没有给模型反馈，也没有重答或中途修改判题规则。

## 第 3 题：题面缺少 50ms 要求

官方 Bugfix 题面删掉了启动消抖定时器的调用，原有题面和 Bug Hint 均未给出必须采用 50ms 的约束。

上游 `cases/zephyr/gpio-basic-006/checks/behavior.py:26` 直接检查源码是否包含 `K_MSEC(50)` 或字符串 `50`。因此使用 30ms 消抖、已经将 GPIO 操作从中断回调延后的答案，也会因 `debounce_50ms_window` 扣掉本题全部 10 分。

已观察到的例子：GPT-5.5 medium 使用 `k_timer_start(&debounce_tmr, K_MSEC(30), K_NO_WAIT)`，失败项只有这一条。这个检查不能证明其消抖修复错误；实际适用的消抖时长需要按硬件验证。

## 第 10 题：统一 cleanup 路径未被识别

上游 `cases/zephyr/security-001/checks/behavior.py:117` 提取 `if (status != PSA_SUCCESS)` 代码块，然后要求其中直接出现 `psa_destroy_key` 字样。

GPT-5.5 medium 在加密/解密失败时执行 `goto cleanup`，在同一个 `cleanup:` 中调用 `psa_destroy_key(key_id)`，最后返回错误状态。规则没有沿跳转检查控制流，仍将 `error_path_key_destroyed` 判为失败。

这条失败记录是判题器未识别该清理结构的证据，不是“错误路径未释放密钥”的可靠证据。

## 第 1 题：原子 API 的内存屏障语义未被识别

上游 `cases/zephyr/isr-concurrency-008/checks/behavior.py:98` 只搜索 `compiler_barrier`、`__dmb` 等额外屏障写法。后面的屏障顺序检查也要求出现这些文本模式。

[Zephyr 官方 Atomic Services 文档](https://docs.zephyrproject.org/latest/kernel/services/other/atomic.html#memory-ordering)说明原子 API 应提供所需的完整内存屏障。已使用 `atomic_get` / `atomic_set` 的答案，删除额外的 `compiler_barrier()`，仍可能被上述规则扣分。

这不自动证明整个队列实现正确；只能说明“缺少这些额外屏障文本”不足以单独判定内存顺序错误。

## 第 7 题：强制 volatile，未识别原子健康标志

上游 `cases/zephyr/watchdog-005/checks/static.py:35` 要求代码包含 `volatile` 和健康标志名称；否则 `health_flag_is_volatile` 失败，并跳过后续 L3 检查。

GPT-6 Luna max 使用 `static atomic_t worker_alive`，工作线程用 `atomic_set(&worker_alive, 1)` 报告存活，主线程用 `atomic_cas(&worker_alive, 1, 0)` 消费信号，仅成功时喂狗。这个实现没有出现 `volatile`，因此被扣除本题 10 分。

[Zephyr 原子 API 文档](https://docs.zephyrproject.org/latest/kernel/services/other/atomic.html#memory-ordering)说明其原子操作的内存屏障要求。缺少 `volatile` 字样本身不能证明上述原子共享标志有错；本例也不等同于已经验证整个看门狗实现正确。

## 如何解读成绩

- 成绩矩阵给出冻结规则的**原始规则分**，保证所有型号使用同一题面和同一判题器。
- 以上题号指首轮 10 题，每题 10 分。614 题测试使用相同的冻结规则体系，按通过比例折算为百分制；每题约占 0.163 分。
- 不以这些原始分直接宣称某个模型或更高推理档位的真实编码能力更差。
- 首次答案和逐项检查结果保存在 [answers/](../answers/) 的 JSONL 文件中。用 `round + model + effort + caseKey` 定位，字段为 `firstAnswer` 与 `checks`。
- 本文不提供编译、运行或硬件验证结论，也不修改本轮总分。
