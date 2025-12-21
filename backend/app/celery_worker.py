"""
Celery Worker Configuration for Finance Platform
Handles background tasks for data synchronization, ML model training, and analytics processing
"""

import os
import logging
from celery import Celery
from celery.schedules import crontab
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional

from app.core.config import settings
from app.database import get_db
from app.services.data_sync import DataSyncService
from app.services.analytics_engine import AnalyticsEngine
from app.services.ai_agent import AIAgentService
from app.models.user import User
from app.models.transaction import Transaction
from app.core.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Celery app configuration
celery_app = Celery(
    "finance_platform",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.celery_worker"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # 1 hour
    # Task routing
    task_routes={
        "sync_payment_data": {"queue": "data_sync"},
        "generate_analytics": {"queue": "analytics"},
        "train_ml_model": {"queue": "ml_processing"},
        "send_notifications": {"queue": "notifications"},
        "process_ai_insights": {"queue": "ai_processing"}
    },
    # Periodic tasks
    beat_schedule={
        "sync-stripe-data": {
            "task": "sync_payment_data",
            "schedule": crontab(minute="*/15"),  # Every 15 minutes
            "args": ("stripe",)
        },
        "sync-shopify-data": {
            "task": "sync_payment_data", 
            "schedule": crontab(minute="*/20"),  # Every 20 minutes
            "args": ("shopify",)
        },
        "sync-quickbooks-data": {
            "task": "sync_payment_data",
            "schedule": crontab(minute="*/30"),  # Every 30 minutes
            "args": ("quickbooks",)
        },
        "generate-daily-analytics": {
            "task": "generate_analytics",
            "schedule": crontab(hour=1, minute=0),  # Daily at 1 AM
            "args": ("daily",)
        },
        "generate-weekly-insights": {
            "task": "process_ai_insights",
            "schedule": crontab(hour=2, minute=0, day_of_week=1),  # Weekly on Monday at 2 AM
        },
        "retrain-ml-models": {
            "task": "train_ml_model",
            "schedule": crontab(hour=3, minute=0, day_of_week=0),  # Weekly on Sunday at 3 AM
        }
    }
)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3, "countdown": 60})
def sync_payment_data(self, provider: str, user_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Synchronize payment data from external providers (Stripe, Shopify, QuickBooks)
    
    Args:
        provider: Payment provider name ('stripe', 'shopify', 'quickbooks')
        user_id: Optional specific user ID to sync
        
    Returns:
        Dict containing sync results and statistics
    """
    try:
        logger.info(f"Starting payment data sync for provider: {provider}")
        
        db = next(get_db())
        sync_service = DataSyncService(db)
        
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            result = sync_service.sync_user_data(user, provider)
        else:
            result = sync_service.sync_all_users_data(provider)
        
        logger.info(f"Payment data sync completed for {provider}: {result}")
        return {
            "status": "success",
            "provider": provider,
            "synced_records": result.get("synced_records", 0),
            "new_transactions": result.get("new_transactions", 0),
            "updated_transactions": result.get("updated_transactions", 0),
            "errors": result.get("errors", [])
        }
        
    except Exception as exc:
        logger.error(f"Payment data sync failed for {provider}: {str(exc)}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 2, "countdown": 120})
def generate_analytics(self, period: str, user_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Generate analytics reports and insights
    
    Args:
        period: Analysis period ('daily', 'weekly', 'monthly', 'quarterly')
        user_id: Optional specific user ID to analyze
        
    Returns:
        Dict containing analytics results
    """
    try:
        logger.info(f"Starting analytics generation for period: {period}")
        
        db = next(get_db())
        analytics_engine = AnalyticsEngine(db)
        
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            result = analytics_engine.generate_user_analytics(user, period)
        else:
            result = analytics_engine.generate_platform_analytics(period)
        
        logger.info(f"Analytics generation completed for {period}")
        return {
            "status": "success",
            "period": period,
            "user_id": user_id,
            "metrics": result.get("metrics", {}),
            "insights": result.get("insights", []),
            "recommendations": result.get("recommendations", [])
        }
        
    except Exception as exc:
        logger.error(f"Analytics generation failed for {period}: {str(exc)}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 1, "countdown": 300})
def train_ml_model(self, model_type: str = "default") -> Dict[str, Any]:
    """
    Train or retrain machine learning models
    
    Args:
        model_type: Type of model to train ('default', 'fraud_detection', 'recommendation')
        
    Returns:
        Dict containing training results
    """
    try:
        logger.info(f"Starting ML model training for type: {model_type}")
        
        db = next(get_db())
        
        # Import ML training module
        from app.ml.training import MLTrainer
        
        trainer = MLTrainer(db)
        result = trainer.train_model(model_type)
        
        logger.info(f"ML model training completed for {model_type}")
        return {
            "status": "success",
            "model_type": model_type,
            "accuracy": result.get("accuracy", 0),
            "training_time": result.get("training_time", 0),
            "model_version": result.get("model_version", "unknown")
        }
        
    except Exception as exc:
        logger.error(f"ML model training failed for {model_type}: {str(exc)}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 2, "countdown": 60})
def process_ai_insights(self, user_id: Optional[int] = None, query: Optional[str] = None) -> Dict[str, Any]:
    """
    Process AI-powered insights and recommendations using LLaMA 3.2
    
    Args:
        user_id: Optional specific user ID for personalized insights
        query: Optional specific query for AI processing
        
    Returns:
        Dict containing AI-generated insights
    """
    try:
        logger.info(f"Starting AI insights processing for user: {user_id}")
        
        db = next(get_db())
        ai_service = AIAgentService()
        
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            result = ai_service.generate_user_insights(user, query)
        else:
            result = ai_service.generate_platform_insights(query)
        
        logger.info(f"AI insights processing completed")
        return {
            "status": "success",
            "user_id": user_id,
            "insights": result.get("insights", []),
            "recommendations": result.get("recommendations", []),
            "confidence_score": result.get("confidence_score", 0)
        }
        
    except Exception as exc:
        logger.error(f"AI insights processing failed: {str(exc)}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 3, "countdown": 30})
def send_notifications(self, user_id: int, notification_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send notifications to users (email, SMS, push notifications)
    
    Args:
        user_id: Target user ID
        notification_type: Type of notification ('email', 'sms', 'push', 'in_app')
        data: Notification data and content
        
    Returns:
        Dict containing notification results
    """
    try:
        logger.info(f"Sending {notification_type} notification to user {user_id}")
        
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Import notification service
        from app.services.notifications import NotificationService
        
        notification_service = NotificationService()
        result = notification_service.send_notification(user, notification_type, data)
        
        logger.info(f"Notification sent successfully to user {user_id}")
        return {
            "status": "success",
            "user_id": user_id,
            "notification_type": notification_type,
            "message_id": result.get("message_id"),
            "delivery_status": result.get("delivery_status", "sent")
        }
        
    except Exception as exc:
        logger.error(f"Notification sending failed for user {user_id}: {str(exc)}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True)
def process_webhook(self, provider: str, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process incoming webhooks from payment providers
    
    Args:
        provider: Webhook provider ('stripe', 'shopify', 'quickbooks')
        webhook_data: Raw webhook payload
        
    Returns:
        Dict containing processing results
    """
    try:
        logger.info(f"Processing webhook from {provider}")
        
        db = next(get_db())
        
        # Import webhook processor
        from app.services.webhook_processor import WebhookProcessor
        
        processor = WebhookProcessor(db)
        result = processor.process_webhook(provider, webhook_data)
        
        logger.info(f"Webhook processed successfully from {provider}")
        return {
            "status": "success",
            "provider": provider,
            "event_type": result.get("event_type"),
            "processed_at": result.get("processed_at"),
            "actions_taken": result.get("actions_taken", [])
        }
        
    except Exception as exc:
        logger.error(f"Webhook processing failed from {provider}: {str(exc)}")
        return {
            "status": "error",
            "provider": provider,
            "error": str(exc)
        }


@celery_app.task(bind=True)
def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, Any]:
    """
    Clean up old data and logs to maintain database performance
    
    Args:
        days_to_keep: Number of days of data to retain
        
    Returns:
        Dict containing cleanup results
    """
    try:
        logger.info(f"Starting data cleanup for data older than {days_to_keep} days")
        
        db = next(get_db())
        
        # Import cleanup service
        from app.services.data_cleanup import DataCleanupService
        
        cleanup_service = DataCleanupService(db)
        result = cleanup_service.cleanup_old_data(days_to_keep)
        
        logger.info(f"Data cleanup completed")
        return {
            "status": "success",
            "days_to_keep": days_to_keep,
            "records_deleted": result.get("records_deleted", 0),
            "space_freed": result.get("space_freed", "0MB")
        }
        
    except Exception as exc:
        logger.error(f"Data cleanup failed: {str(exc)}")
        return {
            "status": "error",
            "error": str(exc)
        }


# Celery signal handlers for monitoring and logging
@celery_app.task(bind=True)
def monitor_task_health(self) -> Dict[str, Any]:
    """Monitor overall task health and system status"""
    try:
        # Get task statistics
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()
        scheduled_tasks = inspect.scheduled()
        
        # Get Redis connection info
        from backend.app.redis_client import redis_client
        redis_info = redis_client.info()
        
        return {
            "status": "healthy",
            "active_tasks": len(active_tasks) if active_tasks else 0,
            "scheduled_tasks": len(scheduled_tasks) if scheduled_tasks else 0,
            "redis_connected": redis_info.get("connected_clients", 0) > 0,
            "memory_usage": redis_info.get("used_memory_human", "unknown")
        }
        
    except Exception as exc:
        logger.error(f"Health monitoring failed: {str(exc)}")
        return {
            "status": "unhealthy",
            "error": str(exc)
        }


if __name__ == "__main__":
    # Start worker with specific configuration
    celery_app.start()
