set +o verbose

# check clients docker networks existence

docker network inspect clients >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "Network clients exists."
else
    docker network create clients --subnet 10.0.10.0/24
    echo "Network clients created."
fi

# check servers docker network existence 

docker network inspect servers >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "Network servers exists."
else
    docker network create servers --subnet 10.0.11.0/24
    echo "Network servers created."
fi

# check router:base docker image existence 

docker image inspect router >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "Image router:base exists."
else
    docker build -t router:base -f router/router_base.Dockerfile router/
    echo "Image router:base created."
fi

# check router docker image existence 

docker image inspect router >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "Image router exists."
else
    docker build -t router -f router/router.Dockerfile router/
    echo "Image router created."
fi

# check router container existence

docker container inspect router >/dev/null 2>&1
if [ $? -eq 0 ]; then
    docker container stop router
    docker container rm router
    echo "Container router removed."    
fi

docker run -d --rm --name router --cap-add NET_ADMIN -e PYTHONUNBUFFERED=1 router
echo "Container router executed."

# attach router to client and server networks

docker network connect --ip 10.0.10.254 clients router
docker network connect --ip 10.0.11.254 servers router

docker run -d --rm --name mcproxy --cap-add NET_ADMIN -e PYTHONUNBUFFERED=1 router
echo "Container mcproxy executed."

docker network connect --ip 10.0.11.253 servers mcproxy
docker network connect --ip 10.0.10.253 clients mcproxy

echo "Container router connected to client and server networks."

docker run --rm -d --network servers  --name server1 --cap-add NET_ADMIN -p 65444:65433 -v C:\Roger\feo\Distributed-Agenda\server\backend\app:/app chord-server
echo "Server1 created."

docker run --rm -d --network servers  --name server2 --cap-add NET_ADMIN -p 65445:65434 -v C:\Roger\feo\Distributed-Agenda\server\backend\app:/app chord-server
echo "Server2 created."

docker run --rm -d --network servers  --name server3 --cap-add NET_ADMIN -p 65446:65435 -v C:\Roger\feo\Distributed-Agenda\server\backend\app:/app chord-server
echo "Server3 created."

docker run --rm -d --network clients  --name client1 --cap-add NET_ADMIN -p 8080:3000 -v C:\Roger\feo\Distributed-Agenda\client:/app client
echo Client1 created.