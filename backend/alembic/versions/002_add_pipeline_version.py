"""Add pipeline_version fields

Revision ID: 002
Revises: 001
Create Date: 2026-01-22 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add pipeline_version to memories
    op.add_column('memories', sa.Column('pipeline_version', sa.String(), server_default='v1', nullable=True))
    
    # Add pipeline_version to persons
    op.add_column('persons', sa.Column('pipeline_version', sa.String(), server_default='v1', nullable=True))
    
    # Add pipeline_version to prompt_runs
    op.add_column('prompt_runs', sa.Column('pipeline_version', sa.String(), server_default='v1', nullable=True))


def downgrade() -> None:
    op.drop_column('prompt_runs', 'pipeline_version')
    op.drop_column('persons', 'pipeline_version')
    op.drop_column('memories', 'pipeline_version')
