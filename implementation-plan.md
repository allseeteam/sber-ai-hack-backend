# Code Search API Restructuring Plan

## Overview
This document outlines the steps to fix the import error by restructuring the project into a proper Python package.

## Implementation Steps

### 1. Package Structure Setup
```bash
code-search-api/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── code_search_api/
│   ├── __init__.py
│   ├── api.py
│   ├── models.py
│   ├── settings.py
│   └── services/
└── data/
```

### 2. File Moves and Updates
1. Move all Python files into code_search_api/ directory:
   - api.py → code_search_api/api.py
   - models.py → code_search_api/models.py
   - settings.py → code_search_api/settings.py
   - services/ → code_search_api/services/

2. Create __init__.py to establish proper package

### 3. Import Updates
Update imports in api.py:
```python
# Before
from .settings import settings
from .models import (...)
from .services import QuadrantService

# After
from code_search_api.settings import settings
from code_search_api.models import (...)
from code_search_api.services import QuadrantService
```

### 4. Docker Configuration Updates
Update Dockerfile:
```dockerfile
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
```

## Validation
After implementation, validate:
1. All files are in correct locations
2. Package imports work correctly
3. Docker container builds and runs successfully
4. API endpoints are accessible

## Expected Results
- Import error resolved
- Application starts successfully in Docker
- All API endpoints functional