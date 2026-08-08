# Base image: a slim Python environment (smaller download, faster builds
# than the full python:3.11 image, but still has everything we need)
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed by some packages (torch/sentence-transformers
# and chromadb pull in a few native libraries)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy just requirements first — Docker caches layers, so if only your
# app code changes (not requirements.txt), this pip install step is
# skipped on rebuild instead of reinstalling everything from scratch.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the actual application code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
