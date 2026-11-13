"""make audit log fields nullable

Revision ID: 81c87b450f47
Revises: 6ff2a021375e
Create Date: 2026-11-12 16:04:00.977570

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '81c87b450f47'
down_revision: Union[str, None] = '6ff2a021375e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make audit_logs columns nullable for SQLite compatibility
    with op.batch_alter_table('audit_logs') as batch_op:
        batch_op.alter_column('entity_type', existing_type=sa.Text(), nullable=True)
        batch_op.alter_column('entity_id', existing_type=sa.Text(), nullable=True)
        batch_op.alter_column('correlation_id', existing_type=sa.Text(), nullable=True)


def downgrade() -> None:
    # Revert to NOT NULL
    with op.batch_alter_table('audit_logs') as batch_op:
        batch_op.alter_column('entity_type', existing_type=sa.Text(), nullable=False)
        batch_op.alter_column('entity_id', existing_type=sa.Text(), nullable=False)
        batch_op.alter_column('correlation_id', existing_type=sa.Text(), nullable=False)
