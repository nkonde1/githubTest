"""add credit score column

Revision ID: add_credit_score_001
Revises: update_rates_001
Create Date: 2025-12-09 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_credit_score_001'
down_revision = 'update_rates_001'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('business_metrics', sa.Column('credit_score', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('business_metrics', 'credit_score')
