FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY scraper /app/scraper
COPY config.toml /app/config.toml
COPY flats.json /app/flats.json

CMD ["python", "/app/scraper/main.py"]