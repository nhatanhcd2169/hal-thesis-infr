mkdir -p config/kibana
docker compose -f kibana.docker-compose.yml run --rm kibana bin/kibana-encryption-keys generate > config/kibana/encrypt.txt
python3 parse.py