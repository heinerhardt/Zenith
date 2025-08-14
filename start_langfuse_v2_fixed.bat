@echo off
echo ============================================
echo Starting Langfuse v2 with Migration Fix
echo ============================================

echo.
echo Step 1: Stopping and removing any existing containers...
docker stop langfuse-server langfuse-postgres 2>nul
docker rm langfuse-server langfuse-postgres 2>nul

echo.
echo Step 2: Removing any existing Langfuse images...
docker rmi langfuse/langfuse:latest 2>nul
docker rmi langfuse/langfuse:2 2>nul

echo.
echo Step 3: Pulling specific Langfuse v2 image...
docker pull langfuse/langfuse:2.70.0

echo.
echo Step 4: Creating Docker network...
docker network create langfuse-net 2>nul

echo.
echo Step 5: Starting PostgreSQL database...
docker run -d ^
  --name langfuse-postgres ^
  --network langfuse-net ^
  -e POSTGRES_DB=langfuse ^
  -e POSTGRES_USER=langfuse ^
  -e POSTGRES_PASSWORD=langfuse ^
  -p 5432:5432 ^
  -v langfuse_postgres_data:/var/lib/postgresql/data ^
  --restart unless-stopped ^
  postgres:13

echo Waiting for PostgreSQL to start...
timeout /t 15 /nobreak

echo.
echo Step 6: Starting Langfuse v2 server with migration settings...
docker run -d ^
  --name langfuse-server ^
  --network langfuse-net ^
  -e DATABASE_URL=postgresql://langfuse:langfuse@langfuse-postgres:5432/langfuse ^
  -e NEXTAUTH_SECRET=your-secret-key-change-in-production ^
  -e SALT=your-salt-key-change ^
  -e TELEMETRY_ENABLED=false ^
  -e NEXTAUTH_URL=http://localhost:3000 ^
  -e CLICKHOUSE_MIGRATION_URL= ^
  -e LANGFUSE_ENABLE_EXPERIMENTAL_FEATURES=false ^
  -e NODE_ENV=production ^
  -p 3000:3000 ^
  --restart unless-stopped ^
  langfuse/langfuse:2.70.0

echo.
echo Step 7: Waiting for Langfuse to start...
timeout /t 20 /nobreak

echo.
echo Step 8: Checking container status...
echo.
docker ps --filter "name=langfuse"

echo.
echo Step 9: Checking Langfuse logs for any errors...
echo.
docker logs langfuse-server --tail=15

echo.
echo ============================================
echo Setup Complete!
echo ============================================
echo.
echo Langfuse should be available at: http://localhost:3000
echo.
echo If you still see ClickHouse errors, try:
echo 1. docker logs langfuse-server (to see detailed logs)
echo 2. Use the alternative v2.50.0 version (run start_langfuse_v2_50.bat)
echo.
echo Next steps:
echo 1. Open http://localhost:3000 in your browser
echo 2. Create an admin account
echo 3. Create a project named 'zenith-pdf-chatbot'
echo 4. Go to Settings and create API keys
echo 5. Update your .env file with the keys
echo.
pause
