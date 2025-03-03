FROM python:3.9-slim

#VOLUME /app_data

RUN apt-get update && apt-get install -y \
    net-tools \
    gcc \
    build-essential \
    iputils-ping \
    iproute2 && \
    rm -rf /var/lib/apt/lists/*


# Establecer el directorio de trabajo
WORKDIR /app

# Copiar requirements.txt e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el contenido de la carpeta app/ al WORKDIR (/app)
COPY app/ .

# Variables de entorno requeridas
 ENV LOCAL_IP="" 
#     NODE_PORT_1="" \
#     NODE_PORT_2="" \
#     NODE_PORT_3="" \
#     NODE_PORT_4="" \
#     NODE_PORT_5=""

# Comando de ejecución
CMD ["sh", "-c", "tail -f /dev/null"]
#CMD ["sh", "-c", "python main.py ${LOCAL_IP}"]