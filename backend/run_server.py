import os
import uvicorn

if __name__ == "__main__":
    # Use the PORT environment variable provided by Cloud Run, default to 8080
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("UVICORN_HOST", "0.0.0.0")

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=False,  # Always False in production
        log_level="info"
    )
