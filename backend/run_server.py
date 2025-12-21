#!/usr/bin/env python3
"""
Simple script to run the FastAPI server with correct host settings
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",  # Allow all hosts
        port=8000,
        reload=True,
        log_level="info"
    )
