mkdir logs

touch logs/file.log

docker compose -f kong.docker-compose.yml -p kong up -d 