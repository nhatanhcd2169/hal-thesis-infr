echo "CLEANING . . ."

docker container rm kong-database
docker container rm kong-gateway
docker container rm konga