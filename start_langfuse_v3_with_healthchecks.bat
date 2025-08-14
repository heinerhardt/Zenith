@echo off
echo ============================================
echo Starting Langfuse v3 with ClickHouse and Healthchecks
echo ============================================

echo.
echo This will start Langfuse v3 with both PostgreSQL and ClickHouse.
echo The healthchecks will ensure proper startup order.
echo.

echo Step 1: Stopping any existing Langfuse containers...
docker-compose -f docker-compose.langfuse.yml down 2>nul
docker-compose -f docker-compose.langfuse-simple.yml down 2>nul
docker-compose -f docker-compose.langfuse-v3.yml down 2>nul

echo.
echo Step 2: Cleaning up any orphaned containers...
docker container prune -f

echo.
echo Step 3: Starting Langfuse v3 with healthchecks...
echo This may take a few minutes as services wait for each other to be ready.
docker-compose -f docker-compose.langfuse-v3.yml up -d

echo.
echo Step 4: Monitoring startup progress...
echo.
echo Waiting for PostgreSQL to be healthy...
:wait_postgres
docker-compose -f docker-compose.langfuse-v3.yml ps db | find "healthy" >nul
if errorlevel 1 (
    echo PostgreSQL still starting...
    timeout /t 5 /nobreak >nul
    goto wait_postgres
)
echo PostgreSQL is healthy!

echo.
echo Waiting for ClickHouse to be healthy...
:wait_clickhouse
docker-compose -f docker-compose.langfuse-v3.yml ps clickhouse | find "healthy" >nul
if errorlevel 1 (
    echo ClickHouse still starting...
    timeout /t 5 /nobreak >nul
    goto wait_clickhouse
)
echo ClickHouse is healthy!

echo.
echo Waiting for Langfuse server to start...
timeout /t 10 /nobreak

echo.
echo Step 5: Checking final status...
docker-compose -f docker-compose.langfuse-v3.yml ps

echo.
echo Step 6: Checking service health...
echo.
echo PostgreSQL status:
docker exec zenith_db_1 pg_isready -U langfuse -d langfuse 2>nul || echo "PostgreSQL not accessible"

echo.
echo ClickHouse status:
curl -s http://localhost:8123/ping 2>nul || echo "ClickHouse not accessible via HTTP"

echo.
echo Langfuse status:
curl -s -o nul -w "HTTP Status: %%{http_code}" http://localhost:3000 2>nul || echo "Langfuse not accessible"

echo.
echo.
echo ============================================
echo Langfuse v3 Setup Complete!
echo ============================================
echo.
echo Services available:
echo - Langfuse UI: http://localhost:3000
echo - PostgreSQL: localhost:5432
echo - ClickHouse HTTP: http://localhost:8123
echo - ClickHouse Native: localhost:9000
echo.
echo Features with v3:
echo - Advanced analytics with ClickHouse
echo - Better performance for large datasets
echo - Enhanced observability features
echo.
echo Next steps:
echo 1. Open http://localhost:3000
echo 2. Create admin account
echo 3. Create project: 'zenith-pdf-chatbot'
echo 4. Get API keys from Settings
echo 5. Update .env with keys
echo.
pause
