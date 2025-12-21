"""Initial schema setup and user profile updates

Revision ID: d3bcfb0518c7
Revises: 
Create Date: 2025-06-20 21:30:51.973026
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# Add these required revision variables
revision: str = 'd3bcfb0518c7'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    connection = op.get_bind()
    
    try:
        # First rollback any failed transaction
        connection.execute(text("ROLLBACK"))
        
        print("Starting fresh transaction...")
        connection.execute(text("BEGIN"))
        
        # Create alembic_version table if it doesn't exist
        print("Creating alembic_version table...")
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR(32) NOT NULL,
                CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
            )
        """))

        # Drop constraints first
        print("Dropping foreign key constraints...")
        constraints_to_drop = [
            ('user_sessions', 'user_sessions_user_id_fkey'),
            ('ai_interactions', 'ai_interactions_user_id_fkey'),
            ('forecasts', 'forecasts_user_id_fkey'),
            ('reports', 'reports_user_id_fkey')
        ]
        
        for table, constraint in constraints_to_drop:
            try:
                connection.execute(
                    text(f"""
                    ALTER TABLE IF EXISTS {table} 
                    DROP CONSTRAINT IF EXISTS {constraint}
                    """)
                )
                print(f"Dropped constraint {constraint}")
            except Exception as e:
                print(f"Note: Could not drop constraint {constraint}: {e}")
        
        # Drop tables
        print("Dropping tables...")
        tables_to_drop = [
            'expenses', 'reports', 'data_sources', 'budget_forecast',
            'budgets', 'forecast_results', 'budget_actuals',
            'financial_documents', 'personnel_expenses', 'internal_orders',
            'budget_forecasts', 'sga_expenses', 'cost_centers',
            'ai_interactions', 'forecasts', 'user_sessions'
        ]
        
        for table in tables_to_drop:
            try:
                connection.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                print(f"Dropped table {table}")
            except Exception as e:
                print(f"Note: Error dropping {table}: {e}")
        
        # Modify users table
        print("Modifying users table...")
        try:
            # Convert ID to UUID
            connection.execute(text("""
                ALTER TABLE users 
                ALTER COLUMN id TYPE uuid 
                USING id::uuid
            """))
            
            # Add new columns
            new_columns = [
                ('is_superuser', 'boolean', 'false'),
                ('is_admin', 'boolean', 'false'),
                ('permissions', 'text[]', None),
                ('tenant_id', 'uuid', None),
                ('api_key_hash', 'text', None)
            ]
            
            for col_name, col_type, default in new_columns:
                default_clause = f"DEFAULT {default}" if default else ""
                connection.execute(text(f"""
                    ALTER TABLE users 
                    ADD COLUMN IF NOT EXISTS {col_name} {col_type} {default_clause}
                """))
                print(f"Added column {col_name}")
            
            # Commit changes
            connection.execute(text("COMMIT"))
            print("Migration completed successfully")
            
        except Exception as e:
            print(f"Error modifying users table: {e}")
            connection.execute(text("ROLLBACK"))
            raise
            
    except Exception as e:
        print(f"Migration failed: {e}")
        connection.execute(text("ROLLBACK"))
        raise


def downgrade() -> None:
    """Downgrade schema."""
    connection = op.get_bind()
    
    try:
        connection.execute(text("BEGIN"))
        
        # Remove added columns from users table
        columns_to_drop = [
            'is_superuser', 'is_admin', 'permissions',
            'tenant_id', 'api_key_hash'
        ]
        
        for column in columns_to_drop:
            connection.execute(text(f"""
                ALTER TABLE users 
                DROP COLUMN IF EXISTS {column}
            """))
        
        # Convert id back to varchar if needed
        connection.execute(text("""
            ALTER TABLE users 
            ALTER COLUMN id TYPE varchar 
            USING id::text
        """))
        
        # Drop alembic_version table
        connection.execute(text("DROP TABLE IF EXISTS alembic_version"))
        
        connection.execute(text("COMMIT"))
        print("Downgrade completed successfully")
        
    except Exception as e:
        print(f"Downgrade failed: {e}")
        connection.execute(text("ROLLBACK"))
        raise