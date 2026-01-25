"""add cookie expires

Revision ID: 73e10af7cb93
Revises: aed9e5a5f399
Create Date: 2026-01-13 21:14:16.565675

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "73e10af7cb93"
down_revision: Union[str, Sequence[str], None] = "aed9e5a5f399"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Явно указываем изменение server_default для колонки
    op.alter_column(
        "users",  # имя таблицы
        "cookie_expires",  # имя колонки
        server_default=sa.text("TIMEZONE('utc', now()) + interval '5 minutes'"),
    )


def downgrade() -> None:
    # Если нужно откатиться, можно вернуть старый default (например, func.now())
    op.alter_column("users", "cookie_expires", server_default=sa.text("now()"))
