@echo off

rem check clients docker networks existence

docker network inspect clients > nul 2>&1
if %errorlevel% equ 0 (
    echo Network clients exists.
) else (
    docker network create clients --subnet 10.0.10.0/24
    echo Network clients created.
)

rem check servers docker network existence 

docker network inspect servers > nul 2>&1
if %errorlevel% equ 0 (
    echo Network servers exists.
) else (
    docker network create servers --subnet 10.0.11.0/24
    echo Network servers created.
)

rem check router:base docker image existence 

docker image inspect router:base > nul 2>&1
if %errorlevel% equ 0 (
    echo Image router:base exists.
) else (
    docker build -t router:base -f router/router_base.Dockerfile router/
    echo Image router:base created.
)

rem check router docker image existence 

docker image inspect router > nul 2>&1
if %errorlevel% equ 0 (
    echo Image router exists.
) else (
    docker build -t router -f router/router.Dockerfile router/
    echo Image router created.
)

rem check router container existence

docker container inspect router > nul 2>&1
if %errorlevel% equ 0 (
    docker container stop router
    docker container rm router
    echo Container router removed.
)

docker run -d --rm --name router --cap-add NET_ADMIN -e PYTHONUNBUFFERED=1 -v C:\Roger\feo\Distributed-Agenda\router:/root router
echo Container router executed.

docker network connect --ip 10.0.10.254 clients router
docker network connect --ip 10.0.11.254 servers router

docker run -d --rm --name mcproxy --cap-add NET_ADMIN -e PYTHONUNBUFFERED=1 -v C:\Roger\feo\Distributed-Agenda\router:/root router
echo Container router executed.

docker network connect --ip 10.0.11.253 servers mcproxy
docker network connect --ip 10.0.10.253 clients mcproxy

echo Container router connected to client and server networks

docker exec -d mcproxy root/route.sh

docker run --rm -d --network servers  --name server1 --cap-add NET_ADMIN -p 65444:65433 -v C:\Roger\feo\Distributed-Agenda\server\backend\app:/app chord-server
echo Server1 created.

docker exec -d server1 ./backend.sh

docker run --rm -d --network servers  --name server2 --cap-add NET_ADMIN -p 65445:65434 -v C:\Roger\feo\Distributed-Agenda\server\backend\app:/app chord-server
echo Server2 created.

docker exec -d server2 ./backend.sh

@REM docker run --rm -d --network servers  --name server3 --cap-add NET_ADMIN -p 65446:65435 -v C:\Roger\feo\Distributed-Agenda\server\backend\app:/app chord-server
@REM echo Server3 created.

@REM docker run --rm -d --network servers  --name server4 --cap-add NET_ADMIN -p 65447:65436 -v C:\Roger\feo\Distributed-Agenda\server\backend\app:/app chord-server
@REM echo Server4 created.

@REM docker run --rm -d --network servers  --name server5 --cap-add NET_ADMIN -p 65448:65437 -v C:\Roger\feo\Distributed-Agenda\server\backend\app:/app chord-server
@REM echo Server5 created.

docker run -it --rm -d --network clients  --name client1 --cap-add NET_ADMIN -p 8080:3000 -p 8000:8000 -v C:\Roger\feo\Distributed-Agenda\client\:/app client
echo client1 created.

docker exec -d client1 ./client.sh
