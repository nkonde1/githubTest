"""update business_metrics rate columns

Revision ID: update_rates_001
Revises: 
Create Date: 2025-11-07 19:57:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'update_rates_001'
down_revision = 'add_shopify_fields'  # Update this to your latest migration
branch_labels = None
depends_on = None


def upgrade():
    # Alter columns to support percentages up to 999.99%
    op.alter_column('business_metrics', 'chargeback_rate',
                    existing_type=sa.Numeric(3, 2),
                    type_=sa.Numeric(5, 2),
                    existing_nullable=True)
    
    op.alter_column('business_metrics', 'refund_rate',
                    existing_type=sa.Numeric(3, 2),
                    type_=sa.Numeric(5, 2),
                    existing_nullable=True)
    
    op.alter_column('business_metrics', 'payment_failure_rate',
                    existing_type=sa.Numeric(3, 2),
                    type_=sa.Numeric(5, 2),
                    existing_nullable=True)


def downgrade():
    # Revert back to original column types
    op.alter_column('business_metrics', 'chargeback_rate',
                    existing_type=sa.Numeric(5, 2),
                    type_=sa.Numeric(3, 2),
                    existing_nullable=True)
    
    op.alter_column('business_metrics', 'refund_rate',
                    existing_type=sa.Numeric(5, 2),
                    type_=sa.Numeric(3, 2),
                    existing_nullable=True)
    
    op.alter_column('business_metrics', 'payment_failure_rate',
                    existing_type=sa.Numeric(5, 2),
                    type_=sa.Numeric(3, 2),
                    existing_nullable=True)

