@echo off
echo Stopping Langfuse containers...

docker stop langfuse-server langfuse-postgres
docker rm langfuse-server langfuse-postgres

echo.
echo Langfuse containers stopped and removed.
echo.
echo To completely clean up (WARNING: This will delete all data):
echo docker volume rm langfuse_postgres_data
echo docker network rm langfuse-net
echo.
pause
