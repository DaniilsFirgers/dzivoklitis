FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY scraper /app/scraper

# Set the PYTHONPATH to /app so that Python can find the scraper module
ENV PYTHONPATH="/app"

CMD ["python3.10", "/app/scraper/main.py"]