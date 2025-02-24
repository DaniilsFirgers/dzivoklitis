FROM python:3.10-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    libvips-dev \
    && rm -rf /var/lib/apt/lists/*  # Clean up to reduce image size

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY scraper /app/scraper

# Set the PYTHONPATH to /app so that Python can find the scraper module
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1
