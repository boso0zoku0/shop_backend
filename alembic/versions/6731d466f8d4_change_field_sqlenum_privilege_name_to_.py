"""change field SQLEnum privilege_name to privilege

Revision ID: 6731d466f8d4
Revises: 1cd0395b01de
Create Date: 2026-02-15 13:54:28.289328

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "6731d466f8d4"
down_revision: Union[str, Sequence[str], None] = "1cd0395b01de"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Создаём новый enum
    op.execute("CREATE TYPE privilege AS ENUM ('weak', 'medium', 'best')")

    # 2. Добавляем новую колонку с именем 'privilege'
    op.add_column(
        "users",
        sa.Column(
            "privilege",  # 👈 новое имя колонки
            sa.Enum("weak", "medium", "best", name="privilege"),
            nullable=True,
        ),
    )

    # 3. Копируем данные из старой колонки
    op.execute(
        """
        UPDATE users
        SET privilege = privilege_level::text::privilege
        """
    )

    # 4. Удаляем старую колонку
    op.drop_column("users", "privilege_level")

    # 5. Удаляем старый enum
    op.execute("DROP TYPE privilege_level")


def downgrade() -> None:
    # 1. Восстанавливаем старый enum
    op.execute("CREATE TYPE privilege_level AS ENUM ('weak', 'medium', 'best')")

    # 2. Добавляем старую колонку
    op.add_column(
        "users",
        sa.Column(
            "privilege_level",
            sa.Enum("weak", "medium", "best", name="privilege_level"),
            nullable=True,
        ),
    )

    # 3. Копируем данные обратно
    op.execute(
        """
        UPDATE users
        SET privilege_level = privilege::text::privilege_level
        """
    )

    # 4. Удаляем новую колонку
    op.drop_column("users", "privilege")

    # 5. Удаляем новый enum
    op.execute("DROP TYPE privilege")
