# Usamos una imagen base de Python con Slim para reducir tamaño
FROM python:3.9-slim

# Instalamos dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    hostname \
    && rm -rf /var/lib/apt/lists/*

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar el contenido de la carpeta app/ al WORKDIR (/app)
COPY multicast_proxy.py .


# Exponemos los puertos necesarios (UDP)
EXPOSE 10000/udp 10001/udp 10002/udp 10003/udp 10004/udp

# Comando para ejecutar la aplicación
#CMD ["python", "multicast_proxy.py"]
CMD ["sh", "-c", "tail -f /dev/null"]