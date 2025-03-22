FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    net-tools \
    gcc \
    build-essential \
    iputils-ping \
    iproute2 

# Establecer el directorio de trabajo

WORKDIR /app

# Copiar requirements.txt e instalar dependencias
COPY /backend/requirements.txt ./backend/

RUN pip install --no-cache-dir -r backend/requirements.txt

# Copiar el contenido de la carpeta app/ al WORKDIR (/app)
COPY /backend .

FROM node:20-alpine

# Copiar solo los archivos necesarios para instalar dependencias
COPY /frontend .

# Instalar las dependencias
#RUN npm cache clean --force && rm -rf /frontend/node_modules /frontend/package-lock.json && npm install && npm install @rollup/rollup-linux-x64-gnu --save-optional

# Exponer el puerto donde corre Nuxt
EXPOSE 3000

# Ejecutar Nuxt
#CMD ["npm", "run", "dev"]

CMD ["sh", "-c", "tail -f /dev/null"]