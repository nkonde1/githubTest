# backend/app/services/ai_agent.py
"""
AI Agent service for LLaMA 3.2 integration via Ollama
Provides intelligent insights, recommendations, and conversational interface
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal

from ..core.config import settings
from ..core.logging import get_logger

logger = get_logger(__name__)



class AIAgentService:
    """AI Agent service for business intelligence and chat functionality"""
    
    def __init__(self):
        self.ollama_base_url = settings.LLAMA_ENDPOINT
        self.model_name = settings.LLAMA_MODEL
        self.session = None
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
    
    async def _make_ollama_request(self, prompt: str, system_prompt: str = None) -> Dict[str, Any]:
        """Make request to Ollama API"""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }
        
        if system_prompt:
            payload["system"] = system_prompt
            
        # Debug logging
        logger.info(f"Making Ollama request to: {self.ollama_base_url}/api/generate")
        logger.info(f"Using model: {self.model_name}")
        logger.info(f"Payload: {payload}")
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_base_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result
                    else:
                        logger.error(f"Ollama API error: {response.status}")
                        logger.error(f"Response text: {await response.text()}")
                        # Return a fallback response instead of raising an exception
                        return {
                            "response": "I'm experiencing some technical difficulties with my AI service. Please try again in a moment, or contact support if the issue persists. In the meantime, I can help you with basic questions about your financial data."
                        }
                        
        except asyncio.TimeoutError:
            logger.error("Ollama API request timed out")
            return {
                "response": "I'm experiencing some technical difficulties with my AI service. Please try again in a moment."
            }
        except Exception as e:
            logger.error(f"Error making Ollama request: {str(e)}")
            return {
                "response": "I'm experiencing some technical difficulties with my AI service. Please try again in a moment."
            }
    
    async def generate_business_insights(self, metrics_context: str) -> Dict[str, str]:
        """Generate business insights from metrics data"""
        
        system_prompt = """
        You are a senior business intelligence analyst for SMBs in Zambia.
        Analyze the provided metrics including revenue, risk, and financing data.
        
        Generate insights in 3 categories:
        1. **Revenue & Operations**: Trends, growth, and operational efficiency (in ZMW).
        2. **Risk & Payments**: Fraud indicators, failure rates, and payment method health (Mobile Money, Cards).
        3. **Capital & Financing**: Cash flow analysis, loan eligibility, and ROI on potential financing.
        
        Provide concise, actionable recommendations suitable for the Zambian market.
        Structure your response as JSON with keys: revenue_analysis, risk_analysis, growth_opportunities.
        """
        
        user_prompt = f"""
        Analyze these business metrics and provide insights:
        
        {metrics_context}
        
        Please provide specific, actionable recommendations based on this data.
        Focus on immediate actions the business owner can take to improve performance.
        """
        
        try:
            response = await self._make_ollama_request(user_prompt, system_prompt)
            
            # Parse AI response
            ai_text = response.get("response", "")
            
            # Try to extract JSON from response
            try:
                # Look for JSON in the response
                start_idx = ai_text.find('{')
                end_idx = ai_text.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = ai_text[start_idx:end_idx]
                    insights = json.loads(json_str)
                else:
                    # Fallback: create structured response from text
                    insights = self._parse_insights_from_text(ai_text)
            except json.JSONDecodeError:
                insights = self._parse_insights_from_text(ai_text)
            
            logger.info("Generated business insights successfully")
            return insights
            
        except Exception as e:
            logger.error(f"Error generating business insights: {str(e)}")
            return {
                "revenue_analysis": "Unable to analyze revenue data at this time.",
                "risk_analysis": "Risk assessment temporarily unavailable.",
                "growth_opportunities": "Growth analysis will be available shortly."
            }
    
    def _json_default(self, obj: Any) -> Any:
        """Make complex types JSON serializable for prompt context."""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, Decimal):
            try:
                return float(obj)
            except Exception:
                return str(obj)
        # Fallback to string representation
        return str(obj)

    def _parse_insights_from_text(self, text: str) -> Dict[str, str]:
        """Parse insights from unstructured AI text response"""
        
        # Simple parsing logic - in production, this would be more sophisticated
        sections = text.split('\n\n')
        
        insights = {
            "revenue_analysis": "",
            "risk_analysis": "",
            "growth_opportunities": ""
        }
        
        current_section = None
        for section in sections:
            section = section.strip()
            if not section:
                continue
                
            # Identify section type
            if any(word in section.lower() for word in ['revenue', 'sales', 'income']):
                current_section = "revenue_analysis"
            elif any(word in section.lower() for word in ['risk', 'concern', 'issue']):
                current_section = "risk_analysis"
            elif any(word in section.lower() for word in ['growth', 'opportunity', 'improve']):
                current_section = "growth_opportunities"
            
            if current_section and section:
                if insights[current_section]:
                    insights[current_section] += " " + section
                else:
                    insights[current_section] = section
        
        # Ensure all sections have content
        for key in insights:
            if not insights[key]:
                insights[key] = "Analysis pending - please check back shortly."
        
        return insights
    
    async def generate_financing_recommendations(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate financing recommendations based on business data"""
        
        system_prompt = """
        You are a business financing expert specializing in SMB lending and alternative financing in Zambia.
        Analyze business data to recommend appropriate financing options available in the region.
        Consider factors like revenue (ZMW), cash flow, growth trends, and risk profile.
        
        Recommend specific financing products with amounts (in ZMW), terms, and reasoning.
        Structure response as JSON with: recommendations (array), risk_assessment, eligibility_score.
        """
        
        business_summary = f"""
        Business Profile:
        - Monthly Revenue: ZMW {business_data.get('monthly_revenue', 0):,.2f}
        - Growth Rate: {business_data.get('growth_rate', 0):.1f}%
        - Time in Business: {business_data.get('months_in_business', 0)} months
        - Risk Level: {business_data.get('risk_level', 'unknown')}
        - Industry: {business_data.get('industry', 'retail')}
        - Cash Flow: {business_data.get('cash_flow_status', 'stable')}
        """
        
        try:
            response = await self._make_ollama_request(business_summary, system_prompt)
            ai_text = response.get("response", "")
            
            # Parse financing recommendations
            try:
                start_idx = ai_text.find('{')
                end_idx = ai_text.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = ai_text[start_idx:end_idx]
                    recommendations = json.loads(json_str)
                else:
                    recommendations = self._create_default_financing_recommendations(business_data)
            except json.JSONDecodeError:
                recommendations = self._create_default_financing_recommendations(business_data)
            
            logger.info("Generated financing recommendations successfully")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating financing recommendations: {str(e)}")
            return self._create_default_financing_recommendations(business_data)
    
    def _create_default_financing_recommendations(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create default financing recommendations when AI fails"""
        
        monthly_revenue = business_data.get('monthly_revenue', 0)
        risk_level = business_data.get('risk_level', 'medium')
        
        recommendations = []
        
        # Working capital loan
        if monthly_revenue > 5000:
            working_capital_amount = min(monthly_revenue * 6, 100000)
            recommendations.append({
                "product_type": "working_capital_loan",
                "lender": "Zanaco SME Loans",
                "amount": working_capital_amount,
                "interest_rate": 22.5 if risk_level == "low" else 28.5,
                "term_months": 12,
                "approval_probability": 0.75 if risk_level == "low" else 0.60,
                "description": "Short-term working capital to manage cash flow and inventory"
            })
        
        # Line of credit
        if monthly_revenue > 10000:
            credit_limit = min(monthly_revenue * 3, 50000)
            recommendations.append({
                "product_type": "line_of_credit",
                "lender": "Airtel Money Merchant Boost",
                "amount": credit_limit,
                "interest_rate": 18.5 if risk_level == "low" else 24.5,
                "term_months": 6,
                "approval_probability": 0.70,
                "description": "Flexible credit line for ongoing business expenses"
            })
        
        return {
            "recommendations": recommendations,
            "risk_assessment": f"Business shows {risk_level} risk profile based on current metrics",
            "eligibility_score": 75 if risk_level == "low" else 60
        }
    
    async def chat_with_agent(self, user_message: str, context: Dict[str, Any] = None) -> Dict[str, str]:
        """Handle conversational chat with the AI agent"""
        
        system_prompt = """
        You are an expert AI financial consultant for SMB retailers in Zambia, specializing in embedded finance, lending, and payment optimization.
        You have access to the user's complete business context, including:
        1. Transaction History & Revenue Metrics (ZMW)
        2. Financing Offers (Active & Past)
        3. Loan Applications & Status
        4. Business Performance & Risk Indicators
        5. Credit Score (Internal Platform Score)
        
        YOUR ROLE:
        - Provide holistic financial advice connecting revenue trends with financing needs in the Zambian context.
        - Analyze loan offers and help the user understand terms, interest rates, and ROI.
        - Recommend payment method optimizations (e.g., Airtel Money, MTN Mobile Money, Visa/Mastercard).
        - Identify opportunities for growth through capital injection (loans/credits) from local lenders (e.g., Zanaco, Stanbic, AB Bank).
        
        CRITICAL INSTRUCTIONS FOR DATA ANALYSIS:
        - **Financing**: Always check 'financing' data. If the user has active offers, highlight them when relevant to cash flow or growth discussions.
        - **Loans**: If the user asks about past loans, check 'applications' history. Explain status and reasons if available.
        - **Payments**: Analyze 'payment_failure_rate' and 'refund_rate'. Suggest specific improvements (e.g., "Enable 3D Secure" or "Add Digital Wallets") if rates are high.
        - **Comprehensive Metrics**: When asked about "total" or "all-time" stats, use the full dataset provided, not just recent 30 days.
        - **Currency**: Always use ZMW (Zambian Kwacha) for monetary values.
        - **Credit Score**: Use the provided 'Credit Score' from the context. This is an internal platform score, NOT from a credit bureau. Explain it based on the user's transaction history and business metrics.
        
        TONE & STYLE:
        - Professional, encouraging, and highly actionable.
        - Proactive: Don't just answer the question; suggest the next best financial move.
        - Data-Driven: Cite specific numbers from the context to back up your advice.
        """
        
        # Add context if provided
        context_str = ""
        if context:
            # Extract data context if available
            data_context = context.get("data", {})
            if data_context:
                # Highlight the data scope in the context
                date_range_info = data_context.get("date_range", {})
                note = data_context.get("note", "")
                
                # Ensure date_range_info is properly serialized (handle any datetime objects)
                # Convert any datetime objects to ISO format strings
                if date_range_info:
                    serialized_date_range = {}
                    for key, value in date_range_info.items():
                        if isinstance(value, datetime):
                            serialized_date_range[key] = value.isoformat()
                        else:
                            serialized_date_range[key] = value
                    date_range_str = json.dumps(serialized_date_range, indent=2, default=self._json_default)
                else:
                    date_range_str = "{}"
                
                # Financing Summary
                financing_data = data_context.get('financing', {})
                active_offers = len(financing_data.get('active_offers', []))
                applications = len(financing_data.get('applications', []))
                credit_score = data_context.get('credit_score', 'N/A')
                
                context_str = f"""
Business Context: {json.dumps(context, indent=2, default=self._json_default)}

DATA SCOPE INFORMATION:
- Date Range: {date_range_str}
- Note: {note}
- Total Transactions Available: {data_context.get('transaction_count', 'N/A')}
- Total Revenue (from all data): ZMW {data_context.get('total_revenue', 0):,.2f}
- Credit Score: {credit_score}
- Financing: {active_offers} active offers, {applications} past applications.

IMPORTANT: Analyze ALL available data. Use the financing data to suggest capital opportunities.
"""
            else:
                context_str = f"\nBusiness Context: {json.dumps(context, indent=2, default=self._json_default)}\n"
        
        full_prompt = f"{context_str}User Question: {user_message}"
        
        try:
            response = await self._make_ollama_request(full_prompt, system_prompt)
            ai_response = response.get("response", "I'm having trouble processing your request right now.")
            
            return {
                "response": ai_response,
                "timestamp": datetime.utcnow().isoformat(),
                "context_used": bool(context)
            }
            
        except Exception as e:
            logger.error(f"Error in chat interaction: {str(e)}")
            return {
                "response": "I'm experiencing some technical difficulties. Please try again in a moment.",
                "timestamp": datetime.utcnow().isoformat(),
                "context_used": False
            }
    
    async def analyze_transaction_patterns(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze transaction patterns for fraud detection and insights"""
        
        system_prompt = """
        You are a financial fraud detection and transaction analysis expert.
        Analyze transaction patterns to identify:
        1. Potential fraud indicators
        2. Seasonal trends
        3. Customer behavior patterns
        4. Revenue optimization opportunities
        
        Provide analysis as JSON with: fraud_score (0-100), patterns_detected, recommendations.
        """
        
        # Summarize transaction data for AI
        if not transactions:
            return {"fraud_score": 0, "patterns_detected": [], "recommendations": []}
        
        transaction_summary = {
            "total_transactions": len(transactions),
            "total_amount": sum(t.get("amount", 0) for t in transactions),
            "avg_amount": sum(t.get("amount", 0) for t in transactions) / len(transactions),
            "failed_count": sum(1 for t in transactions if t.get("status") == "failed"),
            "refund_count": sum(1 for t in transactions if t.get("transaction_type") == "refund"),
            "time_span": "last_30_days"
        }
        
        prompt = f"Analyze these transaction patterns: {json.dumps(transaction_summary, indent=2, default=self._json_default)}"
        
        try:
            response = await self._make_ollama_request(prompt, system_prompt)
            ai_text = response.get("response", "")
            
            # Parse analysis results
            try:
                start_idx = ai_text.find('{')
                end_idx = ai_text.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    analysis = json.loads(ai_text[start_idx:end_idx])
                else:
                    analysis = self._create_default_transaction_analysis(transaction_summary)
            except json.JSONDecodeError:
                analysis = self._create_default_transaction_analysis(transaction_summary)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing transaction patterns: {str(e)}")
            return self._create_default_transaction_analysis(transaction_summary)
    
    def _create_default_transaction_analysis(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Create default transaction analysis"""
        
        total_transactions = summary.get("total_transactions", 0)
        failed_count = summary.get("failed_count", 0)
        refund_count = summary.get("refund_count", 0)
        
        # Calculate basic fraud score
        fraud_score = 0
        if total_transactions > 0:
            failure_rate = failed_count / total_transactions
            refund_rate = refund_count / total_transactions
            fraud_score = min(100, (failure_rate * 30) + (refund_rate * 40))
        
        patterns = []
        recommendations = []
        
        if failure_rate > 0.05:  # >5% failure rate
            patterns.append("High transaction failure rate detected")
            recommendations.append("Review payment gateway settings and customer payment methods")
        
        if refund_rate > 0.02:  # >2% refund rate
            patterns.append("Elevated refund activity")
            recommendations.append("Analyze refund reasons and improve product/service quality")
        
        return {
            "fraud_score": fraud_score,
            "patterns_detected": patterns,
            "recommendations": recommendations,
            "analysis_confidence": 0.75
        }