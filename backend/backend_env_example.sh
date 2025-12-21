# --- Core Application Settings ---
# The name of your project.
PROJECT_NAME="SMB Embedded Finance Platform"

# Environment setting: "development", "staging", "production"
ENVIRONMENT="development"

# FastAPI server host and port.
UVICORN_HOST="0.0.0.0"
UVICORN_PORT=8000

# CORS origins: Comma-separated list of allowed origins for your frontend.
# In development, you might use http://localhost:3000. In production, use your actual domain.
BACKEND_CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"

# API version string.
API_V1_STR="/api/v1"


# --- Database Settings (PostgreSQL) ---
# PostgreSQL connection string. Format: postgresql+asyncpg://user:password@host:port/database
# For Docker Compose, 'db' will be the service name for your PostgreSQL container.
DATABASE_URL="postgresql+asyncpg://user:password@db:5432/finance_db"
# Example for local development without Docker:
# DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/finance_db"


# --- Redis Settings ---
# Redis URL for Celery broker and result backend, and for caching/session store.
# For Docker Compose, 'redis' will be the service name for your Redis container.
REDIS_URL="redis://redis:6377/0"
# Example for local development without Docker:
# REDIS_URL="redis://localhost:6377/0"


# --- Authentication Settings ---
# A strong secret key for JWT token encoding. Generate a complex, random string.
# Command to generate a secret key: openssl rand -hex 32
SECRET_KEY="your_super_secret_jwt_key_here_replace_me_in_production"

# Access token expiration time in minutes.
ACCESS_TOKEN_EXPIRE_MINUTES=60


# --- External Service Integrations ---
# Stripe API Key (for payment processing)
# STRIPE_SECRET_KEY="sk_test_..."

# Shopify API credentials (if integrating with Shopify stores)
# SHOPIFY_API_KEY="shpk_..."
# SHOPIFY_API_SECRET="shpss_..."

# QuickBooks API credentials (if integrating with QuickBooks)
# QUICKBOOKS_CLIENT_ID="your_quickbooks_client_id"
# QUICKBOOKS_CLIENT_SECRET="your_quickbooks_client_secret"


# --- AI Agent Settings (Ollama LLaMA 3.2) ---
# The base URL for your Ollama server.
# For Docker Compose, 'ollama' will be the service name for your Ollama container.
OLLAMA_BASE_URL="http://ollama:11434"
# Example for local development without Docker:
# OLLAMA_BASE_URL="http://localhost:11434"

# The name of the LLaMA 3.2 model to use (or other model you've pulled).
OLLAMA_MODEL_NAME="llama3.2"


# --- Logging Settings ---
# Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL="INFO"