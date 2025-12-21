# ===============================
# MISSING BACKEND FILES - PRODUCTION READY
# ===============================

# 1. backend/app/core/security.py
"""
Security utilities for JWT authentication and password handling
"""
from datetime import datetime, timedelta
from typing import Optional, Union, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status
import secrets
import os

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

class SecurityManager:
    """Centralized security management"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate password hash"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    @staticmethod
    def verify_token(token: str) -> dict:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )

# ===============================
# 2. backend/app/core/logging.py
"""
Centralized logging configuration
"""
import logging
import logging.config
import os
from pathlib import Path

# Create logs directory
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": "logs/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        },
        "errors": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "detailed",
            "filename": "logs/errors.log",
            "maxBytes": 10485760,
            "backupCount": 5,
        },
    },
    "loggers": {
        "": {  # root logger
            "level": "DEBUG" if os.getenv("DEBUG", "False").lower() == "true" else "INFO",
            "handlers": ["console", "file", "errors"],
        },
        "uvicorn": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False,
        },
        "fastapi": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False,
        },
    },
}

def setup_logging():
    """Initialize logging configuration"""
    logging.config.dictConfig(LOGGING_CONFIG)
    logger = logging.getLogger(__name__)
    logger.info("Logging configuration initialized")
    return logger

# ===============================
# 3. backend/app/api/deps.py
"""
API dependencies for authentication and database sessions
"""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.core.security import SecurityManager
from app.models.user import User
import logging

logger = logging.getLogger(__name__)
security = HTTPBearer()

def get_db() -> Generator:
    """Database dependency"""
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    try:
        # Verify token
        payload = SecurityManager.verify_token(credentials.credentials)
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
        
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

# ===============================
# 4. backend/app/models/transaction.py
"""
Transaction and payment data models
"""
from sqlalchemy import Column, Integer, String, DateTime, Decimal, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class Transaction(Base):
    """Transaction model for payment processing"""
    __tablename__ = "transactions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Transaction details
    amount = Column(Decimal(10, 2), nullable=False)
    currency = Column(String(3), default="USD")
    type = Column(String(50), nullable=False)  # payment, refund, payout
    status = Column(String(50), default="pending")  # pending, completed, failed, cancelled
    
    # External references
    stripe_payment_id = Column(String(255), nullable=True)
    shopify_order_id = Column(String(255), nullable=True)
    quickbooks_txn_id = Column(String(255), nullable=True)
    
    # Metadata
    description = Column(Text, nullable=True)
    metadata = Column(Text, nullable=True)  # JSON string
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    financing_applications = relationship("FinancingApplication", back_populates="transaction")

class PaymentMethod(Base):
    """Payment method model"""
    __tablename__ = "payment_methods"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Payment method details
    type = Column(String(50), nullable=False)  # card, bank_account, wallet
    provider = Column(String(50), nullable=False)  # stripe, shopify, etc
    external_id = Column(String(255), nullable=False)
    
    # Card/Account details (encrypted)
    last_four = Column(String(4), nullable=True)
    brand = Column(String(50), nullable=True)
    exp_month = Column(Integer, nullable=True)
    exp_year = Column(Integer, nullable=True)
    
    # Status
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="payment_methods")

# ===============================
# 5. backend/app/services/data_sync.py
"""
Third-party data synchronization service
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import stripe
import requests
from sqlalchemy.orm import Session
from app.models.transaction import Transaction
from app.models.user import User
from app.core.config import settings

logger = logging.getLogger(__name__)

class DataSyncService:
    """Service for synchronizing data from external platforms"""
    
    def __init__(self):
        self.stripe_client = stripe
        self.stripe_client.api_key = settings.STRIPE_SECRET_KEY
    
    async def sync_stripe_payments(self, db: Session, user_id: str) -> List[Transaction]:
        """Sync payments from Stripe"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.stripe_customer_id:
                return []
            
            # Get recent charges
            charges = self.stripe_client.Charge.list(
                customer=user.stripe_customer_id,
                limit=100,
                created={'gte': int((datetime.now() - timedelta(days=30)).timestamp())}
            )
            
            synced_transactions = []
            for charge in charges.data:
                # Check if transaction already exists
                existing = db.query(Transaction).filter(
                    Transaction.stripe_payment_id == charge.id
                ).first()
                
                if not existing:
                    transaction = Transaction(
                        user_id=user_id,
                        amount=charge.amount / 100,  # Convert from cents
                        currency=charge.currency.upper(),
                        type="payment",
                        status="completed" if charge.status == "succeeded" else "failed",
                        stripe_payment_id=charge.id,
                        description=charge.description,
                        processed_at=datetime.fromtimestamp(charge.created)
                    )
                    db.add(transaction)
                    synced_transactions.append(transaction)
            
            db.commit()
            logger.info(f"Synced {len(synced_transactions)} Stripe transactions for user {user_id}")
            return synced_transactions
            
        except Exception as e:
            logger.error(f"Error syncing Stripe payments: {str(e)}")
            db.rollback()
            return []
    
    async def sync_shopify_orders(self, db: Session, user_id: str) -> List[Transaction]:
        """Sync orders from Shopify"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.shopify_store_url or not user.shopify_access_token:
                return []
            
            # Shopify API call
            headers = {
                'X-Shopify-Access-Token': user.shopify_access_token,
                'Content-Type': 'application/json'
            }
            
            url = f"https://{user.shopify_store_url}/admin/api/2023-10/orders.json"
            params = {
                'status': 'any',
                'limit': 250,
                'created_at_min': (datetime.now() - timedelta(days=30)).isoformat()
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            orders = response.json().get('orders', [])
            synced_transactions = []
            
            for order in orders:
                # Check if transaction already exists
                existing = db.query(Transaction).filter(
                    Transaction.shopify_order_id == str(order['id'])
                ).first()
                
                if not existing:
                    transaction = Transaction(
                        user_id=user_id,
                        amount=float(order['total_price']),
                        currency=order['currency'],
                        type="payment",
                        status="completed" if order['financial_status'] == 'paid' else "pending",
                        shopify_order_id=str(order['id']),
                        description=f"Shopify Order #{order['order_number']}",
                        processed_at=datetime.fromisoformat(order['created_at'].replace('Z', '+00:00'))
                    )
                    db.add(transaction)
                    synced_transactions.append(transaction)
            
            db.commit()
            logger.info(f"Synced {len(synced_transactions)} Shopify orders for user {user_id}")
            return synced_transactions
            
        except Exception as e:
            logger.error(f"Error syncing Shopify orders: {str(e)}")
            db.rollback()
            return []
    
    async def sync_quickbooks_transactions(self, db: Session, user_id: str) -> List[Transaction]:
        """Sync transactions from QuickBooks"""
        # QuickBooks integration would go here
        # This is a placeholder for the actual implementation
        logger.info(f"QuickBooks sync not implemented yet for user {user_id}")
        return []

# ===============================
# 6. backend/app/services/analytics_engine.py
"""
Analytics processing engine for financial insights
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models.transaction import Transaction
from app.models.user import User
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class AnalyticsEngine:
    """Advanced analytics engine for financial data processing"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_revenue_metrics(self, db: Session, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Calculate comprehensive revenue metrics"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # Get transactions for the period
            transactions = db.query(Transaction).filter(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.created_at >= start_date,
                    Transaction.type == "payment",
                    Transaction.status == "completed"
                )
            ).all()
            
            if not transactions:
                return self._empty_metrics()
            
            # Convert to DataFrame for easier analysis
            df = pd.DataFrame([{
                'amount': float(t.amount),
                'date': t.created_at.date(),
                'hour': t.created_at.hour,
                'day_of_week': t.created_at.weekday()
            } for t in transactions])
            
            # Calculate metrics
            total_revenue = df['amount'].sum()
            avg_transaction = df['amount'].mean()
            transaction_count = len(df)
            
            # Growth calculation (compare with previous period)
            prev_start = start_date - timedelta(days=days)
            prev_transactions = db.query(Transaction).filter(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.created_at >= prev_start,
                    Transaction.created_at < start_date,
                    Transaction.type == "payment",
                    Transaction.status == "completed"
                )
            ).all()
            
            prev_revenue = sum(float(t.amount) for t in prev_transactions)
            growth_rate = ((total_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
            
            # Daily revenue trend
            daily_revenue = df.groupby('date')['amount'].sum().to_dict()
            daily_revenue = {str(k): v for k, v in daily_revenue.items()}
            
            # Peak hours analysis
            hourly_revenue = df.groupby('hour')['amount'].sum()
            peak_hour = hourly_revenue.idxmax() if not hourly_revenue.empty else 0
            
            return {
                'total_revenue': round(total_revenue, 2),
                'average_transaction': round(avg_transaction, 2),
                'transaction_count': transaction_count,
                'growth_rate': round(growth_rate, 2),
                'daily_revenue': daily_revenue,
                'peak_hour': int(peak_hour),
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Error calculating revenue metrics: {str(e)}")
            return self._empty_metrics()
    
    def generate_cash_flow_forecast(self, db: Session, user_id: str, days_ahead: int = 30) -> Dict[str, Any]:
        """Generate cash flow predictions using simple moving averages"""
        try:
            # Get historical data (last 90 days)
            start_date = datetime.now() - timedelta(days=90)
            
            transactions = db.query(Transaction).filter(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.created_at >= start_date,
                    Transaction.type == "payment",
                    Transaction.status == "completed"
                )
            ).all()
            
            if len(transactions) < 7:  # Need at least a week of data
                return {'error': 'Insufficient data for forecasting'}
            
            # Convert to DataFrame
            df = pd.DataFrame([{
                'amount': float(t.amount),
                'date': t.created_at.date()
            } for t in transactions])
            
            # Daily revenue
            daily_revenue = df.groupby('date')['amount'].sum().reset_index()
            daily_revenue = daily_revenue.sort_values('date')
            
            # Calculate moving averages
            daily_revenue['7_day_ma'] = daily_revenue['amount'].rolling(window=7, min_periods=1).mean()
            daily_revenue['30_day_ma'] = daily_revenue['amount'].rolling(window=30, min_periods=1).mean()
            
            # Simple forecast using trend
            recent_avg = daily_revenue['7_day_ma'].tail(7).mean()
            trend = daily_revenue['amount'].diff().tail(14).mean()  # 2-week trend
            
            # Generate forecast
            forecast_dates = []
            forecast_amounts = []
            
            for i in range(1, days_ahead + 1):
                forecast_date = datetime.now().date() + timedelta(days=i)
                forecast_amount = max(0, recent_avg + (trend * i))  # Ensure non-negative
                
                forecast_dates.append(str(forecast_date))
                forecast_amounts.append(round(forecast_amount, 2))
            
            return {
                'forecast_dates': forecast_dates,
                'forecast_amounts': forecast_amounts,
                'current_avg_daily': round(recent_avg, 2),
                'trend': round(trend, 2),
                'confidence': 'medium' if len(transactions) > 30 else 'low'
            }
            
        except Exception as e:
            logger.error(f"Error generating cash flow forecast: {str(e)}")
            return {'error': 'Failed to generate forecast'}
    
    def detect_anomalies(self, db: Session, user_id: str) -> List[Dict[str, Any]]:
        """Detect unusual transaction patterns"""
        try:
            # Get last 60 days of transactions
            start_date = datetime.now() - timedelta(days=60)
            
            transactions = db.query(Transaction).filter(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.created_at >= start_date,
                    Transaction.type == "payment",
                    Transaction.status == "completed"
                )
            ).all()
            
            if len(transactions) < 10:
                return []
            
            amounts = [float(t.amount) for t in transactions]
            mean_amount = np.mean(amounts)
            std_amount = np.std(amounts)
            
            anomalies = []
            
            # Detect outliers (transactions > 2 standard deviations from mean)
            for transaction in transactions:
                amount = float(transaction.amount)
                z_score = abs(amount - mean_amount) / std_amount if std_amount > 0 else 0
                
                if z_score > 2:
                    anomalies.append({
                        'transaction_id': transaction.id,
                        'amount': amount,
                        'date': transaction.created_at.isoformat(),
                        'z_score': round(z_score, 2),
                        'type': 'unusually_high' if amount > mean_amount else 'unusually_low'
                    })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {str(e)}")
            return []
    
    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure"""
        return {
            'total_revenue': 0,
            'average_transaction': 0,
            'transaction_count': 0,
            'growth_rate': 0,
            'daily_revenue': {},
            'peak_hour': 0,
            'period_days': 30
        }

# ===============================
# 7. backend/app/services/ai_agent.py
"""
AI Agent service using Ollama LLaMA 3.2 integration
"""
import logging
from typing import Dict, List, Optional, Any
import httpx
import json
from datetime import datetime
from app.core.config import settings
from app.services.analytics_engine import AnalyticsEngine

logger = logging.getLogger(__name__)

class AIAgentService:
    """AI Agent powered by Ollama LLaMA 3.2 for financial insights"""
    
    def __init__(self):
        self.ollama_url = settings.OLLAMA_URL
        self.model_name = "llama3.2"
        self.analytics_engine = AnalyticsEngine()
    
    async def generate_financial_insights(self, user_data: Dict[str, Any], user_query: str = None) -> Dict[str, Any]:
        """Generate contextual financial insights"""
        try:
            # Prepare context from user data
            context = self._prepare_financial_context(user_data)
            
            # Create prompt
            prompt = self._create_insights_prompt(context, user_query)
            
            # Call Ollama
            response = await self._call_ollama(prompt)
            
            return {
                'insights': response,
                'timestamp': datetime.now().isoformat(),
                'context_used': context
            }
            
        except Exception as e:
            logger.error(f"Error generating AI insights: {str(e)}")
            return {
                'error': 'Failed to generate insights',
                'fallback_recommendations': self._get_fallback_recommendations(user_data)
            }
    
    async def answer_finance_question(self, user_data: Dict[str, Any], question: str) -> str:
        """Answer specific finance-related questions"""
        try:
            context = self._prepare_financial_context(user_data)
            
            prompt = f"""
            You are a financial advisor AI assistant. Based on the following business financial data, 
            please answer the user's question with specific, actionable advice.
            
            FINANCIAL CONTEXT:
            {json.dumps(context, indent=2)}
            
            USER QUESTION: {question}
            
            Please provide a clear, concise answer with specific recommendations based on the data.
            Focus on actionable insights and avoid generic advice.
            """
            
            response = await self._call_ollama(prompt)
            return response
            
        except Exception as e:
            logger.error(f"Error answering finance question: {str(e)}")
            return "I apologize, but I'm unable to process your question right now. Please try again later."
    
    async def generate_optimization_suggestions(self, user_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate business optimization suggestions"""
        try:
            context = self._prepare_financial_context(user_data)
            
            prompt = f"""
            Analyze the following business financial data and provide 3-5 specific optimization suggestions.
            Each suggestion should include:
            1. The issue or opportunity identified
            2. Specific action to take
            3. Expected impact/benefit
            4. Priority level (High/Medium/Low)
            
            FINANCIAL DATA:
            {json.dumps(context, indent=2)}
            
            Format your response as a JSON array of suggestion objects.
            """
            
            response = await self._call_ollama(prompt)
            
            # Try to parse as JSON, fallback to text parsing
            try:
                suggestions = json.loads(response)
                return suggestions if isinstance(suggestions, list) else []
            except json.JSONDecodeError:
                return self._parse_suggestions_from_text(response)
                
        except Exception as e:
            logger.error(f"Error generating optimization suggestions: {str(e)}")
            return self._get_fallback_suggestions()
    
    async def _call_ollama(self, prompt: str, max_tokens: int = 500) -> str:
        """Make API call to Ollama service"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "num_predict": max_tokens,
                            "temperature": 0.7,
                            "top_p": 0.9
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "No response generated")
                else:
                    logger.error(f"Ollama API error: {response.status_code}")
                    return "Unable to generate response at this time."
                    
        except Exception as e:
            logger.error(f"Error calling Ollama API: {str(e)}")
            return "Service temporarily unavailable."
    
    def _prepare_financial_context(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare financial context for AI prompts"""
        return {
            'revenue_metrics': user_data.get('revenue_metrics', {}),
            'transaction_summary': {
                'total_transactions': user_data.get('transaction_count', 0),
                'average_amount': user_data.get('average_transaction', 0),
                'peak_hours': user_data.get('peak_hours', [])
            },
            'growth_trends': {
                'revenue_growth': user_data.get('growth_rate', 0),
                'trend_direction': 'positive' if user_data.get('growth_rate', 0) > 0 else 'negative'
            },
            'anomalies': user_data.get('anomalies', []),
            'forecast': user_data.get('forecast', {})
        }
    
    def _create_insights_prompt(self, context: Dict[str, Any], user_query: str = None) -> str:
        """Create AI prompt for financial insights"""
        base_prompt = f"""
        You are an expert financial advisor AI. Analyze the following business financial data 
        and provide actionable insights and recommendations.
        
        FINANCIAL DATA:
        {json.dumps(context, indent=2)}
        
        Please provide:
        1. Key financial health indicators
        2. Notable trends or patterns
        3. Specific recommendations for improvement
        4. Risk areas to monitor
        5. Opportunities for growth
        
        Keep your response focused, actionable, and data-driven.
        """
        
        if user_query:
            base_prompt += f"\n\nUSER SPECIFIC QUESTION: {user_query}"
        
        return base_prompt
    
    def _parse_suggestions_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Parse suggestions from text response"""
        # Simple text parsing fallback
        suggestions = []
        lines = text.split('\n')
        current_suggestion = {}
        
        for line in lines:
            if 'suggestion' in line.lower() or line.strip().startswith(('1.', '2.', '3.', '4.', '5.')):
                if current_suggestion:
                    suggestions.append(current_suggestion)
                current_suggestion = {'title': line.strip(), 'priority': 'Medium'}
            elif current_suggestion and line.strip():
                current_suggestion['description'] = current_suggestion.get('description', '') + line.strip() + ' '
        
        if current_suggestion:
            suggestions.append(current_suggestion)
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def _get_fallback_recommendations(self, user_data: Dict[str, Any]) -> List[str]:
        """Provide fallback recommendations when AI fails"""
        recommendations = []
        
        revenue = user_data.get('total_revenue', 0)
        growth_rate = user_data.get('growth_rate', 0)
        transaction_count = user_data.get('transaction_count', 0)
        
        if revenue > 0:
            if growth_rate < 0:
                recommendations.append("Focus on customer retention strategies to reverse negative growth")
            elif growth_rate < 5:
                recommendations.append("Consider marketing campaigns to accelerate growth")
            
            if transaction_count > 0:
                avg_transaction = revenue / transaction_count
                if avg_transaction < 50:
                    recommendations.append("Explore upselling opportunities to increase average transaction value")
        
        recommendations.append("Review your pricing strategy against competitors")
        recommendations.append("Analyze your top-performing products or services")
        
        return recommendations
    
    def _get_fallback_suggestions(self) -> List[Dict[str, Any]]:
        """Fallback optimization suggestions"""
        return [
            {
                'title': 'Review Payment Processing Fees',
                'description': 'Analyze and optimize payment processing costs',
                'priority': 'High',
                'impact': 'Cost Reduction'
            },
            {
                'title': 'Implement Customer Segmentation',
                'description': 'Segment customers for targeted marketing',
                'priority': 'Medium',
                'impact': 'Revenue Growth'
            },
            {
                'title': 'Automate Financial Reporting',
                'description': 'Set up automated financial dashboards',
                'priority': 'Medium',
                'impact': 'Efficiency'
            }
        ]

# ===============================
# 8. backend/app/api/routes/payments.py
"""
Payment processing API routes
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.transaction import Transaction, PaymentMethod
from app.services.data_sync import DataSyncService
from app.schemas.payments import PaymentCreate, PaymentResponse, PaymentMethodResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
data_sync = DataSyncService()

@router.get("/transactions", response_model=List[PaymentResponse])
async def get_transactions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user's transactions"""
    transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    return transactions

@router.post("/sync/stripe")
async def sync_stripe_payments(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Sync payments from Stripe"""
    background_tasks.add_task(data_sync.sync_stripe_payments, db, current_user.id)
    return {"message": "Stripe sync initiated"}

@router.post("/sync/shopify")
async def sync_shopify_orders(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Sync orders from Shopify"""
    background_tasks.add_task(data_sync.sync_shopify_orders, db, current_user.id)
    return {"message": "Shopify sync initiated"}

@router.get("/methods", response_model=List[PaymentMethodResponse])
async def get_payment_methods(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user's payment methods"""
    methods = db.query(PaymentMethod).filter(
        PaymentMethod.user_id == current_user.id,
        PaymentMethod.is_active == True
    ).all()
    
    return methods

# ===============================
# 9. backend/app/api/routes/analytics.py
"""
Analytics API routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.services.analytics_engine import AnalyticsEngine
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
analytics_engine = AnalyticsEngine()

@router.get("/revenue-metrics")
async def get_revenue_metrics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get comprehensive revenue metrics"""
    metrics = analytics_engine.calculate_revenue_metrics(db, current_user.id, days)
    return metrics

@router.get("/cash-flow-forecast")
async def get_cash_flow_forecast(
    days_ahead: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get cash flow predictions"""
    forecast = analytics_engine.generate_cash_flow_forecast(db, current_user.id, days_ahead)
    return forecast

@router.get("/anomalies")
async def detect_anomalies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """Detect unusual transaction patterns"""
    anomalies = analytics_engine.detect_anomalies(db, current_user.id)
    return anomalies

@router.get("/dashboard-summary")
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get comprehensive dashboard data"""
    try:
        # Get various metrics
        revenue_metrics = analytics_engine.calculate_revenue_metrics(db, current_user.id, 30)
        forecast = analytics_engine.generate_cash_flow_forecast(db, current_user.id, 30)
        anomalies = analytics_engine.detect_anomalies(db, current_user.id)
        
        return {
            'revenue_metrics': revenue_metrics,
            'forecast': forecast,
            'anomalies': anomalies,
            'last_updated': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating dashboard summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate dashboard summary")

# ===============================
# 10. backend/app/api/routes/financing.py
"""
Financing and lending API routes
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.financing import FinancingApplication, LoanOffer
from app.services.financing import FinancingService
from app.schemas.financing import FinancingApplicationCreate, LoanOfferResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
financing_service = FinancingService()

@router.post("/applications")
async def create_financing_application(
    application: FinancingApplicationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new financing application"""
    try:
        # Create application
        app = FinancingApplication(
            user_id=current_user.id,
            amount_requested=application.amount_requested,
            purpose=application.purpose,
            business_revenue=application.business_revenue,
            time_in_business=application.time_in_business
        )
        
        db.add(app)
        db.commit()
        db.refresh(app)
        
        # Process application in background
        background_tasks.add_task(financing_service.process_application, db, app.id)
        
        return {"application_id": app.id, "status": "submitted"}
        
    except Exception as e:
        logger.error(f"Error creating financing application: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create application")

@router.get("/offers", response_model=List[LoanOfferResponse])
async def get_loan_offers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get available loan offers for user"""
    offers = db.query(LoanOffer).filter(
        LoanOffer.user_id == current_user.id,
        LoanOffer.is_active == True
    ).all()
    
    return offers

@router.get("/applications")
async def get_financing_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user's financing applications"""
    applications = db.query(FinancingApplication).filter(
        FinancingApplication.user_id == current_user.id
    ).all()
    
    return applications

# ===============================
# 11. backend/app/api/routes/insights.py
"""
AI-powered insights API routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.services.ai_agent import AIAgentService
from app.services.analytics_engine import AnalyticsEngine
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
ai_agent = AIAgentService()
analytics_engine = AnalyticsEngine()

@router.post("/generate")
async def generate_insights(
    query: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Generate AI-powered financial insights"""
    try:
        # Gather user data
        user_data = {
            **analytics_engine.calculate_revenue_metrics(db, current_user.id, 30),
            'forecast': analytics_engine.generate_cash_flow_forecast(db, current_user.id, 30),
            'anomalies': analytics_engine.detect_anomalies(db, current_user.id)
        }
        
        # Generate insights
        insights = await ai_agent.generate_financial_insights(user_data, query)
        return insights
        
    except Exception as e:
        logger.error(f"Error generating insights: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate insights")

@router.post("/ask")
async def ask_finance_question(
    question: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, str]:
    """Ask specific finance questions"""
    try:
        # Gather user data for context
        user_data = {
            **analytics_engine.calculate_revenue_metrics(db, current_user.id, 30),
            'forecast': analytics_engine.generate_cash_flow_forecast(db, current_user.id, 30)
        }
        
        answer = await ai_agent.answer_finance_question(user_data, question)
        return {"answer": answer}
        
    except Exception as e:
        logger.error(f"Error answering question: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process question")

@router.get("/optimization-suggestions")
async def get_optimization_suggestions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """Get AI-powered optimization suggestions"""
    try:
        # Gather comprehensive user data
        user_data = {
            **analytics_engine.calculate_revenue_metrics(db, current_user.id, 60),
            'forecast': analytics_engine.generate_cash_flow_forecast(db, current_user.id, 30),
            'anomalies': analytics_engine.detect_anomalies(db, current_user.id)
        }
        
        suggestions = await ai_agent.generate_optimization_suggestions(user_data)
        return suggestions
        
    except Exception as e:
        logger.error(f"Error generating suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate suggestions")

# ===============================
# 12. backend/app/services/financing.py
"""
Financing and lending service
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.financing import FinancingApplication, LoanOffer
from app.models.transaction import Transaction
from app.services.analytics_engine import AnalyticsEngine
import asyncio

logger = logging.getLogger(__name__)

class FinancingService:
    """Service for processing financing applications and generating offers"""
    
    def __init__(self):
        self.analytics_engine = AnalyticsEngine()
    
    async def process_application(self, db: Session, application_id: str):
        """Process a financing application and generate offers"""
        try:
            application = db.query(FinancingApplication).filter(
                FinancingApplication.id == application_id
            ).first()
            
            if not application:
                logger.error(f"Application {application_id} not found")
                return
            
            # Update status
            application.status = "processing"
            db.commit()
            
            # Calculate credit score and risk assessment
            risk_score = await self._calculate_risk_score(db, application)
            
            # Generate loan offers based on risk
            offers = self._generate_loan_offers(application, risk_score)
            
            # Save offers to database
            for offer_data in offers:
                offer = LoanOffer(
                    user_id=application.user_id,
                    application_id=application.id,
                    **offer_data
                )
                db.add(offer)
            
            # Update application status
            application.status = "completed"
            application.risk_score = risk_score
            db.commit()
            
            logger.info(f"Processed application {application_id}, generated {len(offers)} offers")
            
        except Exception as e:
            logger.error(f"Error processing application {application_id}: {str(e)}")
            # Update application status to failed
            application = db.query(FinancingApplication).filter(
                FinancingApplication.id == application_id
            ).first()
            if application:
                application.status = "failed"
                db.commit()
    
    async def _calculate_risk_score(self, db: Session, application: FinancingApplication) -> float:
        """Calculate risk score based on financial data"""
        try:
            # Get user's financial metrics
            metrics = self.analytics_engine.calculate_revenue_metrics(
                db, application.user_id, 90
            )
            
            # Base score calculation
            score = 500  # Start with neutral score
            
            # Revenue consistency (30% weight)
            if metrics['total_revenue'] > 0:
                revenue_score = min(metrics['total_revenue'] / 10000 * 100, 200)
                score += revenue_score * 0.3
            
            # Growth rate (25% weight)
            if metrics['growth_rate'] > 0:
                growth_score = min(metrics['growth_rate'] * 5, 150)
                score += growth_score * 0.25
            
            # Transaction volume (20% weight)
            if metrics['transaction_count'] > 0:
                volume_score = min(metrics['transaction_count'] / 100 * 100, 100)
                score += volume_score * 0.2
            
            # Business age (15% weight)
            age_score = min(application.time_in_business * 10, 100)
            score += age_score * 0.15
            
            # Application amount vs revenue ratio (10% weight)
            if metrics['total_revenue'] > 0:
                ratio = application.amount_requested / (metrics['total_revenue'] * 12)
                if ratio < 0.1:
                    score += 50 * 0.1
                elif ratio < 0.3:
                    score += 25 * 0.1
            
            # Normalize to 300-850 range (like FICO)
            normalized_score = max(300, min(850, score))
            
            return round(normalized_score, 2)
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {str(e)}")
            return 500.0  # Return neutral score on error
    
    def _generate_loan_offers(self, application: FinancingApplication, risk_score: float) -> List[Dict[str, Any]]:
        """Generate loan offers based on risk score"""
        offers = []
        
        # Define offer tiers based on risk score
        if risk_score >= 700:  # Excellent credit
            offers.extend([
                {
                    'offer_type': 'term_loan',
                    'amount': min(application.amount_requested, 250000),
                    'interest_rate': 6.5,
                    'term_months': 36,
                    'monthly_payment': self._calculate_payment(min(application.amount_requested, 250000), 6.5, 36),
                    'approval_probability': 95
                },
                {
                    'offer_type': 'line_of_credit',
                    'amount': min(application.amount_requested * 1.5, 100000),
                    'interest_rate': 8.0,
                    'term_months': 12,
                    'monthly_payment': 0,  # Interest only
                    'approval_probability': 90
                }
            ])
        elif risk_score >= 600:  # Good credit
            offers.extend([
                {
                    'offer_type': 'term_loan',
                    'amount': min(application.amount_requested, 150000),
                    'interest_rate': 9.5,
                    'term_months': 24,
                    'monthly_payment': self._calculate_payment(min(application.amount_requested, 150000), 9.5, 24),
                    'approval_probability': 80
                },
                {
                    'offer_type': 'merchant_advance',
                    'amount': min(application.amount_requested, 75000),
                    'interest_rate': 12.0,
                    'term_months': 18,
                    'monthly_payment': self._calculate_payment(min(application.amount_requested, 75000), 12.0, 18),
                    'approval_probability': 85
                }
            ])
        elif risk_score >= 500:  # Fair credit
            offers.append({
                'offer_type': 'merchant_advance',
                'amount': min(application.amount_requested, 50000),
                'interest_rate': 18.0,
                'term_months': 12,
                'monthly_payment': self._calculate_payment(min(application.amount_requested, 50000), 18.0, 12),
                'approval_probability': 65
            })
        
        return offers
    
    def _calculate_payment(self, principal: float, annual_rate: float, months: int) -> float:
        """Calculate monthly payment for loan"""
        if annual_rate == 0:
            return principal / months
        
        monthly_rate = annual_rate / 100 / 12
        payment = principal * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)
        return round(payment, 2)

# ===============================
# 13. backend/app/ml/model.py
"""
Machine Learning models for financial predictions
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, accuracy_score
import joblib
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

class FinancialMLModel:
    """ML models for financial predictions and risk assessment"""
    
    def __init__(self):
        self.revenue_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.risk_model = GradientBoostingClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.model_path = "ml_models/"
        
        # Create model directory
        os.makedirs(self.model_path, exist_ok=True)
    
    def prepare_features(self, transactions_data: List[Dict]) -> pd.DataFrame:
        """Prepare features from transaction data"""
        if not transactions_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(transactions_data)
        
        # Convert datetime
        df['date'] = pd.to_datetime(df['created_at'])
        df['amount'] = df['amount'].astype(float)
        
        # Create time-based features
        df['hour'] = df['date'].dt.hour
        df['day_of_week'] = df['date'].dt.dayofweek
        df['day_of_month'] = df['date'].dt.day
        df['month'] = df['date'].dt.month
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Aggregate features by day
        daily_features = df.groupby(df['date'].dt.date).agg({
            'amount': ['sum', 'mean', 'count', 'std'],
            'hour': ['mean', 'std'],
            'is_weekend': 'first'
        }).reset_index()
        
        # Flatten column names
        daily_features.columns = ['_'.join(col).strip() if col[1] else col[0] 
                                 for col in daily_features.columns.values]
        
        # Fill NaN values
        daily_features = daily_features.fillna(0)
        
        # Create rolling features (7-day window)
        for col in ['amount_sum', 'amount_mean', 'amount_count']:
            if col in daily_features.columns:
                daily_features[f'{col}_rolling_7'] = daily_features[col].rolling(
                    window=7, min_periods=1
                ).mean()
        
        return daily_features
    
    def train_revenue_model(self, transactions_data: List[Dict]) -> Dict[str, Any]:
        """Train revenue prediction model"""
        try:
            features_df = self.prepare_features(transactions_data)
            
            if len(features_df) < 10:
                return {'error': 'Insufficient data for training'}
            
            # Prepare target variable (next day revenue)
            features_df['target'] = features_df['amount_sum'].shift(-1)
            features_df = features_df.dropna()
            
            if len(features_df) < 5:
                return {'error': 'Insufficient data after preprocessing'}
            
            # Select features
            feature_columns = [col for col in features_df.columns 
                             if col not in ['date_', 'target'] and not col.startswith('date')]
            
            X = features_df[feature_columns]
            y = features_df['target']
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            self.revenue_model.fit(X_train_scaled, y_train)
            
            # Evaluate
            train_pred = self.revenue_model.predict(X_train_scaled)
            test_pred = self.revenue_model.predict(X_test_scaled)
            
            train_mae = mean_absolute_error(y_train, train_pred)
            test_mae = mean_absolute_error(y_test, test_pred)
            
            # Save model
            self._save_models()
            self.is_trained = True
            
            return {
                'status': 'success',
                'train_mae': round(train_mae, 2),
                'test_mae': round(test_mae, 2),
                'feature_importance': dict(zip(
                    feature_columns, 
                    self.revenue_model.feature_importances_
                ))
            }
            
        except Exception as e:
            logger.error(f"Error training revenue model: {str(e)}")
            return {'error': f'Training failed: {str(e)}'}
    
    def predict_revenue(self, recent_data: List[Dict], days_ahead: int = 7) -> List[float]:
        """Predict future revenue"""
        try:
            if not self.is_trained:
                self._load_models()
            
            features_df = self.prepare_features(recent_data)
            
            if features_df.empty:
                return [0.0] * days_ahead
            
            # Get latest features
            latest_features = features_df.iloc[-1:].select_dtypes(include=[np.number])
            
            # Remove date columns
            feature_columns = [col for col in latest_features.columns 
                             if not col.startswith('date')]
            latest_features = latest_features[feature_columns]
            
            # Scale features
            features_scaled = self.scaler.transform(latest_features)
            
            # Generate predictions
            predictions = []
            current_features = features_scaled[0].copy()
            
            for _ in range(days_ahead):
                pred = self.revenue_model.predict(current_features.reshape(1, -1))[0]
                predictions.append(max(0, pred))  # Ensure non-negative
                
                # Update features for next prediction (simple approach)
                current_features = np.roll(current_features, 1)
                current_features[0] = pred
            
            return [round(p, 2) for p in predictions]
            
        except Exception as e:
            logger.error(f"Error predicting revenue: {str(e)}")
            return [0.0] * days_ahead
    
    def _save_models(self):
        """Save trained models"""
        try:
            joblib.dump(self.revenue_model, f"{self.model_path}/revenue_model.joblib")
            joblib.dump(self.risk_model, f"{self.model_path}/risk_model.joblib")
            joblib.dump(self.scaler, f"{self.model_path}/scaler.joblib")
            logger.info("Models saved successfully")
        except Exception as e:
            logger.error(f"Error saving models: {str(e)}")
    
    def _load_models(self):
        """Load trained models"""
        try:
            if os.path.exists(f"{self.model_path}/revenue_model.joblib"):
                self.revenue_model = joblib.load(f"{self.model_path}/revenue_model.joblib")
                self.risk_model = joblib.load(f"{self.model_path}/risk_model.joblib")
                self.scaler = joblib.load(f"{self.model_path}/scaler.joblib")
                self.is_trained = True
                logger.info("Models loaded successfully")
            else:
                logger.warning("No saved models found")
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")

# ===============================
        