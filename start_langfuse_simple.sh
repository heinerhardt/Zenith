#!/bin/bash

echo "============================================"
echo "Starting Langfuse with Direct Docker Commands"
echo "============================================"

echo
echo "Step 1: Stopping any existing containers..."
docker stop langfuse-server langfuse-postgres 2>/dev/null
docker rm langfuse-server langfuse-postgres 2>/dev/null

echo
echo "Step 2: Creating Docker network..."
docker network create langfuse-net 2>/dev/null

echo
echo "Step 3: Starting PostgreSQL database..."
docker run -d \
  --name langfuse-postgres \
  --network langfuse-net \
  -e POSTGRES_DB=langfuse \
  -e POSTGRES_USER=langfuse \
  -e POSTGRES_PASSWORD=langfuse \
  -p 5432:5432 \
  -v langfuse_postgres_data:/var/lib/postgresql/data \
  --restart unless-stopped \
  postgres:13

echo "Waiting for PostgreSQL to start..."
sleep 10

echo
echo "Step 4: Starting Langfuse server..."
docker run -d \
  --name langfuse-server \
  --network langfuse-net \
  -e DATABASE_URL=postgresql://langfuse:langfuse@langfuse-postgres:5432/langfuse \
  -e NEXTAUTH_SECRET=your-secret-key-change-in-production \
  -e SALT=your-salt-key \
  -e TELEMETRY_ENABLED=false \
  -e NEXTAUTH_URL=http://localhost:3000 \
  -p 3000:3000 \
  --restart unless-stopped \
  langfuse/langfuse:2

echo
echo "Step 5: Waiting for Langfuse to start..."
sleep 15

echo
echo "Step 6: Checking container status..."
echo
docker ps --filter "name=langfuse"

echo
echo "Step 7: Checking logs..."
echo
docker logs langfuse-server --tail=10

echo
echo "============================================"
echo "Setup Complete!"
echo "============================================"
echo
echo "Langfuse should be available at: http://localhost:3000"
echo
echo "Default login will be created on first visit:"
echo "- Create your own admin account"
echo "- Or use any email/password you want"
echo
echo "Next steps:"
echo "1. Open http://localhost:3000 in your browser"
echo "2. Create an admin account"
echo "3. Create a project named 'zenith-pdf-chatbot'"
echo "4. Go to Settings and create API keys"
echo "5. Update your .env file with the keys"
echo
