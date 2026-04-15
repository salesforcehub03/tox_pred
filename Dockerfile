# Use a Python base image with necessary scientific libraries
FROM python:3.10-slim

# 1. Install system dependencies (Rarely changes)
RUN apt-get update && apt-get install -y \
    build-essential \
    libxrender1 \
    libxext6 \
    libfontconfig1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Node.js (Rarely changes)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# 3. Install Python dependencies (Cachable)
WORKDIR /app
COPY research/requirements_render.txt .
RUN pip install --no-cache-dir -r requirements_render.txt

# 4. Build Frontend (Cachable if frontend files don't change)
COPY research-frontend /app/research-frontend
WORKDIR /app/research-frontend
RUN npm install && npm run build

# 5. Copy Backend and Data (Changes frequently)
WORKDIR /app
COPY . .

# 6. Pre-ingest data to bake the cache into the image
RUN python research/pre_ingest.py

# Final stage setup
WORKDIR /app
EXPOSE 10000

# Command to run the FastAPI app
CMD ["python", "research/app/api_render.py"]
