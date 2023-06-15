docker container stop konga
docker container rm konga
docker run -d --name konga \
    --network kong-net \
    -e "TOKEN_SECRET=2169" \
    -e "DB_ADAPTER=postgres" \
    -e "DB_HOST=127.0.0.1" \
    -e "DB_PORT=5432" \
    -e "DB_USER=kong" \
    -e "DB_PASSWORD=kongpass" \
    -e "DB_DATABASE=postgres" \
    -e "NODE_ENV=development" \
    -p 1337:1337 \
    pantsel/konga