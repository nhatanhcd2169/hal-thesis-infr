echo "STARTING . . ."

bash network.sh
bash pg.sh
bash bootstrap.sh
bash kong.sh
bash konga.sh