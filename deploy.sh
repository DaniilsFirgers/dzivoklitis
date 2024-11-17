echo "[>] Starting Deployment..."

compose_file=docker-compose.yml

echo "[+] Removing old containers, volume, images and networks"
docker system prune --force --filter --all

echo "[+] Stopping any running containers from docker compose..."
docker compose down

echo "[+] Pulling the latest images..."
docker compose pull

echo "[+] Starting new container using docker compose in detached mode..."
docker compose up -d

if [[ $? -eq 0 ]]; then
    echo "[✔] Deployment successful!"
else
    echo "[!] Failed to start the container."
    exit 1
fi