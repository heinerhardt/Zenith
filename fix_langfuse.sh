#!/bin/bash
# Script to fix and restart Langfuse

echo "Stopping current Langfuse containers..."
docker-compose -f docker-compose.langfuse.yml down

echo "Removing any orphaned containers..."
docker container prune -f

echo "Pulling Langfuse v2 image..."
docker pull langfuse/langfuse:2

echo "Starting Langfuse v2 with PostgreSQL..."
docker-compose -f docker-compose.langfuse.yml up -d

echo "Waiting for services to start..."
sleep 15

echo "Checking container status..."
docker-compose -f docker-compose.langfuse.yml ps

echo "Checking logs..."
docker-compose -f docker-compose.langfuse.yml logs --tail=20

echo "Langfuse should be available at: http://localhost:3000"
