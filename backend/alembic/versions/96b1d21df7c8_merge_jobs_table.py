"""merge_jobs_table

Revision ID: 96b1d21df7c8
Revises: 20260119_200000, 20260120_100000
Create Date: 2026-01-21 22:02:45.257273

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '96b1d21df7c8'
down_revision: Union[str, None] = ('20260119_200000', '20260120_100000')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
