"""merge stt and interaction branches

Revision ID: 37230f605b1b
Revises: 20260119_200000, 477f0ffdd804
Create Date: 2026-01-21 08:56:15.191580

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '37230f605b1b'
down_revision: Union[str, None] = ('20260119_200000', '477f0ffdd804')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
