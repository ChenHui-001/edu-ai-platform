"""0002 外部知识图谱：先修边、诊断会话、外部映射字段

Revision ID: 0002_math_taxonomy
Revises: 0001_baseline
Create Date: 2026-11-17
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_math_taxonomy"
down_revision: Union[str, None] = "0001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "edu_knowledge_prerequisite",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("topic_kp_id", sa.Integer(), nullable=False,
                  comment="后继知识点（要学的点）"),
        sa.Column("prerequisite_kp_id", sa.Integer(), nullable=False,
                  comment="先修知识点（应先掌握的点）"),
        sa.Column("strength", sa.String(length=8), nullable=False,
                  comment="hard 强先修 / soft 弱先修"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False,
                  comment="manual/import/cn-math-taxonomy"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "topic_kp_id <> prerequisite_kp_id",
            name="ck_kp_prerequisite_not_self"),
        sa.ForeignKeyConstraint(
            ["prerequisite_kp_id"], ["edu_knowledge_point.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["topic_kp_id"], ["edu_knowledge_point.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "topic_kp_id", "prerequisite_kp_id", name="uq_kp_prerequisite"),
    )
    with op.batch_alter_table("edu_knowledge_prerequisite", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_edu_knowledge_prerequisite_prerequisite_kp_id"),
            ["prerequisite_kp_id"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_edu_knowledge_prerequisite_topic_kp_id"),
            ["topic_kp_id"], unique=False)

    op.create_table(
        "edu_taxonomy_diagnosis_session",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False, comment="被诊断学生"),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("grade_id", sa.Integer(), nullable=True),
        sa.Column("targets_json", sa.Text(), nullable=False,
                  comment="目标知识点 ID JSON"),
        sa.Column("mode", sa.String(length=16), nullable=False,
                  comment="target 诊断 / screen 筛查"),
        sa.Column("question_limit", sa.Integer(), nullable=False),
        sa.Column("confirm_count", sa.Integer(), nullable=False),
        sa.Column("answers_json", sa.Text(), nullable=False),
        sa.Column("status_json", sa.Text(), nullable=False),
        sa.Column("seed", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["grade_id"], ["edu_grade.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["subject_id"], ["edu_subject.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["sys_user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("edu_taxonomy_diagnosis_session", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_edu_taxonomy_diagnosis_session_created_at"),
            ["created_at"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_edu_taxonomy_diagnosis_session_grade_id"),
            ["grade_id"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_edu_taxonomy_diagnosis_session_subject_id"),
            ["subject_id"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_edu_taxonomy_diagnosis_session_user_id"),
            ["user_id"], unique=False)

    with op.batch_alter_table("edu_knowledge_point", schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            "external_source", sa.String(length=64), nullable=True,
            comment="外部来源，如 cn-math-taxonomy"))
        batch_op.add_column(sa.Column(
            "external_id", sa.String(length=64), nullable=True,
            comment="外部来源内的稳定 ID，如 cnm_p001"))
        batch_op.create_unique_constraint(
            "uq_kp_external", ["external_source", "external_id"])

    with op.batch_alter_table("edu_question", schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            "external_source", sa.String(length=64), nullable=True,
            comment="外部来源，如 cn-math-taxonomy"))
        batch_op.add_column(sa.Column(
            "external_id", sa.String(length=80), nullable=True,
            comment="外部来源内的稳定题目 ID"))
        batch_op.add_column(sa.Column(
            "extra_json", sa.Text(), nullable=True,
            comment="外部扩展字段 JSON"))
        batch_op.create_unique_constraint(
            "uq_question_external", ["external_source", "external_id"])


def downgrade() -> None:
    with op.batch_alter_table("edu_question", schema=None) as batch_op:
        batch_op.drop_constraint("uq_question_external", type_="unique")
        batch_op.drop_column("extra_json")
        batch_op.drop_column("external_id")
        batch_op.drop_column("external_source")

    with op.batch_alter_table("edu_knowledge_point", schema=None) as batch_op:
        batch_op.drop_constraint("uq_kp_external", type_="unique")
        batch_op.drop_column("external_id")
        batch_op.drop_column("external_source")

    with op.batch_alter_table("edu_taxonomy_diagnosis_session", schema=None) as batch_op:
        batch_op.drop_index(
            batch_op.f("ix_edu_taxonomy_diagnosis_session_user_id"))
        batch_op.drop_index(
            batch_op.f("ix_edu_taxonomy_diagnosis_session_subject_id"))
        batch_op.drop_index(
            batch_op.f("ix_edu_taxonomy_diagnosis_session_grade_id"))
        batch_op.drop_index(
            batch_op.f("ix_edu_taxonomy_diagnosis_session_created_at"))
    op.drop_table("edu_taxonomy_diagnosis_session")

    with op.batch_alter_table("edu_knowledge_prerequisite", schema=None) as batch_op:
        batch_op.drop_index(
            batch_op.f("ix_edu_knowledge_prerequisite_topic_kp_id"))
        batch_op.drop_index(
            batch_op.f("ix_edu_knowledge_prerequisite_prerequisite_kp_id"))
    op.drop_table("edu_knowledge_prerequisite")
