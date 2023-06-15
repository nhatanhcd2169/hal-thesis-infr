echo "STOPPING . . ."

docker container stop kong-database
docker container stop kong-gateway
docker container stop konga