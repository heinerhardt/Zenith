@echo off
echo ============================================
echo Cleaning up and restarting Langfuse
echo ============================================

echo.
echo Step 1: Stopping all containers...
docker-compose -f docker-compose.langfuse.yml down
docker-compose -f docker-compose.langfuse-simple.yml down 2>nul

echo.
echo Step 2: Removing containers and networks...
docker stop langfuse-server langfuse-postgres db-1 zenith_langfuse-server_1 zenith_db_1 2>nul
docker rm langfuse-server langfuse-postgres db-1 zenith_langfuse-server_1 zenith_db_1 2>nul

echo.
echo Step 3: Removing problematic volumes (this will delete existing data)...
docker volume rm langfuse_postgres_data 2>nul
docker volume rm zenith_langfuse_postgres_data 2>nul
docker volume rm postgres_data 2>nul
docker volume rm langfuse_data 2>nul
docker volume rm zenith_langfuse_data 2>nul

echo.
echo Step 4: Removing networks...
docker network rm langfuse_network 2>nul
docker network rm zenith_default 2>nul
docker network rm langfuse-net 2>nul

echo.
echo Step 5: Cleaning up any orphaned containers and volumes...
docker system prune -f
docker volume prune -f

echo.
echo Step 6: Starting fresh with simple Docker commands...
docker network create langfuse-net

echo.
echo Step 7: Starting PostgreSQL with fresh volume...
docker run -d ^
  --name langfuse-postgres ^
  --network langfuse-net ^
  -e POSTGRES_DB=langfuse ^
  -e POSTGRES_USER=langfuse ^
  -e POSTGRES_PASSWORD=langfuse ^
  -p 5432:5432 ^
  --restart unless-stopped ^
  postgres:13

echo.
echo Waiting for PostgreSQL to fully initialize...
timeout /t 20 /nobreak

echo.
echo Step 8: Starting Langfuse server...
docker run -d ^
  --name langfuse-server ^
  --network langfuse-net ^
  -e DATABASE_URL=postgresql://langfuse:langfuse@langfuse-postgres:5432/langfuse ^
  -e CLICKHOUSE_MIGRATION_URL= ^
  -e NEXTAUTH_SECRET=your-secret-key-change-in-production ^
  -e SALT=your-salt-key-change ^
  -e TELEMETRY_ENABLED=false ^
  -e NEXTAUTH_URL=http://localhost:3000 ^
  -p 3000:3000 ^
  --restart unless-stopped ^
  langfuse/langfuse:2

echo.
echo Step 9: Waiting for Langfuse to start...
timeout /t 15 /nobreak

echo.
echo Step 10: Checking status...
docker ps --filter "name=langfuse"

echo.
echo Step 11: Checking logs...
echo.
echo PostgreSQL logs:
docker logs langfuse-postgres --tail=5
echo.
echo Langfuse logs:
docker logs langfuse-server --tail=5

echo.
echo ============================================
echo Fresh Setup Complete!
echo ============================================
echo.
echo Langfuse should be available at: http://localhost:3000
echo.
echo If you still see issues, the logs above will help identify the problem.
echo.
pause
