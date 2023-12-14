#!/bin/bash

# Build the Docker images
echo "Building telegram-listener..."
docker build -t telegram-listener -f bot/telegram/Dockerfile .

echo "Building to-user-listener..."
docker build -t to-user-listener -f bot/listeners/to_user/Dockerfile .

echo "Building from-user-listener..."
docker build -t from-user-listener -f bot/listeners/from_user/Dockerfile .

echo "Docker builds complete."