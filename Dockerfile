FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get install -y libmagic1 && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["uvicorn", "app.main:app", "--host", "10.100.16.187", "--port", "8001"]


# uvicorn app.main:app --host 26.77.162.134 --port 8000
