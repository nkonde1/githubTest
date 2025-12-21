"""
Data Sync Service for AI-Embedded Finance Platform

This service handles synchronization of financial data from multiple sources:
- Stripe for payment processing
- Shopify for e-commerce transactions
- QuickBooks for accounting data

Features:
- Async data fetching and processing
- Rate limiting and retry mechanisms
- Data validation and transformation
- Background job scheduling
- Error handling and logging
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import uuid

import httpx
import stripe
from redis import asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.database import get_async_session
from app.core.config import settings
from app.models.transaction import Transaction
from app.models.user import User
from app.core.celery_app import celery_app
from app.redis_client import redis_client

logger = logging.getLogger(__name__)

class DataSyncService:
    """Service for syncing payment data from various providers"""
    
    def __init__(self, session: AsyncSession = None):
        self.session = session
        self._redis = None  # Will be initialized on first use
        self._shopify_client = None
        self.rate_limits = {
            DataSource.STRIPE: {"requests_per_second": 100, "burst": 1000},
            DataSource.SHOPIFY: {"requests_per_second": 2, "burst": 40},
            DataSource.QUICKBOOKS: {"requests_per_second": 10, "burst": 100}
        }
        
        # Initialize API clients
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self._setup_http_clients()

    async def _init_redis(self):
        """Initialize Redis connection if not already initialized"""
        if not self._redis:
            try:
                await redis_client.init()
                self._redis = await aioredis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True
                )
                logger.info("Redis connection initialized")
            except Exception as e:
                logger.error(f"Redis initialization failed: {str(e)}")
                raise

    async def sync_payment_data(self, user_id: str, provider: str) -> Dict[str, Any]:
        """Main entry point for payment data synchronization"""
        try:
            if provider.lower() == "shopify":
                # Get user's Shopify credentials
                user = await self.session.get(User, user_id)
                if not user or not user.shopify_access_token or not user.shopify_shop_domain:
                    raise ValueError("Shopify credentials not configured")
                
                return await self.sync_shopify_payments(
                    user_id=user_id,
                    shop_domain=user.shopify_shop_domain,
                    access_token=user.shopify_access_token
                )
            else:
                try:
                    source = DataSource(provider.lower())
                    return await self._sync_source(
                        user_id=int(user_id),
                        source=source
                    )
                except ValueError:
                    raise ValueError(f"Unsupported provider: {provider}")

        except Exception as e:
            logger.error(f"Payment sync failed: {str(e)}", exc_info=True)
            raise

    async def sync_shopify_payments(self, user_id: str, shop_domain: str, access_token: str) -> Dict[str, Any]:
        """Sync payments from Shopify"""
        await self._init_redis()  # Ensure Redis is initialized
        cache_key = f"sync:shopify:{user_id}"
        
        try:
            if self._redis:
                # Check if sync is already running
                exists = await self._redis.exists(cache_key)
                if exists:
                    return {
                        "status": "in_progress",
                        "message": "Sync already in progress"
                    }

                # Set sync status
                await self._redis.set(cache_key, "running", ex=300)  # 5 min timeout
            
            # Your sync logic here
            result = {
                "provider": "shopify",
                "synced_count": 0,
                "status": "success",
                "details": {
                    "shop": shop_domain,
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

            # Cache the result
            if self._redis:
                await self._redis.set(
                    f"sync:result:{user_id}:shopify",
                    json.dumps(result),
                    ex=3600  # Cache for 1 hour
                )
            
            return result

        except Exception as e:
            logger.error(f"Shopify sync failed: {str(e)}", exc_info=True)
            raise
        finally:
            # Always clean up the lock if Redis is available
            if self._redis:
                try:
                    await self._redis.delete(cache_key)
                except Exception as e:
                    logger.error(f"Failed to clean up sync lock: {str(e)}")

# Remove the standalone sync_payment_data function

def sync_payment_data(user_id: int, provider: Optional[str] = None):
    """
    Synchronous wrapper used by background task to run an on-demand sync.
    
    Args:
        user_id: User identifier
        provider: Optional provider name ('shopify', 'stripe', 'quickbooks' or None for all)
        
    Returns:
        Dictionary with sync results
    """
    async def run():
        service = DataSyncService()
        logger.info(f"Starting payment sync for user {user_id} provider={provider}")
        
        try:
            if provider is None:
                results = await service.sync_all_sources(user_id=user_id, force_sync=True)
                return {
                    "status": "success",
                    "message": "All sources synced",
                    "results": results
                }
            
            try:
                source = DataSource(provider.lower())
            except ValueError:
                logger.warning(f"Invalid provider '{provider}', falling back to all sources")
                results = await service.sync_all_sources(user_id=user_id, force_sync=True)
                return {
                    "status": "success", 
                    "message": f"Invalid provider {provider}, synced all sources instead",
                    "results": results
                }
            
            result = await service._sync_source(user_id=user_id, source=source)
            return {
                "status": "success",
                "message": f"Source {source.value} synced",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Sync failed for user {user_id}: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Sync failed: {str(e)}",
                "error": str(e)
            }
            
        finally:
            await service.cleanup()
            logger.info(f"Sync completed for user {user_id}")

    return asyncio.run(run())

class DataSource(Enum):
    """Supported data sources for synchronization"""
    STRIPE = "stripe"
    SHOPIFY = "shopify"
    QUICKBOOKS = "quickbooks"


class SyncStatus(Enum):
    """Synchronization status codes"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class SyncResult:
    """Result of a synchronization operation"""
    source: DataSource
    status: SyncStatus
    records_processed: int
    records_created: int
    records_updated: int
    errors: List[str]
    sync_duration: float
    last_sync_timestamp: datetime


class DataSyncService:
    """Service for syncing payment data from various providers"""
    
    def __init__(self, session: AsyncSession = None):
        self.session = session
        self._redis = None  # Will be initialized on first use
        self._shopify_client = None
        self.rate_limits = {
            DataSource.STRIPE: {"requests_per_second": 100, "burst": 1000},
            DataSource.SHOPIFY: {"requests_per_second": 2, "burst": 40},
            DataSource.QUICKBOOKS: {"requests_per_second": 10, "burst": 100}
        }
        
        # Initialize API clients
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self._setup_http_clients()

    async def _init_redis(self):
        """Initialize Redis connection if not already initialized"""
        if not self._redis:
            try:
                await redis_client.init()
                self._redis = await aioredis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True
                )
                logger.info("Redis connection initialized")
            except Exception as e:
                logger.error(f"Redis initialization failed: {str(e)}")
                raise

    async def sync_payment_data(self, user_id: str, provider: str) -> Dict[str, Any]:
        """Main entry point for payment data synchronization"""
        try:
            if provider.lower() == "shopify":
                # Get user's Shopify credentials
                user = await self.session.get(User, user_id)
                if not user or not user.shopify_access_token or not user.shopify_shop_domain:
                    raise ValueError("Shopify credentials not configured")
                
                return await self.sync_shopify_payments(
                    user_id=user_id,
                    shop_domain=user.shopify_shop_domain,
                    access_token=user.shopify_access_token
                )
            else:
                try:
                    source = DataSource(provider.lower())
                    return await self._sync_source(
                        user_id=int(user_id),
                        source=source
                    )
                except ValueError:
                    raise ValueError(f"Unsupported provider: {provider}")

        except Exception as e:
            logger.error(f"Payment sync failed: {str(e)}", exc_info=True)
            raise

    async def sync_shopify_payments(self, user_id: str, shop_domain: str, access_token: str) -> Dict[str, Any]:
        """Sync payments from Shopify"""
        await self._init_redis()  # Ensure Redis is initialized
        cache_key = f"sync:shopify:{user_id}"
        
        try:
            if self._redis:
                # Check if sync is already running
                exists = await self._redis.exists(cache_key)
                if exists:
                    return {
                        "status": "in_progress",
                        "message": "Sync already in progress"
                    }

                # Set sync status
                await self._redis.set(cache_key, "running", ex=300)  # 5 min timeout
            
            # Your sync logic here
            result = {
                "provider": "shopify",
                "synced_count": 0,
                "status": "success",
                "details": {
                    "shop": shop_domain,
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

            # Cache the result
            if self._redis:
                await self._redis.set(
                    f"sync:result:{user_id}:shopify",
                    json.dumps(result),
                    ex=3600  # Cache for 1 hour
                )
            
            return result

        except Exception as e:
            logger.error(f"Shopify sync failed: {str(e)}", exc_info=True)
            raise
        finally:
            # Always clean up the lock if Redis is available
            if self._redis:
                try:
                    await self._redis.delete(cache_key)
                except Exception as e:
                    logger.error(f"Failed to clean up sync lock: {str(e)}")

    async def _setup_http_clients(self):
        """Initialize HTTP clients for external APIs"""
        self.shopify_client = httpx.AsyncClient(
            base_url=f"https://{settings.SHOPIFY_SHOP_DOMAIN}.myshopify.com/admin/api/2023-10",
            headers={
                "X-Shopify-Access-Token": settings.SHOPIFY_ACCESS_TOKEN,
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
        
        self.quickbooks_client = httpx.AsyncClient(
            base_url=settings.QUICKBOOKS_BASE_URL,
            headers={
                "Authorization": f"Bearer {settings.QUICKBOOKS_ACCESS_TOKEN}",
                "Accept": "application/json"
            },
            timeout=30.0
        )
    
    async def sync_all_sources(self, user_id: int, force_sync: bool = False) -> Dict[DataSource, SyncResult]:
        """
        Synchronize data from all configured sources for a user
        
        Args:
            user_id: User identifier
            force_sync: Skip rate limiting and sync immediately
            
        Returns:
            Dictionary mapping data sources to their sync results
        """
        logger.info(f"Starting full sync for user {user_id}")
        
        results = {}
        sync_tasks = []
        
        # Check if sync is needed (unless forced)
        if not force_sync:
            last_sync = await self._get_last_sync_time(user_id)
            if last_sync and (datetime.utcnow() - last_sync).seconds < settings.MIN_SYNC_INTERVAL:
                logger.info(f"Skipping sync for user {user_id} - too recent")
                return results
        
        # Create sync tasks for each source
        for source in DataSource:
            if await self._is_source_enabled(user_id, source):
                task = asyncio.create_task(
                    self._sync_source(user_id, source)
                )
                sync_tasks.append((source, task))
        
        # Execute all sync tasks concurrently
        for source, task in sync_tasks:
            try:
                result = await task
                results[source] = result
                logger.info(f"Sync completed for {source.value}: {result.status.value}")
            except Exception as e:
                logger.error(f"Sync failed for {source.value}: {str(e)}")
                results[source] = SyncResult(
                    source=source,
                    status=SyncStatus.FAILED,
                    records_processed=0,
                    records_created=0,
                    records_updated=0,
                    errors=[str(e)],
                    sync_duration=0.0,
                    last_sync_timestamp=datetime.utcnow()
                )
        
        # Update last sync timestamp
        await self._update_last_sync_time(user_id)
        
        logger.info(f"Full sync completed for user {user_id}")
        return results

    async def _sync_source(self, user_id: int, source: DataSource) -> SyncResult:
        """Synchronize data from a specific source"""
        start_time = datetime.utcnow()
        errors = []
        records_processed = records_created = records_updated = 0
        
        try:
            await self._apply_rate_limit(source)
            last_sync = await self._get_source_last_sync(user_id, source)
            
            # Fetch and validate data
            data = []
            try:
                if source == DataSource.STRIPE:
                    data = await self._fetch_stripe_data(user_id, last_sync)
                elif source == DataSource.SHOPIFY:
                    data = await self._fetch_shopify_data(user_id, last_sync)
                elif source == DataSource.QUICKBOOKS:
                    data = await self._fetch_quickbooks_data(user_id, last_sync)
                else:
                    raise ValueError(f"Unsupported data source: {source}")
                
                if not isinstance(data, list):
                    logger.error(f"Invalid data type from {source.value}: {type(data)}")
                    data = []
                    
            except Exception as e:
                logger.error(f"Data fetch error for {source.value}: {str(e)}")
                errors.append(f"Fetch error: {str(e)}")
                raise
            
            # Process records
            async with get_async_session() as session:
                for record in data:
                    if not isinstance(record, dict):
                        errors.append(f"Invalid record format: {type(record)}")
                        continue
                        
                    try:
                        processed = await self._process_record(session, user_id, source, record)
                        records_processed += 1
                        records_created += processed["created"]
                        records_updated += processed["updated"]
                    except Exception as e:
                        errors.append(f"Record processing error: {str(e)}")
                
                await session.commit()
            
            await self._update_source_last_sync(user_id, source)
            status = (SyncStatus.SUCCESS if not errors else 
                     SyncStatus.PARTIAL if records_processed > 0 else 
                     SyncStatus.FAILED)
            
        except Exception as e:
            logger.error(f"Sync failed for {source.value}: {str(e)}", exc_info=True)
            errors.append(str(e))
            status = SyncStatus.FAILED
        
        return SyncResult(
            source=source,
            status=status,
            records_processed=records_processed,
            records_created=records_created,
            records_updated=records_updated,
            errors=errors,
            sync_duration=(datetime.utcnow() - start_time).total_seconds(),
            last_sync_timestamp=start_time
        )
    
    async def _fetch_stripe_data(self, user_id: int, since: Optional[datetime] = None) -> List[Dict]:
        """
        Fetch transaction data from Stripe API
        
        Args:
            user_id: User identifier
            since: Fetch data since this timestamp
            
        Returns:
            List of Stripe payment intent and charge objects
        """
        logger.info(f"Fetching Stripe data for user {user_id}")
        
        # Get user's Stripe account ID
        async with get_async_session() as session:
            result = await session.execute(
                select(User.stripe_account_id).where(User.id == user_id)
            )
            stripe_account_id = result.scalar_one_or_none()
        
        if not stripe_account_id:
            logger.warning(f"No Stripe account found for user {user_id}")
            return []
        
        data = []
        
        # Prepare query parameters
        params = {
            "limit": 100,
            "expand": ["data.payment_method", "data.customer"]
        }
        
        if since:
            params["created"] = {"gte": int(since.timestamp())}
        
        try:
            # Fetch payment intents
            payment_intents = stripe.PaymentIntent.list(
                stripe_account=stripe_account_id,
                **params
            )
            
            for intent in payment_intents.auto_paging_iter():
                data.append({
                    "type": "payment_intent",
                    "data": intent.to_dict(),
                    "source": DataSource.STRIPE.value
                })
            
            # Fetch charges for additional data
            charges = stripe.Charge.list(
                stripe_account=stripe_account_id,
                **params
            )
            
            for charge in charges.auto_paging_iter():
                data.append({
                    "type": "charge",
                    "data": charge.to_dict(),
                    "source": DataSource.STRIPE.value
                })
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe API error: {str(e)}")
            raise
        
        logger.info(f"Fetched {len(data)} records from Stripe")
        return data
    
    async def _fetch_shopify_data(self, user_id: int, since: Optional[datetime] = None) -> List[Dict]:
        """
        Fetch transaction data from Shopify API
        
        Args:
            user_id: User identifier
            since: Fetch data since this timestamp
            
        Returns:
            List of Shopify order and transaction objects
        """
        logger.info(f"Fetching Shopify data for user {user_id}")
        
        data = []
        params = {"limit": 250, "status": "any"}
        
        if since:
            params["updated_at_min"] = since.isoformat()
        
        try:
            # Fetch orders
            response = await self.shopify_client.get("/orders.json", params=params)
            response.raise_for_status()
            
            orders_data = response.json()
            orders = orders_data.get("orders", [])
            
            for order in orders:
                data.append({
                    "type": "order",
                    "data": order,
                    "source": DataSource.SHOPIFY.value
                })
                
                # Fetch transactions for each order
                order_id = order["id"]
                tx_response = await self.shopify_client.get(f"/orders/{order_id}/transactions.json")
                tx_response.raise_for_status()
                
                transactions = tx_response.json().get("transactions", [])
                for transaction in transactions:
                    data.append({
                        "type": "transaction",
                        "data": transaction,
                        "source": DataSource.SHOPIFY.value,
                        "order_id": order_id
                    })
        
        except httpx.HTTPError as e:
            logger.error(f"Shopify API error: {str(e)}")
            raise
        
        logger.info(f"Fetched {len(data)} records from Shopify")
        return data
    
    async def _fetch_quickbooks_data(self, user_id: int, since: Optional[datetime] = None) -> List[Dict]:
        """
        Fetch transaction data from QuickBooks API
        
        Args:
            user_id: User identifier
            since: Fetch data since this timestamp
            
        Returns:
            List of QuickBooks payment and invoice objects
        """
        logger.info(f"Fetching QuickBooks data for user {user_id}")
        
        # Get user's QuickBooks company ID
        async with get_async_session() as session:
            result = await session.execute(
                select(User.quickbooks_company_id).where(User.id == user_id)
            )
            company_id = result.scalar_one_or_none()
        
        if not company_id:
            logger.warning(f"No QuickBooks company found for user {user_id}")
            return []
        
        data = []
        
        try:
            # Build query for payments
            query = "SELECT * FROM Payment"
            if since:
                query += f" WHERE Metadata.LastUpdatedTime > '{since.isoformat()}'"
            
            response = await self.quickbooks_client.get(
                f"/v3/company/{company_id}/query",
                params={"query": query}
            )
            response.raise_for_status()
            
            qb_data = response.json()
            payments = qb_data.get("QueryResponse", {}).get("Payment", [])
            
            for payment in payments:
                data.append({
                    "type": "payment",
                    "data": payment,
                    "source": DataSource.QUICKBOOKS.value
                })
            
            # Fetch invoices
            invoice_query = "SELECT * FROM Invoice"
            if since:
                invoice_query += f" WHERE Metadata.LastUpdatedTime > '{since.isoformat()}'"
            
            invoice_response = await self.quickbooks_client.get(
                f"/v3/company/{company_id}/query",
                params={"query": invoice_query}
            )
            invoice_response.raise_for_status()
            
            invoice_data = invoice_response.json()
            invoices = invoice_data.get("QueryResponse", {}).get("Invoice", [])
            
            for invoice in invoices:
                data.append({
                    "type": "invoice",
                    "data": invoice,
                    "source": DataSource.QUICKBOOKS.value
                })
        
        except httpx.HTTPError as e:
            logger.error(f"QuickBooks API error: {str(e)}")
            raise
        
        logger.info(f"Fetched {len(data)} records from QuickBooks")
        return data
    
    async def _process_record(self, session: AsyncSession, user_id: int, source: DataSource, record: Dict) -> Dict[str, bool]:
        """
        Process and store a single record in the database
        
        Args:
            session: Database session
            user_id: User identifier
            source: Data source
            record: Raw record data
            
        Returns:
            Dictionary indicating if record was created or updated
        """
        created = False
        updated = False
        
        try:
            # Extract common fields based on source and record type
            transaction_data = self._extract_transaction_data(source, record)
            transaction_data["user_id"] = user_id
            
            # Check if transaction already exists
            existing = await session.execute(
                select(Transaction).where(
                    and_(
                        Transaction.user_id == user_id,
                        Transaction.external_id == transaction_data["external_id"],
                        Transaction.source == source.value
                    )
                )
            )
            existing_transaction = existing.scalar_one_or_none()
            
            if existing_transaction:
                # Update existing transaction
                for key, value in transaction_data.items():
                    if hasattr(existing_transaction, key) and key != "id":
                        setattr(existing_transaction, key, value)
                updated = True
            else:
                # Create new transaction
                transaction = Transaction(**transaction_data)
                session.add(transaction)
                created = True
            
        except Exception as e:
            logger.error(f"Failed to process record: {str(e)}")
            raise
        
        return {"created": created, "updated": updated}
    
    def _extract_transaction_data(self, source: DataSource, record: Dict) -> Dict:
        """
        Extract standardized transaction data from source-specific record
        
        Args:
            source: Data source
            record: Raw record data
            
        Returns:
            Standardized transaction data dictionary
        """
        if source == DataSource.STRIPE:
            return self._extract_stripe_transaction(record)
        elif source == DataSource.SHOPIFY:
            return self._extract_shopify_transaction(record)
        elif source == DataSource.QUICKBOOKS:
            return self._extract_quickbooks_transaction(record)
        else:
            raise ValueError(f"Unsupported source: {source}")
    
    
    
    def _extract_stripe_transaction(self, record: Dict) -> Dict:
        """Extract transaction data from Stripe record"""
        data = record["data"]
        record_type = record["type"]
        
        if record_type == "payment_intent":
            return {
                "external_id": data["id"],
                "source": DataSource.STRIPE.value,
                "transaction_type": "payment",
                "amount": data["amount"] / 100,  # Convert from cents
                "currency": data["currency"].upper(),
                "status": data["status"],
                "created_at": datetime.fromtimestamp(data["created"]),
                "description": data.get("description"),
                "customer_email": data.get("receipt_email"),
                "payment_method": data.get("payment_method_types", [None])[0],
                "metadata": data.get("metadata", {}),
                "raw_data": data
            }
        elif record_type == "charge":
            return {
                "external_id": data["id"],
                "source": DataSource.STRIPE.value,
                "transaction_type": "charge",
                "amount": data["amount"] / 100,
                "currency": data["currency"].upper(),
                "status": "succeeded" if data["paid"] else "failed",
                "created_at": datetime.fromtimestamp(data["created"]),
                "description": data.get("description"),
                "customer_email": data.get("receipt_email"),
                "payment_method": data.get("payment_method_details", {}).get("type"),
                "metadata": data.get("metadata", {}),
                "raw_data": data
            }
    
    def _extract_shopify_transaction(self, record: Dict) -> Dict:
        """Extract transaction data from Shopify record"""
        data = record["data"]
        record_type = record["type"]
        now = datetime.utcnow()
        
        if record_type == "order":
            description = f"Order #{data.get('order_number')}"
            metadata = {
                "order_number": data.get("order_number"),
                "fulfillment_status": data.get("fulfillment_status"),
                "customer": {
                    "email": data.get("email"),
                    "first_name": data.get("customer", {}).get("first_name"),
                    "last_name": data.get("customer", {}).get("last_name")
                }
            }
            
            return {
                "id": str(uuid.uuid4()),
                "user_id": data.get("user_id"),
                "amount": float(data.get("total_price", 0)),
                "currency": data.get("currency", "USD"),
                "status": data.get("financial_status", "unknown"),
                "transaction_type": "shopify_order",
                "stripe_payment_id": None,
                "shopify_order_id": str(data["id"]),
                "quickbooks_ref": None,
                "description": description,
                "transaction_metadata": metadata,
                "created_at": datetime.fromisoformat(data["created_at"].replace('Z', '+00:00')),
                "updated_at": now,
                "processed_at": now
            }
        elif record_type == "transaction":
            description = f"Transaction for order #{record.get('order_id')}"
            metadata = {
                "order_id": record.get("order_id"),
                "payment_details": {
                    "gateway": data.get("gateway"),
                    "payment_method": data.get("payment_method_details", {}).get("type"),
                    "status_details": data.get("status_details")
                }
            }
            
            return {
                "id": str(uuid.uuid4()),
                "user_id": data.get("user_id"),
                "amount": float(data.get("amount", 0)),
                "currency": data.get("currency", "USD"),
                "status": data.get("status", "unknown"),
                "transaction_type": "shopify_payment",
                "stripe_payment_id": None,
                "shopify_order_id": str(record.get("order_id")),
                "quickbooks_ref": None,
                "description": description,
                "transaction_metadata": metadata,
                "created_at": datetime.fromisoformat(data["created_at"].replace('Z', '+00:00')),
                "updated_at": now,
                "processed_at": now
            }
    
    def _extract_quickbooks_transaction(self, record: Dict) -> Dict:
        """Extract transaction data from QuickBooks record"""
        data = record["data"]
        record_type = record["type"]
        
        if record_type == "payment":
            return {
                "external_id": str(data["Id"]),
                "source": DataSource.QUICKBOOKS.value,
                "transaction_type": "payment",
                "amount": float(data.get("TotalAmt", 0)),
                "currency": "USD",  # QuickBooks typically uses company's base currency
                "status": "completed",
                "created_at": datetime.fromisoformat(data["MetaData"]["CreateTime"]),
                "description": f"QB Payment {data['Id']}",
                "customer_email": data.get("CustomerRef", {}).get("name"),
                "payment_method": data.get("PaymentMethodRef", {}).get("name"),
                "metadata": {
                    "qb_txn_number": data.get("TxnNumber"),
                    "customer_ref": data.get("CustomerRef", {}).get("value")
                },
                "raw_data": data
            }
        elif record_type == "invoice":
            return {
                "external_id": str(data["Id"]),
                "source": DataSource.QUICKBOOKS.value,
                "transaction_type": "invoice",
                "amount": float(data.get("TotalAmt", 0)),
                "currency": "USD",
                "status": data.get("Balance", 0) == 0 and "paid" or "unpaid",
                "created_at": datetime.fromisoformat(data["MetaData"]["CreateTime"]),
                "description": f"Invoice {data.get('DocNumber', data['Id'])}",
                "customer_email": data.get("CustomerRef", {}).get("name"),
                "metadata": {
                    "doc_number": data.get("DocNumber"),
                    "due_date": data.get("DueDate"),
                    "balance": data.get("Balance")
                },
                "raw_data": data
            }
    
    async def _apply_rate_limit(self, source: DataSource):
        """Apply rate limiting for API calls"""
        if not self._redis:
            logger.warning(f"Redis client not available, skipping rate limit for {source.value}")
            return
            
        try:
            rate_limit_key = f"rate_limit:{source.value}"
            current_count = await self._redis.get(rate_limit_key)
            
            if current_count:
                current_count = int(current_count)
                if current_count >= self.rate_limits[source]["requests_per_second"]:
                    await asyncio.sleep(1)
            
            await self._redis.incr(rate_limit_key)
            await self._redis.expire(rate_limit_key, 1)
            
        except Exception as e:
            logger.error(f"Rate limiting failed for {source.value}: {str(e)}")
            # Continue without rate limiting rather than failing the sync
            return
    
    async def _is_source_enabled(self, user_id: int, source: DataSource) -> bool:
        """Check if a data source is enabled for the user"""
        config_key = f"user:{user_id}:sync_config"
        config = await self._redis.hget(config_key, source.value)
        return config == "enabled" if config else True  # Default to enabled
    
    async def _get_last_sync_time(self, user_id: int) -> Optional[datetime]:
        """Get the last sync timestamp for a user"""
        sync_key = f"user:{user_id}:last_sync"
        timestamp = await self._redis.get(sync_key)
        
        if timestamp:
            return datetime.fromisoformat(timestamp.decode())
        return None
    
    async def _update_last_sync_time(self, user_id: int):
        """Update the last sync timestamp for a user"""
        sync_key = f"user:{user_id}:last_sync"
        await self._redis.set(sync_key, datetime.utcnow().isoformat())
    
    async def _get_source_last_sync(self, user_id: int, source: DataSource) -> Optional[datetime]:
        """Get the last sync timestamp for a specific source"""
        sync_key = f"user:{user_id}:last_sync:{source.value}"
        timestamp = await self._redis.get(sync_key)
        
        if timestamp:
            return datetime.fromisoformat(timestamp.decode())
        return None
    
    async def _update_source_last_sync(self, user_id: int, source: DataSource):
        """Update the last sync timestamp for a specific source"""
        sync_key = f"user:{user_id}:last_sync:{source.value}"
        await self._redis.set(sync_key, datetime.utcnow().isoformat())
    
    async def schedule_sync(self, user_id: int, delay_seconds: int = 0) -> str:
        """
        Schedule a background sync job
        
        Args:
            user_id: User identifier
            delay_seconds: Delay before execution
            
        Returns:
            Job ID for tracking
        """
        job = celery_app.send_task(
            "app.celery_worker.sync_user_data",
            args=[user_id],
            countdown=delay_seconds
        )
        
        logger.info(f"Scheduled sync job {job.id} for user {user_id}")
        return job.id
    
    async def get_sync_status(self, user_id: int) -> Dict[str, Any]:
        """
        Get current sync status for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with sync status information
        """
        last_sync = await self._get_last_sync_time(user_id)
        
        status = {
            "user_id": user_id,
            "last_sync": last_sync.isoformat() if last_sync else None,
            "sources": {}
        }
        
        for source in DataSource:
            source_sync = await self._get_source_last_sync(user_id, source)
            enabled = await self._is_source_enabled(user_id, source)
            
            status["sources"][source.value] = {
                "enabled": enabled,
                "last_sync": source_sync.isoformat() if source_sync else None
            }
        
        return status
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            await self.shopify_client.aclose()
            await self.quickbooks_client.aclose()
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")


# Background task for Celery worker
@celery_app.task(bind=True)
def sync_user_data_task(self, user_id: int):
    """
    Celery task for background data synchronization
    
    Args:
        user_id: User identifier to sync data for
    """
    import asyncio
    
    async def run_sync():
        sync_service = DataSyncService()
        try:
            results = await sync_service.sync_all_sources(user_id)
            
            # Log results
            for source, result in results.items():
                logger.info(
                    f"Sync completed for user {user_id}, source {source.value}: "
                    f"{result.records_processed} processed, {result.status.value}"
                )
            
            return {
                "user_id": user_id,
                "status": "completed",
                "results": {k.value: v.__dict__ for k, v in results.items()}
            }
            
        except Exception as e:
            logger.error(f"Sync failed for user {user_id}: {str(e)}")
            raise self.retry(exc=e, countdown=60, max_retries=3)
        
        finally:
            await sync_service.cleanup()
    
    return asyncio.run(run_sync())
