# Use a Python base image with necessary scientific libraries
FROM python:3.10-slim

# Install system dependencies for RDKit and other scientific packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libxrender1 \
    libxext6 \
    libfontconfig1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python requirements
COPY research/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Node.js for the frontend
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Copy the entire project
COPY . .

# Build the frontend
WORKDIR /app/research-frontend
RUN npm install && npm run build

# Final stage setup
WORKDIR /app
EXPOSE 8125

# Create a startup script for production
RUN echo '#!/bin/bash\npython research/app/api.py & \ncd research-frontend && npm run preview -- --host 0.0.0.0 --port 5173' > /app/start_prod.sh
RUN chmod +x /app/start_prod.sh

CMD ["/app/start_prod.sh"]
