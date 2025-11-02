"""Rename data_source to content

Revision ID: ff0000000000
Revises: d29a5cd664c9
Create Date: 2025-11-02 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff0000000000'
down_revision: Union[str, Sequence[str], None] = 'd29a5cd664c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('wikibase', 'data_source', new_column_name='content')
    op.alter_column('postbase', 'data_source', new_column_name='content')


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('wikibase', 'content', new_column_name='data_source')
    op.alter_column('postbase', 'content', new_column_name='data_source')

