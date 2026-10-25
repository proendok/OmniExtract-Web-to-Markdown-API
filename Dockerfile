FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for lxml and network tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libxml2-dev \
    libxslt-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose service port
EXPOSE 8000

ENV HOST=0.0.0.0
ENV PORT=8000
ENV APP_ENV=production

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
