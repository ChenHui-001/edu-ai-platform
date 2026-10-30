"""题目「能否被当前用户放进试卷」的唯一判定口径。

## 为什么单独抽出来

同一条规则原来在两个写入口各写了一遍（`question._normalize_paper_items` 与
`paper_compose._normalize_items`），两处都是「公共库 或 本人私有」就放行 ——
**完全没看 `status`**。于是公共题库里 `draft`（AI 生成后待审核）和 `offline`
（已下架）的题，只要知道 id 就能被塞进任何教师的卷子。

这类"两套判定并存"在本项目已经踩过一次（试卷可见性），结果必然是漂移：
改了一处、另一处继续用旧口径。因此这里做成**唯一函数**，两个入口都调它。

## 策略（按优先级）

| 场景 | 是否可用 | 理由 |
|---|---|---|
| 系统管理员 | 可用（不限） | 管理员要能排障、修数据 |
| 本人私有题 | 可用，**不限状态** | 教师编辑自己的草稿/停用题是合法场景，收紧会打断正常备课 |
| 公共题库题 | 仅 `published` 可用 | 待审核、已下架的题不应出现在卷面上 |
| 他人私有题 | 不可用 | 越权 |

「本人题不看状态」是这里唯一需要人为决策的一点：待审核态的题只有
`bank_type=public` 才有审核含义，`private` 的 `draft` 只是"还没整理好"，
限制它没有收益，只会让教师在"先建题、后改卷"的流程里被拦。
"""
from typing import Optional

# 状态中文名，用于把"不可用"的原因说成人话（前端直接展示 message）
STATUS_LABEL = {
    "draft": "待审核",
    "published": "已发布",
    "offline": "已下架",
}


def question_usable_error(
    question, *, user_id: Optional[int], is_admin: bool = False,
) -> Optional[str]:
    """返回不可用原因（中文）；`None` 表示可用。"""
    if is_admin:
        return None

    qid = getattr(question, "id", "?")
    owner_id = getattr(question, "owner_id", None)
    # 本人题：先判本人，再判状态 —— 教师改自己的草稿不该被"未发布"拦住
    if owner_id is not None and user_id is not None and int(owner_id) == int(user_id):
        return None

    if getattr(question, "bank_type", None) != "public":
        return f"无权使用题目（id={qid}）：仅可选公共题或本人私有题"

    status = str(getattr(question, "status", "") or "")
    if status != "published":
        return (f"题目尚未发布（id={qid}，当前{STATUS_LABEL.get(status, status or '未知')}）："
                "公共题库仅可使用已发布题目，请等待审核通过或改用本人题目")
    return None
