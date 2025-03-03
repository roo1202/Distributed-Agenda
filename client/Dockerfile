
FROM node:16-alpine as frontend-builder

WORKDIR /app
COPY frontend/package*.json ./
RUN npm cache clean --force && \
    rm -rf node_modules package-lock.json && \
    npm install && \
    npm install @rollup/rollup-linux-x64-gnu --save-optional
COPY frontend/ .
RUN npm run build

# ------------------------

FROM python:3.9-slim

RUN apt-get update && apt-get install -y npm && \
    npm install -g http-server && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --from=frontend-builder /app/dist /app/frontend/dist

COPY backend/ .

ENV FRONTEND_PORT=8080 BACKEND_PORT=8000

EXPOSE ${FRONTEND_PORT} ${BACKEND_PORT}

CMD ["sh", "-c", "python main.py --port $BACKEND_PORT & http-server /app/frontend/dist -p $FRONTEND_PORT"]