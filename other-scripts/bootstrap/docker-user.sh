echo "DOCKER USERING . . ."

sudo groupadd docker
sudo usermod -aG docker ubuntu
newgrp docker
docker run hello-world