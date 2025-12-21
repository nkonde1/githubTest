FROM python:3.11-slim

# Set environment variables for Python
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Set the working directory in the container
WORKDIR /app/backend

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install build dependencies, then clean up to reduce image size
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libc6-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y --auto-remove gcc libc6-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy the rest of the application code
COPY . .

# Stage 2: Production/Runtime Stage
# Use a smaller base image for the final production image
FROM python:3.10-slim-buster AS production_stage

# Set environment variables for Python
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Set the working directory in the container
WORKDIR /app/backend

# Copy only the installed packages from the build stage
COPY --from=build_stage /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
# Copy the application code from the build stage
COPY --from=build_stage /app/backend .

# Expose the port FastAPI will run on
EXPOSE 8000

# Command to run the application using Uvicorn
# Use Gunicorn with Uvicorn workers for production for better performance and management
# Use --reload for development purposes (hot reload)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" ]

# Production command (uncomment and replace the above CMD for production deployment)
# CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]