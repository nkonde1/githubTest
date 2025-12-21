"""add shopify fields to users

Revision ID: add_shopify_fields
Revises: d3bcfb0518c7
Create Date: 2025-08-25 21:25:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_shopify_fields'
down_revision = 'd3bcfb0518c7'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add Shopify integration columns
    op.add_column('users', sa.Column('shopify_access_token', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('shopify_shop_domain', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('shopify_integration_active', sa.Boolean(), server_default='false'))

def downgrade() -> None:
    # Remove Shopify integration columns
    op.drop_column('users', 'shopify_integration_active')
    op.drop_column('users', 'shopify_shop_domain')
    op.drop_column('users', 'shopify_access_token')