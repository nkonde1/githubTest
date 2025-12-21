"""
SQLAlchemy models initialization module for AI-embedded finance platform.

This module serves as the central hub for all database models, ensuring:
- Proper model registration with SQLAlchemy
- Consistent database table creation
- Model relationships and foreign key constraints
- Centralized model imports for the application

All models are imported here to ensure they are registered with SQLAlchemy's
metadata before database initialization occurs.
"""

from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import configure_mappers
import logging

# Configure logging for model operations
logger = logging.getLogger(__name__)

# Define consistent naming conventions for database constraints
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# Create metadata with naming conventions
metadata = MetaData(naming_convention=naming_convention)

# Create the declarative base for all models
Base = declarative_base(metadata=metadata)

# Import all model classes to register them with SQLAlchemy
# Order matters for foreign key relationships - import base models first
try:
    # Core user and authentication models
    from .user import (
        User,
        UserSession
    )
    
    # Transaction and payment models
    from .transaction import (
        Transaction,
        PaymentMethod
    )
    
    # Financing and lending models
    from .financing import (
        FinancingOffer
    )
    
    
    
    logger.info("Successfully imported all model classes")
    
except ImportError as e:
    logger.error(f"Failed to import model class: {e}")
    raise


# List of all model classes for easy access
ALL_MODELS = [
    # User models
    User,
   
    UserSession,
  
    
    # Transaction models
    Transaction,
    
    PaymentMethod,
   
    
    # Financing models
    
    FinancingOffer,
    
    
    
]

# Model categories for organized access
USER_MODELS = [User, UserSession]
TRANSACTION_MODELS = [Transaction, PaymentMethod]
FINANCING_MODELS = [FinancingOffer]



def configure_model_relationships():
    """
    Configure and validate all model relationships.
    
    This function should be called after all models are imported
    to ensure proper relationship configuration and validation.
    """
    try:
        # Configure all mappers to validate relationships
        configure_mappers()
        logger.info("Successfully configured all model relationships")
        return True
    except Exception as e:
        logger.error(f"Failed to configure model relationships: {e}")
        return False


def get_model_by_name(model_name: str):
    """
    Get a model class by its name.
    
    Args:
        model_name (str): Name of the model class
        
    Returns:
        SQLAlchemy model class or None if not found
    """
    for model in ALL_MODELS:
        if model.__name__ == model_name:
            return model
    return None


def get_models_by_category(category: str):
    """
    Get models by category.
    
    Args:
        category (str): Model category ('user', 'transaction', 'financing', etc.)
        
    Returns:
        List of model classes in the specified category
    """
    category_mapping = {
        'user': USER_MODELS,
        'transaction': TRANSACTION_MODELS,
        'financing': FINANCING_MODELS,
        
    }
    
    return category_mapping.get(category.lower(), [])


def get_table_names():
    """
    Get all table names from registered models.
    
    Returns:
        List of table names
    """
    return [model.__tablename__ for model in ALL_MODELS if hasattr(model, '__tablename__')]


def validate_models():
    """
    Validate all models for common issues.
    
    Returns:
        dict: Validation results with any issues found
    """
    issues = {
        'missing_tablename': [],
        'missing_primary_key': [],
        'circular_imports': [],
        'relationship_errors': []
    }
    
    for model in ALL_MODELS:
        # Check for __tablename__
        if not hasattr(model, '__tablename__'):
            issues['missing_tablename'].append(model.__name__)
        
        # Check for primary key
        if not hasattr(model, '__table__'):
            continue
            
        primary_keys = [col for col in model.__table__.columns if col.primary_key]
        if not primary_keys:
            issues['missing_primary_key'].append(model.__name__)
    
    # Try to configure mappers to catch relationship issues
    try:
        configure_mappers()
    except Exception as e:
        issues['relationship_errors'].append(str(e))
    
    return issues


# Database initialization utilities
def create_all_tables(engine):
    """
    Create all tables defined by the models.
    
    Args:
        engine: SQLAlchemy engine instance
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Successfully created all database tables")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


def drop_all_tables(engine):
    """
    Drop all tables defined by the models.
    
    Args:
        engine: SQLAlchemy engine instance
    """
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("Successfully dropped all database tables")
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        raise


def get_model_dependencies():
    """
    Get model dependency graph for migration ordering.
    
    Returns:
        dict: Model dependencies mapping
    """
    dependencies = {}
    
    for model in ALL_MODELS:
        if not hasattr(model, '__table__'):
            continue
            
        model_name = model.__name__
        dependencies[model_name] = []
        
        # Check foreign key dependencies
        for column in model.__table__.columns:
            if column.foreign_keys:
                for fk in column.foreign_keys:
                    ref_table = fk.column.table.name
                    # Find model with this table name
                    for dep_model in ALL_MODELS:
                        if hasattr(dep_model, '__tablename__') and dep_model.__tablename__ == ref_table:
                            dependencies[model_name].append(dep_model.__name__)
                            break
    
    return dependencies


# Export commonly used items
__all__ = [
    'Base',
    'metadata',
    'ALL_MODELS',
    'USER_MODELS',
    'TRANSACTION_MODELS',
    'FINANCING_MODELS',
    'ANALYTICS_MODELS',
    'AI_MODELS',
    'INTEGRATION_MODELS',
    'NOTIFICATION_MODELS',
    'AUDIT_MODELS',
    'configure_model_relationships',
    'get_model_by_name',
    'get_models_by_category',
    'get_table_names',
    'validate_models',
    'create_all_tables',
    'drop_all_tables',
    'get_model_dependencies',
    # Individual model classes
    'User',
    'UserProfile',
    'Transaction',
    'FinancingApplication',
    'AIInsight',
    'AnalyticsQuery',
]

# Initialize model relationships on import
if configure_model_relationships():
    logger.info("Models initialization completed successfully")
else:
    logger.warning("Models initialization completed with warnings")
