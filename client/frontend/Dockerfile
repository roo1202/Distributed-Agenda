FROM node:20-alpine

WORKDIR /app

# Copiar solo los archivos necesarios para instalar dependencias
COPY package*.json ./

# Instalar las dependencias
RUN npm cache clean --force && rm -rf node_modules package-lock.json && npm install && npm install @rollup/rollup-linux-x64-gnu --save-optional

COPY . .

# Exponer el puerto donde corre Nuxt
EXPOSE 3000

# Ejecutar Nuxt
CMD ["npm", "run", "dev"]