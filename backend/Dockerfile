# backend/Dockerfile
FROM python:3.10-alpine

WORKDIR /app

COPY backend.sh .
COPY requirements.txt .

RUN pip install -r requirements.txt --timeout=120 --index-url=https://pypi.org/simple

RUN chmod +x ./backend.sh

EXPOSE 8000

CMD ["sh", "-c", "./backend.sh && uvicorn app.main:app --host 0.0.0.0 --port 8000"]