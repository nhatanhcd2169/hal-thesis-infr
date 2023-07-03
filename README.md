# HAL-Thesis

<b>Collaborators</b>:
- Huynh Nhat Long       -       1852522
- Ta Gia Hung           -       1852433
- Nguyen Nhat Anh       -       1852236

<b>Prequisite</b>: docker, docker-compose

<b>Steps to run</b>:

1) Open terminal in current folder
2) `cp .env.example .env`
3) `nano .env` to edit environment variables
4) Run `docker network create thesis_kong-network` to create network
5) Run `bash start-kong.sh` to start containers
6) Run `bash stop-kong.sh` to stop the containers


Steps to run ELK:

1) Run `sudo apt -y install firewalld` to install firewall-cmd
2) Run `sudo systemctl enable firewalld`
3) Run `sudo firewall-cmd --state` to return state of firewall-cmd
4) Run `sudo firewall-cmd --add-port=9200/tcp --permanent
        sudo firewall-cmd --add-port=5601/tcp --permanent 
        sudo firewall-cmd --add-port=9600/tcp --permanent
        sudo firewall-cmd --add-port=9300/tcp --permanent
        sudo firewall-cmd --reload` to turn off firewall


<b>Important note</b>: 
- When prompted to add Kong Admin connection in Konga, use container name + port 8001, not 8002 (e.g: `http://gateway:8001`)
- When registering a containerized service in the same machine, use `http://host.docker.internal:<port>`, not `localhost`
- ELK stack currently runs in HTTP security (no SSL encryption), which we will implement later
- Analytics on Kong logs are still pending
- Internal visualization is still pending
