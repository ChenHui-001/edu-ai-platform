"""AI 补题的单批题量上限（从 paper_compose 路由层抽出的独立策略）。

`paper_compose.py` 已承担补题/重生/预览/编辑/版本/共享/审核/导出 8 类职责，
是项目第一热点文件。把与 HTTP 路由无关的「推理预算 → 批量」策略挪到
services 层，是拆分这块胖路由的第一步；原模块保留 re-import，既有调用点
与验证脚本无需改动。
"""
from typing import Dict

# 统一 10 道对重题型必然撞墙：单题正文量越大的题型，单批越小。
# 作文一题上千字、解答题要完整解题过程、材料题自带长材料 + 多小问。
FILL_BATCH_BY_TYPE: Dict[str, int] = {
    "composition": 2,
    "calc": 3,
    "material": 3,
    "multiple": 4,
    "short": 4,
}
FILL_BATCH_DEFAULT = 5

# 难度对批量的影响：**困难题比简单题更吃推理 token**。
# 生产实测（2026-11-05，MiniMax-M3.1-Flash）同一提示词下：
#   easy → output_tokens=277，reasoning=80，正文 494 字，正常；
#   hard → output_tokens=8192，reasoning=8191，正文 0 字，整批作废。
# 只按题型分档时 hard 仍按 5 道发，必然 100% 失败并白白浪费一次
# 60~90s 的「减半重试」往返，故对困难档再打对折。
FILL_BATCH_HARD_DIVISOR = 2


def _fill_batch_cap(qtype: str, difficulty: str = "") -> int:
    """单批题量上限 = 题型分档，困难题再对折（推理 token 更贵）。"""
    cap = FILL_BATCH_BY_TYPE.get(qtype, FILL_BATCH_DEFAULT)
    if str(difficulty or "").strip() == "hard":
        cap = max(1, cap // FILL_BATCH_HARD_DIVISOR)
    return cap
