"""Flow engine: transfer / urge / overdue support.

- edu_flow_transfer: 转办留痕表
- edu_flow_task 新增列：催办次数、最近催办时间、转办次数、最近转办时间，
  以及 deadline 上的索引（逾期待办要按 deadline 排序查）
"""
from alembic import op
import sqlalchemy as sa

revision = "0006_flow_transfer_urge"
down_revision = "0005_flow_engine"
branch_labels = None
depends_on = None


def upgrade():
    # ---- edu_flow_task 新增列 ----
    with op.batch_alter_table("edu_flow_task") as batch:
        batch.add_column(sa.Column(
            "urge_count", sa.Integer(), nullable=False, server_default="0",
            comment="催办次数"))
        batch.add_column(sa.Column(
            "last_urged_at", sa.DateTime(), nullable=True,
            comment="最近催办时间"))
        batch.add_column(sa.Column(
            "transfer_count", sa.Integer(), nullable=False, server_default="0",
            comment="转办次数"))
        batch.add_column(sa.Column(
            "last_transferred_at", sa.DateTime(), nullable=True,
            comment="最近转办时间"))

    # deadline 上的索引：逾期待办按 deadline 升序查，没索引会全表扫。
    op.create_index("ix_edu_flow_task_deadline", "edu_flow_task", ["deadline"])

    # ---- edu_flow_transfer 转办留痕 ----
    op.create_table("edu_flow_transfer",
                    sa.Column("id", sa.Integer(), primary_key=True),
                    sa.Column("task_id", sa.Integer(),
                              sa.ForeignKey("edu_flow_task.id", ondelete="CASCADE"),
                              nullable=False),
                    sa.Column("from_user_id", sa.Integer(),
                              sa.ForeignKey("sys_user.id", ondelete="SET NULL"),
                              nullable=True),
                    sa.Column("to_user_id", sa.Integer(),
                              sa.ForeignKey("sys_user.id", ondelete="CASCADE"),
                              nullable=False),
                    sa.Column("operator_id", sa.Integer(),
                              sa.ForeignKey("sys_user.id", ondelete="SET NULL"),
                              nullable=True),
                    sa.Column("reason", sa.Text(), nullable=True),
                    sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_edu_flow_transfer_task_id", "edu_flow_transfer", ["task_id"])
    op.create_index("ix_flow_transfer_task", "edu_flow_transfer", ["task_id"])
    op.create_index("ix_edu_flow_transfer_created_at", "edu_flow_transfer",
                    ["created_at"])


def downgrade():
    op.drop_table("edu_flow_transfer")
    op.drop_index("ix_edu_flow_task_deadline", table_name="edu_flow_task")
    with op.batch_alter_table("edu_flow_task") as batch:
        batch.drop_column("last_transferred_at")
        batch.drop_column("transfer_count")
        batch.drop_column("last_urged_at")
        batch.drop_column("urge_count")
