docker container stop konga
docker container rm konga
docker run -d -p 1337:1337 \
    --network kong-net \
    -e "TOKEN_SECRET=2169" \
    -e "DB_ADAPTER=postgres" \
    -e "DB_URI=postgres://kong:kongpass@kong-database:5433/postgres" \
    -e "NODE_ENV=development" \
    --name konga \
    pantsel/konga
