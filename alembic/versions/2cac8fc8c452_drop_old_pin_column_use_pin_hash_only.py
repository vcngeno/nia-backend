"""Drop old pin column, use pin_hash only

Revision ID: 2cac8fc8c452
Revises: 2f1ef727261d
Create Date: 2026-10-15 05:42:08.449561

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2cac8fc8c452'
down_revision: Union[str, None] = '2f1ef727261d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('children', 'pin')


def downgrade() -> None:
    op.add_column('children', sa.Column('pin', sa.String(), nullable=False))
