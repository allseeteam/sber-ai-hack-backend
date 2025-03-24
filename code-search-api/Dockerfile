FROM python:3.10-slim

WORKDIR /app

# Install git and other dependencies
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire package
COPY code_search_api /app/code_search_api
COPY data /app/data

# Create directories for data
RUN mkdir -p /app/data/semantic_search/repos && \
    chmod -R 777 /app/data

# Run FastAPI application with correct module path
CMD ["uvicorn", "code_search_api.api:app", "--host", "0.0.0.0", "--port", "8000"]
