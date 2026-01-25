"""change2 frontend_db field gallery type JSONB

Revision ID: b7d1f3ebc595
Revises: be8cce6fd1e8
Create Date: 2026-01-08 13:40:45.074302

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b7d1f3ebc595"
down_revision: Union[str, Sequence[str], None] = "be8cce6fd1e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Подготовим колонку, убрав потенциально некорректные данные
    op.execute(text("UPDATE games SET gallery = '[]' WHERE gallery = '';"))

    # Переходим к изменению типа поля
    op.execute(
        text("ALTER TABLE games ALTER COLUMN gallery TYPE JSONB USING gallery::jsonb;")
    )


def downgrade() -> None:
    """Downgrade schema."""
    # При откате возвращаем старый тип данных
    op.execute(text("ALTER TABLE games ALTER COLUMN gallery TYPE TEXT;"))
