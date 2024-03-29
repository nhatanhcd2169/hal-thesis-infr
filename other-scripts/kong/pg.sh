echo "DATABASING . . ."

docker run -d --name kong-database \
  --network=kong-net \
  -p 5433:5432 \
  -e "POSTGRES_USER=kong" \
  -e "POSTGRES_DB=kong" \
  -e "POSTGRES_PASSWORD=kongpass" \
  postgres:13
