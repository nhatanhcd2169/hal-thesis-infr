# HAL-Thesis

<b>Collaborators</b>:
- Huynh Nhat Long
- Ta Gia Hung
- Nguyen Nhat Anh

<b>Important note</b>: When prompted to add Kong Admin connection in Konga, use container name + port 8001, not 8002 (e.g: `http://gateway:8001`)

<b>Prequisite</b>: docker, docker-compose

<b>Steps to run</b>:

1) Open terminal in current folder
2) `cp .env.example .env`
3) `nano .env` to edit environment variables
4) Run `bash start-kong.sh` to start containers
5) Run `bash stop-kong.sh` to stop the containers
