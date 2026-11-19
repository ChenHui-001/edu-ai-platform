"""Scope teacher corrections to a class."""
from alembic import op
import sqlalchemy as sa

revision = "0004_tutor_feedback_scope"
down_revision = "0003_learning_extensions"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("edu_tutor_feedback") as batch:
        batch.add_column(sa.Column("class_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_tutor_feedback_class", "edu_class", ["class_id"], ["id"], ondelete="SET NULL")
        batch.create_index("ix_edu_tutor_feedback_class_id", ["class_id"])


def downgrade():
    with op.batch_alter_table("edu_tutor_feedback") as batch:
        batch.drop_index("ix_edu_tutor_feedback_class_id")
        batch.drop_constraint("fk_tutor_feedback_class", type_="foreignkey")
        batch.drop_column("class_id")
