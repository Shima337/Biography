"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('locale', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Create sessions table
    op.create_table(
        'sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sessions_id'), 'sessions', ['id'], unique=False)

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('content_text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_messages_id'), 'messages', ['id'], unique=False)

    # Create chapters table
    op.create_table(
        'chapters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=True),
        sa.Column('period_text', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chapters_id'), 'chapters', ['id'], unique=False)

    # Create memories table
    op.create_table(
        'memories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('source_message_id', sa.Integer(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('narrative', sa.Text(), nullable=False),
        sa.Column('time_text', sa.String(), nullable=True),
        sa.Column('location_text', sa.String(), nullable=True),
        sa.Column('topics', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('importance_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
        sa.ForeignKeyConstraint(['source_message_id'], ['messages.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_memories_id'), 'memories', ['id'], unique=False)

    # Create persons table (after memories for foreign key)
    op.create_table(
        'persons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('display_name', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('first_seen_memory_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['first_seen_memory_id'], ['memories.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_persons_id'), 'persons', ['id'], unique=False)

    # Create memory_person join table
    op.create_table(
        'memory_person',
        sa.Column('memory_id', sa.Integer(), nullable=False),
        sa.Column('person_id', sa.Integer(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['memory_id'], ['memories.id'], ),
        sa.ForeignKeyConstraint(['person_id'], ['persons.id'], ),
        sa.PrimaryKeyConstraint('memory_id', 'person_id')
    )

    # Create memory_chapter join table
    op.create_table(
        'memory_chapter',
        sa.Column('memory_id', sa.Integer(), nullable=False),
        sa.Column('chapter_id', sa.Integer(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['memory_id'], ['memories.id'], ),
        sa.ForeignKeyConstraint(['chapter_id'], ['chapters.id'], ),
        sa.PrimaryKeyConstraint('memory_id', 'chapter_id')
    )

    # Create question_queue table
    op.create_table(
        'question_queue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('target_type', sa.String(), nullable=False),
        sa.Column('target_ref', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_question_queue_id'), 'question_queue', ['id'], unique=False)

    # Create prompt_runs table
    op.create_table(
        'prompt_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=True),
        sa.Column('prompt_name', sa.String(), nullable=False),
        sa.Column('prompt_version', sa.String(), nullable=False),
        sa.Column('model', sa.String(), nullable=False),
        sa.Column('input_json', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('output_text', sa.Text(), nullable=True),
        sa.Column('output_json', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('parse_ok', sa.Boolean(), nullable=True),
        sa.Column('error_text', sa.Text(), nullable=True),
        sa.Column('token_in', sa.Integer(), nullable=True),
        sa.Column('token_out', sa.Integer(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_prompt_runs_id'), 'prompt_runs', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_prompt_runs_id'), table_name='prompt_runs')
    op.drop_table('prompt_runs')
    op.drop_index(op.f('ix_question_queue_id'), table_name='question_queue')
    op.drop_table('question_queue')
    op.drop_table('memory_chapter')
    op.drop_table('memory_person')
    op.drop_index(op.f('ix_persons_id'), table_name='persons')
    op.drop_table('persons')
    op.drop_index(op.f('ix_memories_id'), table_name='memories')
    op.drop_table('memories')
    op.drop_index(op.f('ix_chapters_id'), table_name='chapters')
    op.drop_table('chapters')
    op.drop_index(op.f('ix_messages_id'), table_name='messages')
    op.drop_table('messages')
    op.drop_index(op.f('ix_sessions_id'), table_name='sessions')
    op.drop_table('sessions')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
