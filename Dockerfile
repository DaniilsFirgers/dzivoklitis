FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY scraper /app/scraper
COPY config.toml /app/config.toml
COPY flats.json /app/flats.json

# Set the PYTHONPATH to /app so that Python can find the scraper module
ENV PYTHONPATH="/app"

CMD ["python", "/app/scraper/main.py"]