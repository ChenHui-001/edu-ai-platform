"""Persistent learning extensions."""
from alembic import op
import sqlalchemy as sa

revision = "0003_learning_extensions"
down_revision = "0002_math_taxonomy"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("edu_remediation_plan",
                    sa.Column("id", sa.Integer(), primary_key=True),
                    sa.Column("student_id", sa.Integer(), sa.ForeignKey("sys_user.id"), nullable=False),
                    sa.Column("diagnosis_id", sa.Integer(), sa.ForeignKey("edu_taxonomy_diagnosis_session.id"), nullable=False),
                    sa.Column("title", sa.String(128), nullable=False),
                    sa.Column("payload", sa.Text(), nullable=False),
                    sa.Column("version", sa.Integer(), nullable=False),
                    sa.Column("created_at", sa.DateTime(), nullable=False),
                    sa.Column("updated_at", sa.DateTime(), nullable=False),
                    sa.UniqueConstraint("student_id", "diagnosis_id", name="uq_remediation_diagnosis"))
    op.create_index("ix_edu_remediation_plan_student_id", "edu_remediation_plan", ["student_id"])
    op.create_table("edu_tutor_feedback",
                    sa.Column("id", sa.Integer(), primary_key=True),
                    sa.Column("user_id", sa.Integer(), sa.ForeignKey("sys_user.id"), nullable=False),
                    sa.Column("question_id", sa.Integer(), sa.ForeignKey("edu_question.id"), nullable=False),
                    sa.Column("stage", sa.String(16), nullable=False),
                    sa.Column("content", sa.Text(), nullable=False),
                    sa.Column("correction", sa.Text(), nullable=True),
                    sa.Column("reviewer_id", sa.Integer(), sa.ForeignKey("sys_user.id"), nullable=True),
                    sa.Column("status", sa.String(16), nullable=False),
                    sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_edu_tutor_feedback_user_id", "edu_tutor_feedback", ["user_id"])
    op.create_table("edu_taxonomy_sync_run",
                    sa.Column("id", sa.Integer(), primary_key=True),
                    sa.Column("user_id", sa.Integer(), sa.ForeignKey("sys_user.id"), nullable=False),
                    sa.Column("action", sa.String(16), nullable=False),
                    sa.Column("source_commit", sa.String(40), nullable=False),
                    sa.Column("status", sa.String(16), nullable=False),
                    sa.Column("report", sa.Text(), nullable=False),
                    sa.Column("bundle_path", sa.Text(), nullable=True),
                    sa.Column("backup_path", sa.Text(), nullable=True),
                    sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_edu_taxonomy_sync_run_user_id", "edu_taxonomy_sync_run", ["user_id"])


def downgrade():
    for name in ("edu_taxonomy_sync_run", "edu_tutor_feedback", "edu_remediation_plan"):
        op.drop_table(name)
