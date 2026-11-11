"""学生学习域（笔记 / 错题本）与附件的请求模型。

## 这批为什么值得先迁

这 5 处都是**写接口**，而且踩过裸 Dict 的两个真实坑：

1. **字段名漂移静默生效**：`create_note` 用 `data.get("content", "")`，
   前端把 `content` 写成 `contents` 时后端不报错，学生保存的笔记直接变空，
   而且界面提示"创建成功"。迁移后 OpenAPI 里有真实字段表，拼错在 422 阶段拒绝。
2. **类型错误到 SQL 层才炸**：`subject_id` 传 `"语文"` 这种字符串，
   SQLite 无类型检查，能写进去，直到某次 JOIN 出一个不存在的学科才暴露。

## 一条必须一起改的语义：`exclude_unset`

`update_note` / `update_wrong` 原实现是 `if "title" in data: setattr(...)`，
它天然区分「没传这个字段」和「传了 null」。迁移时若写成

    if body.title is not None:
        note.title = body.title

学生就再也**清不空**标题了（传 null 和不传长得一样）。所以调用方必须用
`body.model_dump(exclude_unset=True)` 取"客户端真的发过来的字段"，
而不是靠 `None` 判断。这一点比模型本身更容易出错，因此写进模块注释。

`extra="ignore"`：存量调用方可能多传模板/前端临时参数，迁移不应让它们一夜
之间全部 422。真正的"拼错字段"仍会被 OpenAPI 文档挡住 —— 前端照着文档写。
"""
from typing import List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator


class NoteCreateIn(BaseModel):
    """创建笔记（POST /learning/notes）。"""
    model_config = ConfigDict(extra="ignore")

    title: Optional[str] = Field(default=None, max_length=200, description="标题，空则填「未命名笔记」")
    content: Optional[str] = Field(default=None, description="正文，支持 Markdown")
    format: Optional[str] = Field(default=None, description="markdown / text，默认 markdown")
    subject_id: Optional[int] = Field(default=None, ge=1)
    knowledge_point_id: Optional[int] = Field(default=None, ge=1)
    # 前端历史上两种都发过：数组（多选标签）与逗号串（导入的旧数据）。
    # 收紧成单一形态会让其中一种调用方静默丢标签，所以两种都收。
    tags: Optional[Union[List[str], str]] = Field(default=None, description="标签，数组或逗号分隔串")


class NoteUpdateIn(BaseModel):
    """更新笔记（PUT /learning/notes/{id}）。

    **所有字段都可缺省**：缺省 = 不动这一列；显式传 null = 把这一列清空。
    调用方必须用 `model_dump(exclude_unset=True)` 才能区分两者。
    """
    model_config = ConfigDict(extra="ignore")

    title: Optional[str] = Field(default=None, max_length=200)
    content: Optional[str] = None
    format: Optional[str] = None
    subject_id: Optional[int] = Field(default=None, ge=1)
    knowledge_point_id: Optional[int] = Field(default=None, ge=1)
    tags: Optional[Union[List[str], str]] = None
    is_favorite: Optional[bool] = Field(default=None, description="收藏开关")

    @model_validator(mode="after")
    def _reject_null_on_not_null_columns(self):
        """`title` / `content` / `format` 是 NOT NULL 列：显式传 null 直接 422。

        不管的话，`{"content": null}` 会走到 SQL 层抛 IntegrityError，前端拿到
        一条「数据完整性错误」——既说不清是哪个字段，也看不出该改成什么。
        这里用 422 + 字段名把话说清楚。

        注意判据是 `model_fields_set`（客户端真的发了这个键），不是 `is None`：
        整个字段不传时它不在集合里，属于"不改这一列"，必须放行。
        """
        for f in ("title", "content", "format"):
            if f in self.model_fields_set and getattr(self, f) is None:
                raise ValueError(f"{f} 不能为 null（该列 NOT NULL）；不想改就省略该字段")
        return self


class NoteShareIn(BaseModel):
    """分享/取消分享（PUT /learning/notes/{id}/share）。

    `shared` 默认 True：旧实现是 `Body(default={})` + `.get("shared", True)`，
    即"不带 body 等于分享"。保持这个默认值，避免前端少传一个字段就把
    学生刚点的分享又撤回去。
    """
    model_config = ConfigDict(extra="ignore")

    shared: bool = True


class WrongQuestionUpdateIn(BaseModel):
    """标注错因 / 标记掌握（PUT /learning/wrong-questions/{id}）。

    同样靠 `exclude_unset` 区分「不动」与「清空」：`error_reason` 传 null
    表示撤销原来的错因标注。
    """
    model_config = ConfigDict(extra="ignore")

    error_reason: Optional[str] = Field(default=None, max_length=500)
    is_mastered: Optional[bool] = Field(default=None, description="掌握则写入 mastered_at，撤销则清空")


class AttachmentBindIn(BaseModel):
    """绑定业务（PUT /attachment/{id}/bind，把临时附件转正式）。

    `biz_type` / `biz_id` 成对使用，但**不做成对校验**：既有调用方
    确实传过 `biz_type="question"` + `biz_id=null`（先建、后补绑），
    强加成对校验会让这些流程 422。归属校验在 `_assert_biz_owned` 里做。
    """
    model_config = ConfigDict(extra="ignore")

    biz_type: Optional[str] = Field(default=None, max_length=32)
    biz_id: Optional[int] = Field(default=None, ge=1)
