@echo off
echo ============================================
echo Alternative: Starting OpenLLMetry for Observability
echo ============================================
echo.
echo OpenLLMetry is a simpler alternative to Langfuse
echo that works with OpenTelemetry and is easier to set up.
echo.

echo Step 1: Stopping any existing containers...
docker stop openllmetry grafana prometheus 2>nul
docker rm openllmetry grafana prometheus 2>nul

echo.
echo Step 2: Creating Docker network...
docker network create observability-net 2>nul

echo.
echo Step 3: Starting Prometheus for metrics...
docker run -d ^
  --name prometheus ^
  --network observability-net ^
  -p 9090:9090 ^
  -v prometheus_data:/prometheus ^
  --restart unless-stopped ^
  prom/prometheus

echo.
echo Step 4: Starting Grafana for dashboards...
docker run -d ^
  --name grafana ^
  --network observability-net ^
  -p 3000:3000 ^
  -e GF_SECURITY_ADMIN_PASSWORD=admin ^
  -v grafana_data:/var/lib/grafana ^
  --restart unless-stopped ^
  grafana/grafana

echo.
echo Step 5: Starting OpenLLMetry collector...
docker run -d ^
  --name openllmetry ^
  --network observability-net ^
  -p 4317:4317 ^
  -p 4318:4318 ^
  -e PROMETHEUS_URL=http://prometheus:9090 ^
  --restart unless-stopped ^
  traceloop/openllmetry

echo.
echo Waiting for services to start...
timeout /t 15 /nobreak

echo.
echo Step 6: Checking container status...
docker ps --filter "network=observability-net"

echo.
echo ============================================
echo Alternative Setup Complete!
echo ============================================
echo.
echo Services available:
echo - Grafana Dashboard: http://localhost:3000 (admin/admin)
echo - Prometheus: http://localhost:9090
echo - OpenLLMetry: Listening on ports 4317/4318
echo.
echo To use this with your app, install:
echo pip install opentelemetry-api opentelemetry-sdk traceloop-sdk
echo.
echo This is much simpler than Langfuse and works great!
echo.
pause
