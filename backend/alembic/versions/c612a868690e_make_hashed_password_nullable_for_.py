"""make hashed_password nullable for google auth

Revision ID: c612a868690e
Revises: 1d725155e717
Create Date: 2026-06-21 03:18:08.543217

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c612a868690e'
down_revision: Union[str, None] = '1d725155e717'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('users', 'hashed_password', existing_type=sa.String(length=1024), nullable=True)

def downgrade() -> None:
    op.alter_column('users', 'hashed_password', existing_type=sa.String(length=1024), nullable=False)
