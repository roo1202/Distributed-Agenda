FROM python:3.9-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# Variables de entorno requeridas
ENV NODE_IP="" \
    NODE_PORT_1="" \
    NODE_PORT_2="" \
    NODE_PORT_3="" \
    NODE_PORT_4="" \
    NODE_PORT_5=""


EXPOSE $NODE_PORT_1 $NODE_PORT_2 $NODE_PORT_3 $NODE_PORT_4 $NODE_PORT_5

CMD ["sh", "-c", "python main.py ${NODE_IP} ${NODE_PORT_1} ${NODE_PORT_2} ${NODE_PORT_3} ${NODE_PORT_4} ${NODE_PORT_5}"]