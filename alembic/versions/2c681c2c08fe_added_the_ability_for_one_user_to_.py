"""added the ability for one user to create a rating multiple time

Revision ID: 2c681c2c08fe
Revises: 956d1633f1d6
Create Date: 2026-01-18 16:23:59.718547

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2c681c2c08fe"
down_revision: Union[str, Sequence[str], None] = "956d1633f1d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # УДАЛЯЕМ старый PK (только на user_id)
    op.drop_constraint("gamesuserratings_pkey", "gamesuserratings", type_="primary")

    # СОЗДАЕМ новый composite PK (user_id + game)
    op.create_primary_key(
        "gamesuserratings_pkey",  # то же имя, но теперь composite
        "gamesuserratings",
        ["user_id", "game"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    # УДАЛЯЕМ composite PK
    op.drop_constraint("gamesuserratings_pkey", "gamesuserratings", type_="primary")

    # ВОЗВРАЩАЕМ старый PK (только user_id)
    op.create_primary_key("gamesuserratings_pkey", "gamesuserratings", ["user_id"])
