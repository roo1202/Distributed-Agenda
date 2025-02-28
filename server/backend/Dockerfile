FROM python:3.9-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000 5001 5002 5003 5004

CMD ["python", "main.py"]