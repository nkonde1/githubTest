"""
FastAPI routes for AI-powered insights and analytics.

This module provides endpoints for generating AI-driven insights, recommendations,
and conversational analytics for SMB retailers using LLaMA 3.2 via Ollama.
"""

import logging
from datetime import datetime, timedelta
import asyncio
from typing import Dict, List, Optional, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from celery.result import AsyncResult
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.schemas.insights import (
    InsightRequest,
    InsightResponse,
    ChatMessage,
    ChatResponse,
    AnalyticsInsightRequest,
    RecommendationResponse,
    InsightTask
)
from app.models.user import User
from app.models.transaction import Transaction
from app.models.financing import FinancingOffer, LoanApplication, BusinessMetrics
from app.services.ai_agent import AIAgentService
from app.services.analytics_engine import AnalyticsEngine
from app.core.config import settings
from app.core.logging import get_logger
from app.celery_worker import process_ai_insights, generate_analytics
from app.redis_client import redis_client
import json

# Initialize router and dependencies
# NOTE: Do not add a module-level path prefix here because main.py already
# mounts this router at "/api/v1/insights". Having a prefix here would create
# a doubled path like "/api/v1/insights/insights/*" and cause 404s.
router = APIRouter(tags=["insights"])
security = HTTPBearer()
logger = get_logger(__name__)

# Initialize services
db = get_db()
ai_agent = AIAgentService()
analytics_engine = AnalyticsEngine(db, ai_agent)


@router.post("/generate", response_model=InsightResponse)
async def generate_insights(
    request: InsightRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate AI-powered insights based on user data and specific focus areas.
    
    This endpoint analyzes user transaction data, payment patterns, and business
    metrics to provide actionable insights using LLaMA 3.2.
    """
    try:
        logger.info(f"Generating insights for user {current_user.id}, focus: {request.focus_area}")
        
        # Validate request parameters
        if not request.focus_area or request.focus_area not in [
            "revenue", "cashflow", "customer_behavior", "inventory", 
            "financing", "growth", "risk_analysis", "market_trends"
        ]:
            raise HTTPException(
                status_code=400,
                detail="Invalid focus area. Must be one of: revenue, cashflow, customer_behavior, inventory, financing, growth, risk_analysis, market_trends"
            )
        
        # Check rate limiting
        rate_limit_key = f"insights:rate_limit:{current_user.id}"
        current_requests = redis_client.get(rate_limit_key)
        if current_requests and int(current_requests) >= settings.INSIGHTS_RATE_LIMIT:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please wait before requesting more insights."
            )
        
        # Gather user data for context
        user_data = await _gather_user_context(current_user, db, request.date_range)
        
        # Generate task ID for tracking
        task_id = str(uuid4())
        
        # Queue background task for insight generation
        if request.async_processing:
            task = generate_insights_task.delay(
                user_id=current_user.id,
                focus_area=request.focus_area,
                user_data=user_data,
                parameters=request.parameters or {},
                task_id=task_id
            )
            
            # Store task info in Redis
            redis_client.setex(
                f"insights:task:{task_id}",
                3600,  # 1 hour expiry
                task.id
            )
            
            return InsightResponse(
                task_id=task_id,
                status="processing",
                message="Insight generation started. Use task_id to check status.",
                estimated_completion=datetime.utcnow() + timedelta(minutes=2)
            )
        
        # Synchronous processing for immediate results
        insights = await ai_agent.generate_insights(
            user_data=user_data,
            focus_area=request.focus_area,
            parameters=request.parameters or {}
        )
        
        # Update rate limiting
        redis_client.incr(rate_limit_key)
        redis_client.expire(rate_limit_key, 3600)  # Reset every hour
        
        # Log insight generation for analytics
        background_tasks.add_task(
            _log_insight_usage,
            user_id=current_user.id,
            focus_area=request.focus_area,
            response_length=len(str(insights))
        )
        
        return InsightResponse(
            task_id=task_id,
            status="completed",
            insights=insights,
            generated_at=datetime.utcnow(),
            confidence_score=insights.get("confidence", 0.85),
            data_points_analyzed=user_data.get("transaction_count", 0)
        )
        
    except Exception as e:
        logger.error(f"Error generating insights: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate insights. Please try again later."
        )


@router.get("/status/{task_id}")
async def get_insight_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Check the status of an asynchronous insight generation task.
    """
    try:
        # Get Celery task ID from Redis
        celery_task_id = redis_client.get(f"insights:task:{task_id}")
        if not celery_task_id:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Check task status
        result = AsyncResult(celery_task_id.decode())
        
        if result.state == "PENDING":
            return {"status": "processing", "message": "Task is being processed"}
        elif result.state == "SUCCESS":
            return {
                "status": "completed",
                "insights": result.result,
                "completed_at": datetime.utcnow()
            }
        elif result.state == "FAILURE":
            return {
                "status": "failed",
                "error": str(result.info),
                "failed_at": datetime.utcnow()
            }
        else:
            return {"status": result.state.lower()}
            
    except Exception as e:
        logger.error(f"Error checking task status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to check task status")


@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    message: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Interactive chat interface for asking questions about business analytics and insights.
    
    Provides a conversational interface where users can ask natural language
    questions about their business data and receive AI-powered responses.
    """
    try:
        logger.info(f"Chat request from user {current_user.id}: {message.content[:100]}...")
        
        # Validate message
        if not message.content or len(message.content.strip()) < 3:
            raise HTTPException(
                status_code=400,
                detail="Message content is too short. Please provide a meaningful question."
            )
        
        # Check for inappropriate content
        if await _contains_inappropriate_content(message.content):
            raise HTTPException(
                status_code=400,
                detail="Message contains inappropriate content."
            )
        
        # Get conversation context
        conversation_context = await _get_conversation_context(
            current_user.id,
            message.conversation_id
        )
        
        # Gather relevant user data based on message context
        user_data = await _gather_contextual_data(current_user, db, message.content)
        
        # Generate AI response
        response = await ai_agent.chat_with_agent(
            user_message=message.content,
            context={
                "user_profile": {
                    "id": str(current_user.id),
                    "business_name": current_user.business_name,
                    "industry": getattr(current_user, "industry", None),
                },
                "conversation_context": conversation_context,
                "data": user_data,
            }
        )
        
        # Store conversation in Redis for context
        await _store_conversation_turn(
            current_user.id,
            message.conversation_id,
            message.content,
            (response.get("response") if isinstance(response, dict) else (response or ""))
        )
        
        return ChatResponse(
            conversation_id=message.conversation_id,
            response=(response.get("response") if isinstance(response, dict) else response) or "",
            suggestions=response.get("suggestions", []),
            data_visualizations=response.get("visualizations", []),
            follow_up_questions=response.get("follow_ups", []),
            confidence=response.get("confidence", 0.8),
            response_time=response.get("processing_time", 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat response: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate chat response. Please try again."
        )


@router.post("/recommendations", response_model=List[RecommendationResponse])
async def get_recommendations(
    request: AnalyticsInsightRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get AI-powered recommendations for business optimization.
    
    Analyzes user data to provide actionable recommendations for improving
    revenue, reducing costs, optimizing cashflow, and growing the business.
    """
    try:
        logger.info(f"Generating recommendations for user {current_user.id}")
        
        # Gather comprehensive user data
        user_data = await _gather_user_context(current_user, db, request.date_range)
        
        # Run analytics to identify optimization opportunities
        analytics_results = await analytics_engine._generate_ai_insights(
            user_data=user_data,
            focus_areas=request.focus_areas or ["revenue", "costs", "cashflow"]
        )
        
        # Generate AI-powered recommendations
        recommendations = await ai_agent.generate_financing_recommendations(
            analytics_results=analytics_results,
            user_preferences=current_user.preferences or {},
            business_context=user_data.get("business_profile", {})
        )
        
        # Format and prioritize recommendations
        formatted_recommendations = []
        for idx, rec in enumerate(recommendations[:10]):  # Limit to top 10
            formatted_recommendations.append(RecommendationResponse(
                id=f"rec_{current_user.id}_{idx}",
                title=rec["title"],
                description=rec["description"],
                category=rec["category"],
                priority=rec["priority"],
                impact_score=rec["impact_score"],
                effort_required=rec["effort_required"],
                implementation_steps=rec["steps"],
                expected_outcome=rec["expected_outcome"],
                confidence=rec["confidence"],
                supporting_data=rec.get("supporting_data", {}),
                created_at=datetime.utcnow()
            ))
        
        return formatted_recommendations
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate recommendations. Please try again later."
        )


@router.post("/trends/analyze")
async def analyze_trends(
    background_tasks: BackgroundTasks,
    date_range: Optional[int] = Query(30, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user)
):
    """
    Trigger background analysis of business trends and patterns.
    
    Analyzes historical data to identify trends, seasonal patterns,
    and predict future performance using AI models.
    """
    try:
        # Queue trend analysis task
        task = analyze_trends_task.delay(
            user_id=current_user.id,
            date_range=date_range,
            analysis_types=["revenue", "customer", "seasonal", "growth"]
        )
        
        return {
            "task_id": task.id,
            "status": "started",
            "message": "Trend analysis started. Results will be available in insights dashboard.",
            "estimated_completion": datetime.utcnow() + timedelta(minutes=5)
        }
        
    except Exception as e:
        logger.error(f"Error starting trend analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to start trend analysis"
        )


@router.get("/history")
async def get_insights_history(
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    focus_area: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve user's insights generation history.
    """
    try:
        # Get insights history from Redis/Database
        history_key = f"insights:history:{current_user.id}"
        
        # This would typically come from a database table
        # For now, using Redis for demonstration
        history_data = redis_client.lrange(history_key, offset, offset + limit - 1)
        
        insights_history = []
        for item in history_data:
            import json
            insight_data = json.loads(item.decode())
            if not focus_area or insight_data.get("focus_area") == focus_area:
                insights_history.append(insight_data)
        
        return {
            "insights": insights_history,
            "total": len(insights_history),
            "offset": offset,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error fetching insights history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch insights history"
        )


@router.get("/chat/history/{conversation_id}")
async def get_chat_history(
    conversation_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve conversation history for a specific conversation ID.
    """
    try:
        # Get conversation history from Redis
        conversation_context = await _get_conversation_context(
            str(current_user.id),
            conversation_id
        )
        
        # Format messages for frontend
        messages = []
        for turn in conversation_context:
            if turn.get("user"):
                messages.append({
                    "role": "user",
                    "content": turn.get("user"),
                    "timestamp": turn.get("ts"),
                })
            if turn.get("ai"):
                messages.append({
                    "role": "assistant",
                    "content": turn.get("ai"),
                    "timestamp": turn.get("ts"),
                })
        
        return {
            "conversation_id": conversation_id,
            "messages": messages,
            "total_messages": len(messages),
        }
        
    except Exception as e:
        logger.error(f"Error fetching chat history: {str(e)}")
        # Return empty history instead of error to allow new conversations
        return {
            "conversation_id": conversation_id,
            "messages": [],
            "total_messages": 0,
        }


# Helper functions

async def _gather_user_context(user: User, db: AsyncSession, date_range: Optional[int] = 30) -> Dict[str, Any]:
    """Gather user's financial context for AI insights.
    
    Args:
        user: User object
        db: Database session
        date_range: Number of days to fetch (None = fetch ALL data, no date filter)
    """
    try:
        end_date = datetime.utcnow()
        
        # Build query filters
        filters = [Transaction.user_id == user.id]
        
        # Apply date filter only if date_range is specified
        if date_range is not None:
            start_date = end_date - timedelta(days=date_range)
            filters.append(Transaction.created_at >= start_date)
            filters.append(Transaction.created_at <= end_date)
            date_range_info = {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
                "days": date_range
            }
        else:
            # No date filter - fetch ALL data
            start_date = None
            date_range_info = {
                "start": None,
                "end": end_date.isoformat() if end_date else None,
                "days": None,
                "note": "All available data"
            }
        
        # Get transactions using async SQLAlchemy
        query = select(Transaction).where(*filters).order_by(Transaction.created_at.desc())
        result = await db.execute(query)
        all_transactions = result.scalars().all()
        
        # For large datasets, sample transactions but keep all for metrics calculation
        # Limit transaction list to last 500 for context size, but use all for calculations
        transaction_sample = all_transactions[:500] if len(all_transactions) > 500 else all_transactions
        
        # Calculate key metrics from ALL transactions (not just sample)
        # Include both "payment" and "sale" transaction types for revenue
        # Convert to ZMW (Zambian Kwacha) for consistent analysis
        # Exchange rates (approximate): 1 USD = 27 ZMW, 1 EUR = 29 ZMW
        total_revenue = 0
        for t in all_transactions:
            if t.status == "completed" and t.transaction_type in ["payment", "sale"]:
                amount = float(t.amount)
                currency = getattr(t, "currency", "ZMW") or "ZMW"
                
                if currency.upper() == "USD":
                    amount = amount * 27.0
                elif currency.upper() == "EUR":
                    amount = amount * 29.0
                # Assume other currencies are ZMW or 1:1 for now
                
                total_revenue += amount
                
        total_transactions = len(all_transactions)
        avg_transaction = total_revenue / total_transactions if total_transactions > 0 else 0
        
        # Calculate additional metrics across all data
        completed_transactions = [t for t in all_transactions if t.status == "completed"]
        pending_transactions = [t for t in all_transactions if t.status == "pending"]
        failed_transactions = [t for t in all_transactions if t.status == "failed"]
        
        # Calculate revenue by time period for better context
        revenue_by_period = {}
        if all_transactions:
            # Get earliest transaction date
            earliest_date = min(t.created_at for t in all_transactions if t.created_at)
            if earliest_date:
                revenue_by_period["earliest_transaction"] = earliest_date.isoformat() if earliest_date else None
                revenue_by_period["total_days_in_data"] = (end_date - earliest_date).days if earliest_date else None
        
        context_data = {
            "user_id": user.id,
            "business_name": user.business_name,
            "industry": user.industry,
            "transaction_count": total_transactions,
            "total_revenue": total_revenue,
            "average_transaction": avg_transaction,
            "date_range": date_range_info,
            "transaction_summary": {
                "total": total_transactions,
                "completed": len(completed_transactions),
                "pending": len(pending_transactions),
                "failed": len(failed_transactions),
                "revenue_by_period": revenue_by_period
            },
            "transactions": [
                {
                    "id": str(t.id),
                    "amount": float(t.amount),
                    "currency": getattr(t, "currency", "ZMW"),
                    "amount_zmw": (float(t.amount) * 27.0 if getattr(t, "currency", "ZMW") == "USD" else 
                                  float(t.amount) * 29.0 if getattr(t, "currency", "ZMW") == "EUR" else 
                                  float(t.amount)),
                    "type": t.transaction_type,
                    "status": t.status,
                    "date": t.created_at.isoformat() if t.created_at else None,
                    "description": t.description
                } for t in transaction_sample  # Sample for context size
            ],
            "note": f"Analyzing {'all available data' if date_range is None else f'{date_range} days'} with {total_transactions} total transactions"
        }
        
        # Fetch financing data to enrich context
        try:
            # Active offers
            offers_query = select(FinancingOffer).where(
                FinancingOffer.user_id == user.id,
                FinancingOffer.expires_at >= datetime.utcnow()
            )
            offers_result = await db.execute(offers_query)
            offers = offers_result.scalars().all()
            
            # Recent applications
            apps_query = select(LoanApplication).where(
                LoanApplication.user_id == user.id
            ).order_by(LoanApplication.created_at.desc()).limit(5)
            apps_result = await db.execute(apps_query)
            applications = apps_result.scalars().all()
            
            context_data["financing"] = {
                "active_offers": [
                    {
                        "provider": o.lender_name,
                        "amount": float(o.amount),
                        "type": o.offer_type,
                        "rate": float(o.interest_rate)
                    } for o in offers
                ],
                "applications": [
                    {
                        "status": a.status,
                        "amount": float(a.requested_amount),
                        "date": a.created_at.isoformat() if a.created_at else None
                    } for a in applications
                ]
            }
            
            # Fetch latest business metrics for credit score
            from app.models.financing import BusinessMetrics
            metrics_query = select(BusinessMetrics).where(
                BusinessMetrics.user_id == user.id
            ).order_by(BusinessMetrics.calculated_at.desc()).limit(1)
            metrics_result = await db.execute(metrics_query)
            latest_metrics = metrics_result.scalars().first()
            
            if latest_metrics and latest_metrics.credit_score is not None:
                context_data["credit_score"] = latest_metrics.credit_score
                context_data["financing"]["credit_score"] = latest_metrics.credit_score
                
        except Exception as e:
            logger.error(f"Error fetching financing context: {str(e)}")
            # Don't fail the whole request if financing fetch fails
            
        return context_data
        
    except Exception as e:
        logger.error(f"Error gathering user context: {str(e)}")
        return {"error": "Failed to gather user context"}


async def _gather_contextual_data(user: User, db: AsyncSession, message: str) -> Dict[str, Any]:
    """Gather relevant data based on the chat message context.
    
    Intelligently detects time period queries and fetches appropriate data ranges.
    """
    message_lower = message.lower()
    
    # Detect time period queries and set appropriate date range
    date_range = None  # None means fetch ALL data
    
    # Time period detection
    if any(phrase in message_lower for phrase in ["this year", "current year", "ytd", "year to date"]):
        # Calculate days from start of current year
        now = datetime.utcnow()
        start_of_year = datetime(now.year, 1, 1)
        date_range = (now - start_of_year).days + 1
    elif any(phrase in message_lower for phrase in ["last year", "previous year", "past year"]):
        # Fetch last 365 days
        date_range = 365
    elif any(phrase in message_lower for phrase in ["all time", "ever", "all data", "entire history", "complete history"]):
        # Fetch ALL data - no date filter
        date_range = None
    elif any(phrase in message_lower for phrase in ["this month", "current month"]):
        # Calculate days from start of current month
        now = datetime.utcnow()
        start_of_month = datetime(now.year, now.month, 1)
        date_range = (now - start_of_month).days + 1
    elif any(phrase in message_lower for phrase in ["last month", "previous month"]):
        date_range = 60  # Last ~2 months to cover previous month
    elif any(phrase in message_lower for phrase in ["this quarter", "current quarter"]):
        # Calculate days from start of current quarter
        now = datetime.utcnow()
        quarter_start_month = ((now.month - 1) // 3) * 3 + 1
        start_of_quarter = datetime(now.year, quarter_start_month, 1)
        date_range = (now - start_of_quarter).days + 1
    elif any(phrase in message_lower for phrase in ["last quarter", "previous quarter"]):
        date_range = 120  # Last ~4 months to cover previous quarter
    elif any(phrase in message_lower for phrase in ["last 6 months", "past 6 months", "6 months"]):
        date_range = 180
    elif any(phrase in message_lower for phrase in ["last 3 months", "past 3 months", "3 months"]):
        date_range = 90
    elif any(word in message_lower for word in ["revenue", "sales", "income"]):
        # Default to 30 days for revenue queries unless time period specified
        date_range = 30
    elif any(word in message_lower for word in ["cash", "flow", "payment"]):
        # More recent data for cashflow
        date_range = 7
    else:
        # Default to 30 days if no specific time period detected
        date_range = 30
    
    return await _gather_user_context(user, db, date_range)


async def _get_conversation_context(user_id: str, conversation_id: str | None):
    """Fetch prior conversation turns for a user and conversation id."""
    conv_id = conversation_id or "default"
    key = f"conv:{user_id}:{conv_id}"
    try:
        messages = await asyncio.wait_for(redis_client.lrange(key, 0, -1), timeout=0.3)
        return [json.loads(m) for m in messages]
    except Exception as e:
        logger.exception("Error getting conversation context: %s", e)
        return []


async def _store_conversation_turn(user_id: str, conversation_id: str | None, user_text: str, ai_text: str):
    """Append a conversation turn to Redis for context."""
    conv_id = conversation_id or "default"
    key = f"conv:{user_id}:{conv_id}"
    turn = {
        "user": user_text,
        "ai": ai_text,
        "ts": datetime.utcnow().isoformat()
    }
    try:
        await asyncio.wait_for(redis_client.lpush(key, json.dumps(turn)), timeout=0.3)
    except Exception as e:
        logger.exception("Error storing conversation turn: %s", e)


def _serialize_transactions(transactions):
    """Serialize transactions safely for context snippets."""
    context = []
    for tx in transactions:
        try:
            context.append({
                "id": str(tx.id),
                "amount": float(tx.amount),
                "currency": getattr(tx, "currency", None),
                "status": getattr(tx, "status", None),
                "transaction_type": getattr(tx, "transaction_type", None),
                "category": getattr(tx, "category", None),
                "created_at": tx.created_at.isoformat() if getattr(tx, "created_at", None) else None
            })
        except Exception:
            logger.exception("Error serializing transaction %s", getattr(tx, "id", None))
    return context


async def _contains_inappropriate_content(content: str) -> bool:
    """Basic content filtering - would use proper content moderation in production."""
    inappropriate_keywords = ["spam", "hack", "exploit"]  # Simplified list
    return any(keyword in content.lower() for keyword in inappropriate_keywords)


async def _log_insight_usage(user_id: int, focus_area: str, response_length: int):
    """Log insight usage for analytics and billing."""
    try:
        import json
        usage_data = {
            "user_id": user_id,
            "focus_area": focus_area,
            "response_length": response_length,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store in Redis for processing
        redis_client.lpush("insights:usage_log", json.dumps(usage_data))
        
    except Exception as e:
        logger.error(f"Error logging insight usage: {str(e)}")
