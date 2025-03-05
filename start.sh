#!/bin/bash

echo "[>] Starting Deployment..."

compose_file=docker-compose.yml
protected_volume="postgres_data"

echo "[+] Stopping and removing containers, networks, and orphans related to the compose file..."
docker compose down --remove-orphans

echo "[+] Removing dangling images (unused by any container)..."
docker image prune --force

echo "[+] Removing unused networks..."
docker network prune --force

echo "[+] Removing unused volumes except for $protected_volume..."
docker volume ls -q | grep -v "$protected_volume" | xargs -r docker volume rm

echo "[+] Pulling the latest images..."
docker compose pull

echo "[+] Starting new container using docker compose..."
docker compose up 

if [[ $? -eq 0 ]]; then
    echo "[✔] Deployment successful!"
else
    echo "[!] Failed to start the container."
    exit 1
fi