"""
Payment Schemas Module

This module contains all Pydantic schemas for payment-related operations
in the AI-embedded finance platform. It handles validation for transactions,
payment methods, refunds, subscriptions, and third-party integrations.

Author: AI Finance Platform Team
Created: 2025-06-14
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any, Union
from uuid import UUID

from pydantic import BaseModel, Field, validator, model_validator
from pydantic import EmailStr, PositiveFloat, NonNegativeFloat


class TransactionFilter(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None

class PaymentStatus(str, Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class PaymentMethod(str, Enum):
    """Payment method types"""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    DIGITAL_WALLET = "digital_wallet"
    CRYPTOCURRENCY = "cryptocurrency"
    BUY_NOW_PAY_LATER = "bnpl"
    ACH = "ach"
    WIRE_TRANSFER = "wire_transfer"


class TransactionType(str, Enum):
    """Transaction type enumeration"""
    PAYMENT = "payment"
    SALE = "sale"
    REFUND = "refund"
    PARTIAL_REFUND = "partial_refund"
    CHARGEBACK = "chargeback"
    AUTHORIZATION = "authorization"
    CAPTURE = "capture"
    VOID = "void"
    SUBSCRIPTION = "subscription"


class Currency(str, Enum):
    """Supported currencies"""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CAD = "CAD"
    AUD = "AUD"
    JPY = "JPY"
    ZMW = "ZMW"


class IntegrationProvider(str, Enum):
    """Third-party integration providers"""
    STRIPE = "stripe"
    SHOPIFY = "shopify"
    QUICKBOOKS = "quickbooks"
    SQUARE = "square"
    PAYPAL = "paypal"
    ADYEN = "adyen"


# Base Schemas
class PaymentBase(BaseModel):
    """Base payment schema with common fields"""
    amount: PositiveFloat = Field(..., description="Payment amount")
    currency: Currency = Field(default=Currency.USD, description="Payment currency")
    description: Optional[str] = Field(None, max_length=500, description="Payment description")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        use_enum_values = True


class CustomerInfoBase(BaseModel):
    """Base customer information schema"""
    customer_id: Optional[str] = Field(None, description="External customer ID")
    email: Optional[EmailStr] = Field(None, description="Customer email")
    name: Optional[str] = Field(None, max_length=100, description="Customer name")
    phone: Optional[str] = Field(None, max_length=20, description="Customer phone number")


class AddressBase(BaseModel):
    """Base address schema"""
    line1: str = Field(..., max_length=100, description="Address line 1")
    line2: Optional[str] = Field(None, max_length=100, description="Address line 2")
    city: str = Field(..., max_length=50, description="City")
    state: str = Field(..., max_length=50, description="State/Province")
    postal_code: str = Field(..., max_length=20, description="Postal/ZIP code")
    country: str = Field(..., max_length=2, description="ISO country code")


# Request Schemas
class PaymentMethodCreate(BaseModel):
    """Schema for creating a new payment method"""
    type: PaymentMethod = Field(..., description="Payment method type")
    card_number: Optional[str] = Field(None, min_length=13, max_length=19, description="Card number (encrypted)")
    card_holder_name: Optional[str] = Field(None, max_length=100, description="Cardholder name")
    expiry_month: Optional[int] = Field(None, ge=1, le=12, description="Card expiry month")
    expiry_year: Optional[int] = Field(None, ge=2024, le=2050, description="Card expiry year")
    cvv: Optional[str] = Field(None, min_length=3, max_length=4, description="CVV code")
    billing_address: Optional[AddressBase] = Field(None, description="Billing address")
    bank_account_number: Optional[str] = Field(None, description="Bank account number")
    routing_number: Optional[str] = Field(None, description="Bank routing number")
    wallet_provider: Optional[str] = Field(None, description="Digital wallet provider")
    wallet_id: Optional[str] = Field(None, description="Wallet identifier")
    is_default: bool = Field(default=False, description="Set as default payment method")

    @validator('card_number')
    def validate_card_number(cls, v, values):
        if values.get('type') in [PaymentMethod.CREDIT_CARD, PaymentMethod.DEBIT_CARD] and not v:
            raise ValueError('Card number is required for card payments')
        return v

    @validator('bank_account_number')
    def validate_bank_account(cls, v, values):
        if values.get('type') in [PaymentMethod.BANK_TRANSFER, PaymentMethod.ACH] and not v:
            raise ValueError('Bank account number is required for bank transfers')
        return v


class PaymentCreate(PaymentBase):
    """Schema for creating a new payment"""
    customer_info: CustomerInfoBase = Field(..., description="Customer information")
    payment_method_id: Optional[UUID] = Field(None, description="Stored payment method ID")
    payment_method: Optional[PaymentMethodCreate] = Field(None, description="New payment method details")
    billing_address: Optional[AddressBase] = Field(None, description="Billing address")
    shipping_address: Optional[AddressBase] = Field(None, description="Shipping address")
    order_id: Optional[str] = Field(None, description="Associated order ID")
    invoice_id: Optional[str] = Field(None, description="Associated invoice ID")
    return_url: Optional[str] = Field(None, description="Return URL for redirects")
    webhook_url: Optional[str] = Field(None, description="Webhook notification URL")
    save_payment_method: bool = Field(default=False, description="Save payment method for future use")
    
    @model_validator(mode="after")
    def check_something(cls, values):
        # ...validation logic...
        return values


class PaymentUpdate(BaseModel):
    """Schema for updating payment details"""
    status: Optional[PaymentStatus] = Field(None, description="Payment status")
    description: Optional[str] = Field(None, max_length=500, description="Payment description")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class RefundCreate(BaseModel):
    """Schema for creating a refund"""
    payment_id: UUID = Field(..., description="Original payment ID")
    amount: Optional[PositiveFloat] = Field(None, description="Refund amount (full refund if not specified)")
    reason: Optional[str] = Field(None, max_length=200, description="Refund reason")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class TransactionSearch(BaseModel):
    """Schema for transaction search and filtering"""
    customer_id: Optional[str] = Field(None, description="Filter by customer ID")
    status: Optional[PaymentStatus] = Field(None, description="Filter by payment status")
    payment_method: Optional[PaymentMethod] = Field(None, description="Filter by payment method")
    transaction_type: Optional[TransactionType] = Field(None, description="Filter by transaction type")
    date_from: Optional[date] = Field(None, description="Filter from date")
    date_to: Optional[date] = Field(None, description="Filter to date")
    amount_min: Optional[NonNegativeFloat] = Field(None, description="Minimum amount filter")
    amount_max: Optional[NonNegativeFloat] = Field(None, description="Maximum amount filter")
    currency: Optional[Currency] = Field(None, description="Filter by currency")
    order_id: Optional[str] = Field(None, description="Filter by order ID")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="Sort order")


class TransactionCreate(BaseModel):
    """Schema for creating a new transaction manually"""
    amount: PositiveFloat = Field(..., description="Transaction amount")
    currency: Currency = Field(default=Currency.USD, description="Transaction currency")
    status: PaymentStatus = Field(default=PaymentStatus.COMPLETED, description="Transaction status")
    transaction_type: TransactionType = Field(default=TransactionType.PAYMENT, description="Transaction type")
    description: Optional[str] = Field(None, max_length=500, description="Transaction description")
    
    # External references
    stripe_payment_id: Optional[str] = Field(None, description="Stripe Payment ID")
    shopify_order_id: Optional[str] = Field(None, description="Shopify Order ID")
    quickbooks_ref: Optional[str] = Field(None, description="QuickBooks Reference")
    
    # Metadata
    transaction_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    # Optional override for creation date (useful for backfilling)
    date: Optional[datetime] = Field(None, description="Transaction date")


# Response Schemas
class PaymentMethodResponse(BaseModel):
    """Response schema for payment method"""
    id: UUID = Field(..., description="Payment method ID")
    user_id: UUID = Field(..., description="User ID")
    type: PaymentMethod = Field(..., description="Payment method type")
    last_four: Optional[str] = Field(None, description="Last four digits of card/account")
    brand: Optional[str] = Field(None, description="Card brand or bank name")
    expiry_month: Optional[int] = Field(None, description="Card expiry month")
    expiry_year: Optional[int] = Field(None, description="Card expiry year")
    is_default: bool = Field(..., description="Is default payment method")
    is_active: bool = Field(..., description="Is payment method active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class PaymentResponse(PaymentBase):
    """Response schema for payment"""
    id: UUID = Field(..., description="Payment ID")
    user_id: UUID = Field(..., description="User ID")
    status: PaymentStatus = Field(..., description="Payment status")
    transaction_type: TransactionType = Field(..., description="Transaction type")
    payment_method_id: Optional[UUID] = Field(None, description="Payment method ID")
    gateway_transaction_id: Optional[str] = Field(None, description="Gateway transaction ID")
    gateway_reference: Optional[str] = Field(None, description="Gateway reference")
    processing_fee: Optional[Decimal] = Field(None, description="Processing fee")
    net_amount: Optional[Decimal] = Field(None, description="Net amount after fees")
    refunded_amount: Optional[Decimal] = Field(None, description="Total refunded amount")
    order_id: Optional[str] = Field(None, description="Associated order ID")
    invoice_id: Optional[str] = Field(None, description="Associated invoice ID")
    failure_reason: Optional[str] = Field(None, description="Failure reason if failed")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    processed_at: Optional[datetime] = Field(None, description="Processing timestamp")
    
    class Config:
        from_attributes = True


class RefundResponse(BaseModel):
    """Response schema for refund"""
    id: UUID = Field(..., description="Refund ID")
    payment_id: UUID = Field(..., description="Original payment ID")
    amount: Decimal = Field(..., description="Refund amount")
    status: PaymentStatus = Field(..., description="Refund status")
    reason: Optional[str] = Field(None, description="Refund reason")
    gateway_refund_id: Optional[str] = Field(None, description="Gateway refund ID")
    processing_fee: Optional[Decimal] = Field(None, description="Refund processing fee")
    created_at: datetime = Field(..., description="Creation timestamp")
    processed_at: Optional[datetime] = Field(None, description="Processing timestamp")
    
    class Config:
        from_attributes = True


class TransactionResponse(BaseModel):
    """Response schema for transaction details"""
    id: UUID = Field(..., description="Transaction ID")
    user_id: UUID = Field(..., description="User ID")
    transaction_type: TransactionType = Field(..., description="Transaction type")
    status: str = Field(..., description="Transaction status")
    amount: Decimal = Field(..., description="Transaction amount")
    currency: Currency = Field(..., description="Transaction currency")
    description: Optional[str] = Field(None, description="Transaction description")
    stripe_payment_id: Optional[str] = Field(None, description="Stripe Payment ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True


class PaymentSummary(BaseModel):
    """Payment summary statistics"""
    total_payments: int = Field(..., description="Total number of payments")
    total_amount: Decimal = Field(..., description="Total payment amount")
    successful_payments: int = Field(..., description="Number of successful payments")
    failed_payments: int = Field(..., description="Number of failed payments")
    refunded_payments: int = Field(..., description="Number of refunded payments")
    average_payment_amount: Decimal = Field(..., description="Average payment amount")
    total_fees: Decimal = Field(..., description="Total processing fees")
    net_revenue: Decimal = Field(..., description="Net revenue after fees")


class PaginatedPayments(BaseModel):
    """Paginated payment response"""
    items: List[PaymentResponse] = Field(..., description="Payment items")
    total: int = Field(..., description="Total number of payments")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")


class PaginatedTransactions(BaseModel):
    """Paginated transaction response"""
    items: List[TransactionResponse] = Field(..., description="Transaction items")
    total: int = Field(..., description="Total number of transactions")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")


# Integration Schemas
class StripeWebhookPayload(BaseModel):
    """Stripe webhook payload schema"""
    id: str = Field(..., description="Event ID")
    object: str = Field(..., description="Object type")
    api_version: Optional[str] = Field(None, description="API version")
    created: int = Field(..., description="Creation timestamp")
    data: Dict[str, Any] = Field(..., description="Event data")
    livemode: bool = Field(..., description="Live mode flag")
    pending_webhooks: int = Field(..., description="Pending webhooks count")
    request: Optional[Dict[str, Any]] = Field(None, description="Request information")
    type: str = Field(..., description="Event type")


class ShopifyWebhookPayload(BaseModel):
    """Shopify webhook payload schema"""
    id: int = Field(..., description="Order ID")
    order_number: Optional[str] = Field(None, description="Order number")
    total_price: str = Field(..., description="Total price")
    currency: str = Field(..., description="Currency")
    financial_status: str = Field(..., description="Financial status")
    gateway: Optional[str] = Field(None, description="Payment gateway")
    customer: Optional[Dict[str, Any]] = Field(None, description="Customer information")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Update timestamp")


class QuickBooksPayment(BaseModel):
    """QuickBooks payment schema"""
    Id: str = Field(..., description="Payment ID")
    TotalAmt: float = Field(..., description="Total amount")
    CustomerRef: Dict[str, Any] = Field(..., description="Customer reference")
    TxnDate: str = Field(..., description="Transaction date")
    PaymentMethodRef: Optional[Dict[str, Any]] = Field(None, description="Payment method reference")
    Line: List[Dict[str, Any]] = Field(..., description="Payment line items")
    MetaData: Dict[str, Any] = Field(..., description="Metadata")


# Analytics and AI Schemas
class PaymentAnalyticsRequest(BaseModel):
    """Request schema for payment analytics"""
    date_range: str = Field(..., pattern="^(7d|30d|90d|1y|custom)$", description="Date range")
    start_date: Optional[date] = Field(None, description="Custom start date")
    end_date: Optional[date] = Field(None, description="Custom end date")
    group_by: str = Field(default="day", pattern="^(hour|day|week|month)$", description="Grouping period")
    metrics: List[str] = Field(default=["revenue", "volume", "fees"], description="Metrics to include")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional filters")


class PaymentInsightResponse(BaseModel):
    """AI-generated payment insights response"""
    insight_type: str = Field(..., description="Type of insight")
    title: str = Field(..., description="Insight title")
    description: str = Field(..., description="Detailed description")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    recommendations: List[str] = Field(..., description="Actionable recommendations")
    data_points: Dict[str, Any] = Field(..., description="Supporting data points")
    generated_at: datetime = Field(..., description="Generation timestamp")


class FraudDetectionResult(BaseModel):
    """Fraud detection result schema"""
    payment_id: UUID = Field(..., description="Payment ID")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Risk score")
    risk_level: str = Field(..., pattern="^(low|medium|high|critical)$", description="Risk level")
    factors: List[str] = Field(..., description="Risk factors identified")
    recommendations: List[str] = Field(..., description="Recommended actions")
    requires_manual_review: bool = Field(..., description="Manual review required flag")
    evaluated_at: datetime = Field(..., description="Evaluation timestamp")


# Webhook and Event Schemas
class PaymentEvent(BaseModel):
    """Payment event schema for internal processing"""
    event_id: UUID = Field(..., description="Event ID")
    event_type: str = Field(..., description="Event type")
    payment_id: UUID = Field(..., description="Payment ID")
    user_id: UUID = Field(..., description="User ID")
    data: Dict[str, Any] = Field(..., description="Event data")
    created_at: datetime = Field(..., description="Event timestamp")
    processed: bool = Field(default=False, description="Processing status")


class WebhookSubscription(BaseModel):
    """Webhook subscription schema"""
    url: str = Field(..., description="Webhook URL")
    events: List[str] = Field(..., description="Subscribed events")
    secret: Optional[str] = Field(None, description="Webhook secret")
    active: bool = Field(default=True, description="Subscription status")
    retry_config: Optional[Dict[str, Any]] = Field(None, description="Retry configuration")


# Error Schemas
class PaymentError(BaseModel):
    """Payment error response schema"""
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Error message")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    payment_id: Optional[UUID] = Field(None, description="Associated payment ID")
    timestamp: datetime = Field(..., description="Error timestamp")
    suggested_action: Optional[str] = Field(None, description="Suggested remediation action")
