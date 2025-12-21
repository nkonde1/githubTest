# AI Agent Environment Configuration

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
OLLAMA_TIMEOUT=120
OLLAMA_MAX_RETRIES=3

# Service Configuration
AI_AGENT_HOST=0.0.0.0
AI_AGENT_PORT=8080
AI_AGENT_WORKERS=4
AI_AGENT_DEBUG=false

# Session Management
SESSION_TIMEOUT=3600
MAX_SESSIONS=1000
CLEANUP_INTERVAL=300

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/app/logs/ai-agent.log
STRUCTURED_LOGGING=true

# Redis Configuration (for session persistence)
REDIS_URL=redis://localhost:6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_SSL=false

# Database Configuration (optional)
DATABASE_URL=postgresql://user:password@localhost:5432/finance_platform
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Security Configuration
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here
JWT_SECRET=your-jwt-secret-here
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Performance Tuning
RESPONSE_CACHE_TTL=300
MAX_RESPONSE_LENGTH=4000
CONCURRENT_REQUESTS_LIMIT=100

# Model Configuration
DEFAULT_TEMPERATURE=0.7
DEFAULT_MAX_TOKENS=2000
CONTEXT_WINDOW_SIZE=10
ENABLE_STREAMING=true

# Monitoring and Metrics
ENABLE_METRICS=true
METRICS_PORT=9090
HEALTH_CHECK_INTERVAL=30

# Feature Flags
ENABLE_CONVERSATION_HISTORY=true
ENABLE_ANALYTICS_INSIGHTS=true
ENABLE_REPORT_GENERATION=true
ENABLE_REAL_TIME_ANALYSIS=true

# External Integrations
BACKEND_API_URL=http://localhost:8000
BACKEND_API_KEY=your-backend-api-key
WEBHOOK_URL=http://localhost:8000/webhook/ai-agent

# Development Settings
DEVELOPMENT_MODE=false
MOCK_OLLAMA=false
ENABLE_DEBUG_LOGGING=false
PROFILE_PERFORMANCE=false