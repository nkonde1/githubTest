import asyncio
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session_maker
from app.models import User  # Import from models package
from app.core.config import settings
import httpx
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_session() -> AsyncSession:
    """Get database session"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def setup_shopify_credentials(user_email: str):
    """Configure Shopify credentials from env vars for a user"""
    
    if not settings.has_shopify_config:
        print("\n❌ Shopify credentials not found in environment!")
        return False

    async with get_session() as session:
        # Get user record
        result = await session.execute(
            select(User).where(User.email == user_email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"\n❌ User with email {user_email} not found in database\n")
            return False
            
        try:
            # Test Shopify credentials
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://{settings.SHOPIFY_SHOP_DOMAIN}.myshopify.com/admin/api/{settings.SHOPIFY_API_VERSION}/shop.json",
                    headers={
                        "X-Shopify-Access-Token": settings.SHOPIFY_ACCESS_TOKEN,
                        "Content-Type": "application/json"
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    # Update user
                    stmt = (
                        update(User)
                        .where(User.id == user.id)
                        .values(
                            shopify_access_token=settings.SHOPIFY_ACCESS_TOKEN,
                            shopify_shop_domain=settings.SHOPIFY_SHOP_DOMAIN,
                            shopify_integration_active=True
                        )
                    )
                    await session.execute(stmt)
                    
                    shop_data = response.json()["shop"]
                    print("\n✅ Shopify credentials configured successfully!")
                    print(f"✓ Shop name: {shop_data['name']}")
                    print(f"✓ User updated: {user_email}\n")
                    return True
                else:
                    print(f"\n❌ Shopify API test failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"\n❌ Error configuring Shopify credentials: {str(e)}\n")
            return False

def main():
    """Main entry point"""
    if len(sys.argv) != 2:
        print("\nUsage: python -m app.utils.setup_shopify your-email@example.com\n")
        sys.exit(1)
        
    user_email = sys.argv[1]
    asyncio.run(setup_shopify_credentials(user_email))

if __name__ == "__main__":
    import sys
    main()