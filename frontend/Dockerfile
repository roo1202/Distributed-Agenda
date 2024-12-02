# frontend/Dockerfile
FROM node:20

WORKDIR /app

COPY frontend.sh .

# Instalar iproute2 para el comando ip
RUN apt-get update && apt-get install -y iproute2

# Copiar package.json y package-lock.json e instalar dependencias
COPY package.json package-lock.json ./
RUN npm install

COPY . .

RUN chmod +x ./frontend.sh

# Exponer el puerto en el que correrá la aplicación
EXPOSE 3000

CMD ["sh", "-c", "./frontend.sh && npm run dev"]