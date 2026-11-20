"""Flow engine tables: definition, instance, task, history."""
from alembic import op
import sqlalchemy as sa

revision = "0005_flow_engine"
down_revision = "0004_tutor_feedback_scope"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("edu_flow_definition",
                    sa.Column("id", sa.Integer(), primary_key=True),
                    sa.Column("code", sa.String(64), nullable=False),
                    sa.Column("name", sa.String(128), nullable=False),
                    sa.Column("flow_type", sa.String(20), nullable=False),
                    sa.Column("trigger_type", sa.String(20), nullable=False),
                    sa.Column("trigger_behavior", sa.String(100), nullable=True),
                    sa.Column("definition", sa.Text(), nullable=False),
                    sa.Column("version", sa.Integer(), nullable=False),
                    sa.Column("status", sa.Integer(), nullable=False),
                    sa.Column("created_at", sa.DateTime(), nullable=False),
                    sa.Column("updated_at", sa.DateTime(), nullable=False),
                    sa.UniqueConstraint("code", name="uq_flow_definition_code"))
    op.create_index("ix_edu_flow_definition_code", "edu_flow_definition", ["code"])

    op.create_table("edu_flow_instance",
                    sa.Column("id", sa.Integer(), primary_key=True),
                    sa.Column("def_id", sa.Integer(),
                              sa.ForeignKey("edu_flow_definition.id", ondelete="RESTRICT"),
                              nullable=False),
                    sa.Column("biz_type", sa.String(32), nullable=False),
                    sa.Column("biz_id", sa.Integer(), nullable=False),
                    sa.Column("biz_key", sa.String(128), nullable=True),
                    sa.Column("current_activity_ids", sa.Text(), nullable=False),
                    sa.Column("variables", sa.Text(), nullable=False),
                    sa.Column("status", sa.String(20), nullable=False),
                    sa.Column("creator_id", sa.Integer(),
                              sa.ForeignKey("sys_user.id", ondelete="SET NULL"), nullable=True),
                    sa.Column("started_at", sa.DateTime(), nullable=False),
                    sa.Column("ended_at", sa.DateTime(), nullable=True),
                    sa.Column("updated_at", sa.DateTime(), nullable=False))
    op.create_index("ix_edu_flow_instance_def_id", "edu_flow_instance", ["def_id"])
    op.create_index("ix_flow_instance_biz", "edu_flow_instance", ["biz_type", "biz_id"])
    op.create_index("ix_flow_instance_status", "edu_flow_instance", ["status"])
    op.create_index("ix_flow_instance_creator", "edu_flow_instance", ["creator_id"])

    op.create_table("edu_flow_task",
                    sa.Column("id", sa.Integer(), primary_key=True),
                    sa.Column("instance_id", sa.Integer(),
                              sa.ForeignKey("edu_flow_instance.id", ondelete="CASCADE"),
                              nullable=False),
                    sa.Column("activity_id", sa.String(64), nullable=False),
                    sa.Column("activity_type", sa.String(20), nullable=False),
                    sa.Column("activity_name", sa.String(128), nullable=False),
                    sa.Column("role_code", sa.String(32), nullable=False),
                    sa.Column("assignee_id", sa.Integer(),
                              sa.ForeignKey("sys_user.id", ondelete="SET NULL"), nullable=True),
                    sa.Column("status", sa.String(20), nullable=False),
                    sa.Column("action", sa.String(20), nullable=True),
                    sa.Column("comment", sa.Text(), nullable=True),
                    sa.Column("created_at", sa.DateTime(), nullable=False),
                    sa.Column("claimed_at", sa.DateTime(), nullable=True),
                    sa.Column("done_at", sa.DateTime(), nullable=True),
                    sa.Column("deadline", sa.DateTime(), nullable=True))
    op.create_index("ix_edu_flow_task_instance_id", "edu_flow_task", ["instance_id"])
    op.create_index("ix_edu_flow_task_role_code", "edu_flow_task", ["role_code"])
    op.create_index("ix_edu_flow_task_assignee_id", "edu_flow_task", ["assignee_id"])
    op.create_index("ix_edu_flow_task_status", "edu_flow_task", ["status"])
    op.create_index("ix_flow_task_status_role", "edu_flow_task", ["status", "role_code"])
    op.create_index("ix_flow_task_assignee_status", "edu_flow_task", ["assignee_id", "status"])

    op.create_table("edu_flow_history",
                    sa.Column("id", sa.Integer(), primary_key=True),
                    sa.Column("instance_id", sa.Integer(),
                              sa.ForeignKey("edu_flow_instance.id", ondelete="CASCADE"),
                              nullable=False),
                    sa.Column("activity_id", sa.String(64), nullable=True),
                    sa.Column("activity_name", sa.String(128), nullable=True),
                    sa.Column("operator_id", sa.Integer(),
                              sa.ForeignKey("sys_user.id", ondelete="SET NULL"), nullable=True),
                    sa.Column("operator_name", sa.String(64), nullable=True),
                    sa.Column("action", sa.String(20), nullable=False),
                    sa.Column("comment", sa.Text(), nullable=True),
                    sa.Column("from_activity", sa.String(64), nullable=True),
                    sa.Column("to_activity", sa.String(64), nullable=True),
                    sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_edu_flow_history_instance_id", "edu_flow_history", ["instance_id"])
    op.create_index("ix_flow_history_instance", "edu_flow_history", ["instance_id"])
    op.create_index("ix_flow_history_created", "edu_flow_history", ["created_at"])


def downgrade():
    op.drop_table("edu_flow_history")
    op.drop_table("edu_flow_task")
    op.drop_table("edu_flow_instance")
    op.drop_table("edu_flow_definition")
