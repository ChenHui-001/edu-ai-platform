# audit-reports/archive —— 已被取代的评估报告

这里存放**已被新结论取代**的阶段性评估报告。它们不再作为决策依据，
只用于追溯"当时为什么这么改"。

## 规则

1. **唯一入口是 [`../BACKLOG.md`](../BACKLOG.md)。** 新发现先加行，不要新开报告。
2. 评估报告只在两种情况下新建：一次性全量评估（如 `structured-assessment-*`）、
   或某个专题的取证记录（如 `paper-analysis-*`）。
3. 报告被下一份同类报告取代时，把旧的移到本目录，并在 BACKLOG 里更新引用。

## 清单

| 文件 | 日期 | 被谁取代 |
|---|---|---|
| `perf-audit-2026-11-02.md` | 2026-11-02 | `structured-assessment-2.5.19-2026-11-10.md`（§6.2 性能） |
| `chain-audit-2026-11-03.md` | 2026-11-03 | 同上 |
| `questionbank-ui-audit-2026-11-03.md` | 2026-11-03 | 同上（§6.5 UI） |
| `followup-7-items-2026-11-03.md` | 2026-11-03 | `BACKLOG.md`（7 项已全部进 backlog） |
| `full-project-audit-2026-11-05.md` | 2026-11-05 | `structured-assessment-2.5.19-2026-11-10.md` |
| `reaudit-2026-11-06.md` | 2026-11-06 | 同上 |
| `reaudit3-2026-11-09.md` | 2026-11-09 | 同上 |

仍在 `audit-reports/` 根下的两份是**当前**评估依据：

- `paper-analysis-2026-11-10.md` —— 试卷域 P0/P1/P2 的来源
- `structured-assessment-2.5.19-2026-11-10.md` —— §6.1~§6.5 建议清单的来源
