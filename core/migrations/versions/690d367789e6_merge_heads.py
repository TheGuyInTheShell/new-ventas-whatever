"""merge_heads

Revision ID: 690d367789e6
Revises: 4b013e168101, 305d9cbda18c
Create Date: 2026-04-18 22:16:46.209628

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '690d367789e6'
down_revision: Union[str, None] = ('4b013e168101', '305d9cbda18c')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
