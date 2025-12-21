"""
Financing Schemas Module

This module contains Pydantic schemas for financing-related operations including
loan applications, credit assessments, financing offers, and payment plans.
All schemas include comprehensive validation and support for AI-driven insights.

Author: AI Finance Platform Team
Version: 1.0.0
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any, Union
from uuid import UUID

from pydantic import BaseModel, Field, validator, model_validator
from pydantic import EmailStr, constr, confloat, conint


class FinancingStatus(str, Enum):
    """Enumeration for financing application status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    UNDER_REVIEW = "under_review"
    REQUIRES_DOCUMENTATION = "requires_documentation"
    ACTIVE = "active"
    COMPLETED = "completed"
    DEFAULTED = "defaulted"
    CANCELLED = "cancelled"


class FinancingType(str, Enum):
    """Enumeration for types of financing products"""
    TERM_LOAN = "term_loan"
    LINE_OF_CREDIT = "line_of_credit"
    MERCHANT_CASH_ADVANCE = "merchant_cash_advance"
    INVOICE_FINANCING = "invoice_financing"
    EQUIPMENT_FINANCING = "equipment_financing"
    WORKING_CAPITAL = "working_capital"
    SEASONAL_FINANCING = "seasonal_financing"
    BRIDGE_LOAN = "bridge_loan"


class RiskLevel(str, Enum):
    """Risk assessment levels for financing applications"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class PaymentFrequency(str, Enum):
    """Payment frequency options for financing"""
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


# Base schemas for common fields
class FinancingBase(BaseModel):
    """Base schema with common financing fields"""
    financing_type: FinancingType
    # FIX APPLIED HERE: Correctly nesting constr/confloat/conint within Field
    requested_amount: float = Field(
        ...,
        description="Requested financing amount in USD",
        gt=0, le=10000000 # Constraints moved into Field for cleaner syntax
    )
    purpose: str = Field(
        ...,
        description="Purpose of financing",
        min_length=10, max_length=500 # Constraints moved into Field
    )
    business_description: Optional[str] = Field(
        None,
        description="Brief business description",
        max_length=1000 # Constraint moved into Field
    )


class BusinessInfo(BaseModel):
    """Business information schema for financing applications"""
    business_name: str = constr(min_length=2, max_length=200) # This pattern is fine without Field
    legal_entity_type: str = constr(max_length=50)
    tax_id: str = constr(pattern=r'^\d{2}-\d{7}$|^\d{9}$')  # EIN format
    years_in_business: int = conint(ge=0, le=100)
    industry: str = constr(max_length=100)
    annual_revenue: float = confloat(ge=0)
    monthly_revenue: float = confloat(ge=0)
    employees_count: int = conint(ge=1, le=10000)
    business_address: Dict[str, str]
    business_phone: str = constr(pattern=r'^\+?1?[- ]?\(?[0-9]{3}\)?[- ]?[0-9]{3}[- ]?[0-9]{4}$')
    website: Optional[str] = constr(pattern=r'^https?://')

    @validator('annual_revenue', 'monthly_revenue')
    def validate_revenue_consistency(cls, v, values):
        if 'monthly_revenue' in values and 'annual_revenue' in values:
            if values['monthly_revenue'] * 12 > values['annual_revenue'] * 1.5:
                raise ValueError('Monthly revenue seems inconsistent with annual revenue')
        return v


class PersonalGuarantee(BaseModel):
    """Personal guarantee information schema"""
    guarantor_name: str = constr(min_length=2, max_length=100)
    ssn: str = constr(pattern=r'^\d{3}-\d{2}-\d{4}$|^\d{9}$')
    date_of_birth: date
    ownership_percentage: float = confloat(ge=0, le=100)
    personal_credit_score: Optional[int] = conint(ge=300, le=850)
    annual_income: float = confloat(ge=0)
    address: Dict[str, str]
    phone: str = constr(pattern=r'^\+?1?[- ]?\(?[0-9]{3}\)?[- ]?[0-9]{3}[- ]?[0-9]{4}$')
    email: EmailStr

    @validator('date_of_birth')
    def validate_age(cls, v):
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age < 18:
            raise ValueError('Guarantor must be at least 18 years old')
        return v


class FinancialDocuments(BaseModel):
    """Schema for required financial documents"""
    # FIX APPLIED HERE: Corrected syntax for default values
    bank_statements_months: int = Field(12, ge=3, le=24)
    tax_returns_years: int = Field(2, ge=1, le=3)
    profit_loss_statement: bool = True
    balance_sheet: bool = True
    cash_flow_statement: bool = False
    accounts_receivable_aging: bool = False
    accounts_payable_aging: bool = False
    additional_documents: Optional[List[str]] = []


# Request schemas
class FinancingApplicationCreate(FinancingBase):
    """Schema for creating a new financing application"""
    business_info: BusinessInfo
    personal_guarantees: List[PersonalGuarantee] = Field(
        ...,
        min_items=1,
        description="At least one personal guarantee required"
    )
    collateral_description: Optional[str] = constr(max_length=1000)
    # FIX APPLIED HERE: Corrected syntax for default values
    requested_terms_months: int = Field(
        ...,
        description="Requested loan term in months",
        ge=1, le=120
    )
    preferred_payment_frequency: PaymentFrequency = PaymentFrequency.MONTHLY
    has_existing_debt: bool = False
    existing_debt_amount: Optional[float] = confloat(ge=0)
    bank_account_info: Dict[str, str] = Field(
        ...,
        description="Primary business bank account information"
    )

    @model_validator(mode='after')
    def validate_existing_debt(cls, values):
        has_debt = values.get('has_existing_debt', False)
        debt_amount = values.get('existing_debt_amount')

        if has_debt and (debt_amount is None or debt_amount <= 0):
            raise ValueError('Existing debt amount must be provided if has_existing_debt is True')
        elif not has_debt and debt_amount is not None and debt_amount > 0:
            raise ValueError('Existing debt amount should not be provided if has_existing_debt is False')

        return values


class FinancingApplicationUpdate(BaseModel):
    """Schema for updating financing application"""
    status: Optional[FinancingStatus]
    purpose: Optional[str] = constr(min_length=10, max_length=500)
    requested_amount: Optional[float] = confloat(gt=0, le=10000000)
    requested_terms_months: Optional[int] = conint(ge=1, le=120)
    collateral_description: Optional[str] = constr(max_length=1000)
    notes: Optional[str] = constr(max_length=2000)


# AI-driven assessment schemas
class CreditAssessment(BaseModel):
    """AI-generated credit assessment schema"""
    credit_score: int = conint(ge=300, le=850)
    risk_level: RiskLevel
    assessment_date: datetime
    factors_considered: List[str] = Field(
        ...,
        description="List of factors considered in assessment"
    )
    positive_factors: List[str] = []
    negative_factors: List[str] = []
    recommendations: List[str] = []
    # FIX APPLIED HERE: Corrected syntax
    confidence_score: float = Field(
        ...,
        description="AI confidence in assessment (0-1)",
        ge=0, le=1
    )
    model_version: str = Field(
        ...,
        description="Version of AI model used for assessment"
    )


class FinancingOffer(BaseModel):
    """Schema for financing offer generated by AI"""
    offer_id: UUID
    financing_type: FinancingType
    approved_amount: float = confloat(gt=0)
    # FIX APPLIED HERE: Corrected syntax
    interest_rate: float = Field(
        ...,
        description="Annual interest rate as percentage",
        ge=0, le=50
    )
    term_months: int = conint(ge=1, le=120)
    payment_frequency: PaymentFrequency
    monthly_payment: float = confloat(gt=0)
    total_cost: float = confloat(gt=0)
    # FIX APPLIED HERE: Corrected syntax
    origination_fee: float = Field(0, ge=0)
    processing_fee: float = Field(0, ge=0)
    early_payoff_penalty: Optional[float] = confloat(ge=0)
    collateral_required: bool = False
    personal_guarantee_required: bool = True
    conditions: List[str] = []
    valid_until: datetime = Field(
        ...,
        description="Offer expiration date"
    )
    ai_reasoning: Optional[Dict[str, Any]] = Field(
        None,
        description="AI reasoning behind offer terms"
    )


class PaymentSchedule(BaseModel):
    """Payment schedule schema"""
    payment_number: int = conint(ge=1)
    due_date: date
    principal_amount: float = confloat(ge=0)
    interest_amount: float = confloat(ge=0)
    total_payment: float = confloat(gt=0)
    remaining_balance: float = confloat(ge=0)


class FinancingContract(BaseModel):
    """Finalized financing contract schema"""
    contract_id: UUID
    application_id: UUID
    offer_id: UUID
    contract_date: datetime
    funding_date: Optional[date]
    funded_amount: float = confloat(gt=0)
    terms: FinancingOffer
    payment_schedule: List[PaymentSchedule]
    contract_status: FinancingStatus
    signed_by_borrower: bool = False
    signed_by_lender: bool = False
    esignature_ids: Optional[Dict[str, str]] = None


# Response schemas
class FinancingApplicationResponse(FinancingBase):
    """Response schema for financing application"""
    id: UUID
    user_id: UUID
    application_number: str
    status: FinancingStatus
    created_at: datetime
    updated_at: datetime
    business_info: BusinessInfo
    personal_guarantees: List[PersonalGuarantee]
    credit_assessment: Optional[CreditAssessment]
    offers: List[FinancingOffer] = []
    contract: Optional[FinancingContract]
    notes: Optional[str]

    class Config:
        alias_generator = True


class FinancingOfferResponse(BaseModel):
    """Response schema for financing offer"""
    id: UUID
    application_id: UUID
    offer: FinancingOffer
    created_at: datetime
    expires_at: datetime
    is_accepted: bool = False
    accepted_at: Optional[datetime]

    class Config:
        alias_generator = True


class FinancingDashboard(BaseModel):
    """Dashboard summary schema for financing overview"""
    total_applications: int
    pending_applications: int
    approved_applications: int
    active_loans: int
    total_funded_amount: Decimal
    total_outstanding_balance: Decimal
    average_approval_time_days: float
    default_rate_percentage: float
    recent_applications: List[FinancingApplicationResponse] = Field(
        max_items=10
    )
    ai_insights: Dict[str, Any] = Field(
        default_factory=dict,
        description="AI-generated insights about financing portfolio"
    )


# AI-specific schemas
class FinancingInsightRequest(BaseModel):
    """Schema for requesting AI insights on financing data"""
    user_id: UUID
    analysis_type: str = Field(
        ...,
        pattern=r'^(risk_assessment|market_trends|recommendation|portfolio_analysis)$'
    )
    time_period_days: int = Field(30, ge=1, le=365) # FIX APPLIED HERE: Corrected syntax
    include_predictions: bool = True
    specific_questions: Optional[List[str]] = []


class FinancingInsightResponse(BaseModel):
    """AI-generated financing insights response"""
    insight_id: UUID
    user_id: UUID
    generated_at: datetime
    analysis_type: str
    summary: str = Field(
        ...,
        description="Executive summary of insights"
    )
    key_findings: List[str]
    recommendations: List[str]
    risk_factors: List[str]
    opportunities: List[str]
    data_points: Dict[str, Any] = Field(
        default_factory=dict,
        description="Supporting data and metrics"
    )
    confidence_level: float = confloat(ge=0, le=1)
    next_review_date: Optional[date]


class MLModelPrediction(BaseModel):
    """Schema for ML model predictions"""
    prediction_id: UUID
    model_name: str
    model_version: str
    input_features: Dict[str, Any]
    prediction: Union[float, str, Dict[str, Any]]
    confidence_score: float = confloat(ge=0, le=1)
    prediction_date: datetime
    explanation: Optional[Dict[str, Any]] = Field(
        None,
        description="Model explanation/feature importance"
    )


# Bulk operations schemas
class BulkFinancingUpdate(BaseModel):
    """Schema for bulk financing updates"""
    application_ids: List[UUID] = Field(min_items=1, max_items=100)
    update_data: FinancingApplicationUpdate
    reason: str = constr(min_length=10, max_length=500)


class BulkFinancingResponse(BaseModel):
    """Response schema for bulk operations"""
    total_requested: int
    successful_updates: int
    failed_updates: int
    errors: List[Dict[str, str]] = []
    updated_applications: List[UUID] = []


# Export schemas for external integrations
class FinancingExport(BaseModel):
    """Schema for exporting financing data"""
    export_format: str = Field(
        ...,
        pattern=r'^(csv|xlsx|json|pdf)$'
    )
    date_range: Dict[str, date] = Field(
        ...,
        description="Start and end dates for export"
    )
    include_fields: List[str] = []
    filters: Optional[Dict[str, Any]] = {}

    @validator('date_range')
    def validate_date_range(cls, v):
        if 'start_date' not in v or 'end_date' not in v:
            raise ValueError('Both start_date and end_date are required')
        if v['start_date'] > v['end_date']:
            raise ValueError('start_date cannot be after end_date')
        return v


# Webhook schemas for third-party integrations
class FinancingWebhook(BaseModel):
    """Schema for financing-related webhooks"""
    event_type: str = Field(
        ...,
        pattern=r'^(application_created|application_approved|payment_due|payment_received|default_detected)$'
    )
    application_id: UUID
    timestamp: datetime
    data: Dict[str, Any]
    signature: str = Field(
        ...,
        description="Webhook signature for verification"
    )


# Validation helper schemas
class FinancingValidationRules(BaseModel):
    """Schema defining validation rules for financing applications"""
    # FIX APPLIED HERE: Corrected syntax
    min_credit_score: int = Field(600, ge=300, le=850)
    max_debt_to_income_ratio: float = Field(0.5, ge=0, le=10)
    min_years_in_business: int = Field(1, ge=0, le=100)
    min_annual_revenue: float = Field(50000, ge=0)
    max_loan_to_revenue_ratio: float = Field(0.3, ge=0, le=10)
    required_documents: List[str] = [
        "bank_statements",
        "tax_returns",
        "profit_loss_statement"
    ]
    industry_restrictions: List[str] = []
    state_restrictions: List[str] = []


class FinancingMetrics(BaseModel):
    """Comprehensive financing metrics schema"""
    period_start: date
    period_end: date
    applications_submitted: int = 0
    applications_approved: int = 0
    approval_rate: float = confloat(ge=0, le=1)
    average_loan_amount: Decimal = Decimal('0')
    total_funded: Decimal = Decimal('0')
    default_rate: float = confloat(ge=0, le=1)
    average_interest_rate: float = confloat(ge=0, le=100)
    roi: float = confloat(ge=-1, le=10)
    customer_satisfaction: Optional[float] = confloat(ge=0, le=5)
    processing_time_avg_days: float = 0
    ai_accuracy_rate: float = confloat(ge=0, le=1)

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }
        alias_generator = True