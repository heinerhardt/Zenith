@echo off
REM Zenith AI Chat - Simplified Enterprise Startup Script (Windows)
REM Auto-detects setup state and runs appropriate mode

setlocal enabledelayedexpansion

REM Configuration variables
set "SCRIPT_DIR=%~dp0"
set "STARTUP_LOG=%SCRIPT_DIR%data\logs\startup.log"
set "ENTERPRISE_MARKER=%SCRIPT_DIR%data\enterprise\.enterprise_configured"
set "port=8501"

REM Parse command line arguments
:parse_args
if "%~1"=="" goto args_done
if "%~1"=="--help" goto show_help
if "%~1" neq "" (
    REM Check if argument contains equals sign
    echo.%~1 | findstr /C:"=" >nul 2>&1
    if not errorlevel 1 (
        REM Parse argument with equals sign
        for /f "tokens=1,2 delims==" %%a in ("%~1") do (
            if "%%a"=="--port" (
                set "port=%%b"
                call :log "DEBUG" "Port set to: %%b"
            )
        )
    ) else (
        REM Handle arguments without equals sign
        echo Unknown argument: %~1
    )
    shift
    goto parse_args
)
:args_done

REM Create required directories
if not exist "%SCRIPT_DIR%data\logs" mkdir "%SCRIPT_DIR%data\logs" 2>nul
if not exist "%SCRIPT_DIR%data\enterprise" mkdir "%SCRIPT_DIR%data\enterprise" 2>nul

REM Initialize log file
echo. > "%STARTUP_LOG%" 2>nul

REM Print banner
call :print_banner

REM Detect Python executable
call :detect_python_executable

REM System requirements check
call :check_system_requirements
if errorlevel 1 (
    call :log "ERROR" "System requirements not met"
    goto error_exit
)

REM Setup virtual environment
call :setup_virtual_environment

REM Ensure Python dependencies are available
call :ensure_python_dependencies

REM Smart startup logic - Check enterprise setup state
call :log "INFO" "Checking enterprise setup status..."

if exist "%ENTERPRISE_MARKER%" (
    call :log "INFO" "Enterprise setup detected - Starting in Production Mode"
    call :start_production_mode
) else (
    call :log "INFO" "No enterprise setup found - Running interactive setup"
    call :run_interactive_setup
    if not errorlevel 1 (
        echo.
        call :log "INFO" "Setup completed - Starting in Production Mode"
        call :start_production_mode
    ) else (
        call :log "ERROR" "Setup failed"
        goto error_exit
    )
)

goto normal_exit

:show_help
    echo Usage: %~n0 [OPTIONS]
    echo Options:
    echo   --port=PORT          Set application port (default: 8501)
    echo   --help              Show this help message
    echo.
    echo Zenith AI automatically detects setup state:
    echo   - If enterprise setup is not complete: Runs interactive setup
    echo   - If enterprise setup is complete: Starts in Production Mode
    goto normal_exit

:print_banner
    echo.
    echo ===============================================
    echo    🚀 Zenith AI - Enterprise Startup
    echo ===============================================
    echo.
    goto :eof

:run_interactive_setup
    call :log "INFO" "Starting interactive enterprise setup..."
    
    %PYTHON_CMD% run_interactive_setup.py
    
    if errorlevel 1 (
        call :log "ERROR" "Interactive setup failed"
        exit /b 1
    ) else (
        call :log "INFO" "Interactive setup completed successfully"
        exit /b 0
    )

:start_production_mode
    call :log "INFO" "Starting in Production Mode..."
    
    REM Run quick health check
    call :run_health_check
    if errorlevel 1 (
        call :log "WARN" "Some health checks failed, but continuing..."
    )
    
    REM Start application
    call :start_application "production" "%port%"
    goto :eof

:check_system_requirements
    call :log "INFO" "Checking system requirements..."
    
    REM Check if we're in the right directory
    if not exist "src\ui\simple_chat_app.py" (
        call :log "ERROR" "simple_chat_app.py not found!"
        call :log "ERROR" "Please run this script from the Zenith project root directory."
        exit /b 1
    )
    
    REM Check Python version
    %PYTHON_CMD% -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>&1
    if errorlevel 1 (
        call :log "ERROR" "Python 3.9+ required"
        exit /b 1
    )
    
    call :log "INFO" "System requirements check passed"
    exit /b 0

:detect_python_executable
    REM Try to find the best Python executable on Windows
    set "PYTHON_CMD="
    
    REM Try 'py' first (Python Launcher - most reliable on Windows)
    py --version >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_CMD=py"
        goto python_found
    )
    
    REM Check for Python executable in default Windows paths
    if exist "%ProgramFiles%\Python313\python.exe" (
        set "PYTHON_CMD=%ProgramFiles%\Python313\python.exe"
        goto python_found
    )
    if exist "%ProgramFiles(x86)%\Python313\python.exe" (
        set "PYTHON_CMD=%ProgramFiles(x86)%\Python313\python.exe"
        goto python_found
    )
    
    REM Try 'python3'
    python3.exe --version >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_CMD=python3.exe"
        goto python_found
    )
    
    REM Try 'python'
    python.exe --version >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_CMD=python.exe"
        goto python_found
    )
    
    REM If none work, default to 'py' and let it fail with proper error
    set "PYTHON_CMD=py"
    
    :python_found
    call :log "INFO" "Using Python executable: %PYTHON_CMD%"
    goto :eof

:setup_virtual_environment
    if exist "venv\Scripts\activate.bat" (
        call :log "INFO" "Activating virtual environment..."
        call venv\Scripts\activate.bat
        if errorlevel 1 (
            call :log "WARN" "Failed to activate virtual environment, using system Python"
        ) else (
            call :log "INFO" "Virtual environment activated successfully"
            REM Update Python command to use activated environment
            set "PYTHON_CMD=python"
        )
    ) else (
        call :log "WARN" "Virtual environment not found, using system Python"
        call :log "INFO" "Consider creating a virtual environment: %PYTHON_CMD% -m venv venv"
    )
    goto :eof

:check_python_dependencies
    call :log "INFO" "Checking Python dependencies..."
    
    REM Check critical dependencies
    set "missing_deps="
    
    %PYTHON_CMD% -c "import streamlit" >nul 2>&1
    if errorlevel 1 set "missing_deps=%missing_deps% streamlit"
    
    %PYTHON_CMD% -c "import langchain" >nul 2>&1
    if errorlevel 1 set "missing_deps=%missing_deps% langchain"
    
    %PYTHON_CMD% -c "import qdrant_client" >nul 2>&1
    if errorlevel 1 set "missing_deps=%missing_deps% qdrant_client"
    
    %PYTHON_CMD% -c "import openai" >nul 2>&1
    if errorlevel 1 set "missing_deps=%missing_deps% openai"
    
    %PYTHON_CMD% -c "import loguru" >nul 2>&1
    if errorlevel 1 set "missing_deps=%missing_deps% loguru"
    
    if "%missing_deps%"=="" (
        call :log "INFO" "All critical dependencies are available"
        exit /b 0
    ) else (
        call :log "WARN" "Missing dependencies:%missing_deps%"
        exit /b 1
    )

:install_python_dependencies
    call :log "INFO" "Installing Python dependencies..."
    
    if not exist "requirements.txt" (
        call :log "ERROR" "requirements.txt not found!"
        exit /b 1
    )
    
    echo.
    echo 📦 Installing dependencies from requirements.txt...
    echo This may take a few minutes on first run.
    echo.
    
    REM Upgrade pip first
    %PYTHON_CMD% -m pip install --upgrade pip >nul 2>&1
    if not errorlevel 1 call :log "INFO" "pip upgraded successfully"
    
    REM Install dependencies
    %PYTHON_CMD% -m pip install -r requirements.txt --quiet --no-warn-script-location
    if errorlevel 1 (
        call :log "ERROR" "Failed to install some dependencies"
        call :log "INFO" "You may need to install them manually with: pip install -r requirements.txt"
        exit /b 1
    ) else (
        call :log "INFO" "Dependencies installed successfully"
        echo.
        exit /b 0
    )

:ensure_python_dependencies
    call :check_python_dependencies
    if errorlevel 1 (
        echo.
        if "%interactive%"=="true" (
            set /p "install_deps=Install missing dependencies automatically? (y/n): "
            if /i "!install_deps!"=="y" (
                call :install_python_dependencies
                if not errorlevel 1 (
                    call :log "INFO" "Dependencies installed. Verifying..."
                    call :check_python_dependencies
                    if errorlevel 1 call :log "WARN" "Some dependencies may still be missing"
                )
            ) else (
                call :log "WARN" "Proceeding with potentially missing dependencies"
                call :log "INFO" "Install them manually with: pip install -r requirements.txt"
            )
        ) else (
            call :log "INFO" "Non-interactive mode: Installing dependencies automatically..."
            call :install_python_dependencies
        )
        echo.
    )
    goto :eof

:check_enterprise_setup
    if exist "%ENTERPRISE_MARKER%" (
        call :log "INFO" "Enterprise setup detected"
        exit /b 0
    ) else (
        call :log "WARN" "Enterprise setup not found"
        exit /b 1
    )

:run_enterprise_setup
    call :log "INFO" "Starting enterprise setup..."
    
    %PYTHON_CMD% run_enterprise_setup.py
    
    if errorlevel 1 (
        call :log "ERROR" "Enterprise setup failed"
        exit /b 1
    ) else (
        call :log "INFO" "Enterprise setup completed successfully"
        exit /b 0
    )

:run_health_check
    call :log "INFO" "Running comprehensive health check..."
    
    set "health_passed=true"
    
    REM System health check
    %PYTHON_CMD% main.py info >nul 2>&1
    if errorlevel 1 (
        call :log "ERROR" "Basic system health check failed"
        set "health_passed=false"
    )
    
    REM Enterprise components health check
    if exist "%ENTERPRISE_MARKER%" (
        %PYTHON_CMD% -c "import sys; sys.path.insert(0, 'src'); from setup.enterprise_setup import check_enterprise_setup_status; status = check_enterprise_setup_status(); sys.exit(0 if status.get('is_complete', False) else 1)" >nul 2>&1
        if errorlevel 1 (
            call :log "ERROR" "Enterprise components health check failed"
            set "health_passed=false"
        ) else (
            call :log "INFO" "Enterprise components health check passed"
        )
    )
    
    REM Database connectivity
    if exist "%ENTERPRISE_MARKER%" (
        set "db_path=./data/enterprise/zenith.db"
    ) else (
        set "db_path=./data/zenith.db"
    )
    
    %PYTHON_CMD% -c "import sqlite3; conn = sqlite3.connect('%db_path%'); conn.execute('SELECT 1'); conn.close()" >nul 2>&1
    if errorlevel 1 (
        call :log "WARN" "Database connectivity check failed (may be first run)"
    ) else (
        call :log "INFO" "Database connectivity check passed"
    )
    
    REM Qdrant connectivity
    %PYTHON_CMD% -c "import requests; response = requests.get('http://localhost:6333/health', timeout=5); exit(0 if response.status_code == 200 else 1)" >nul 2>&1
    if errorlevel 1 (
        call :log "WARN" "Qdrant not accessible (start with: docker-compose up -d qdrant)"
    ) else (
        call :log "INFO" "Qdrant connectivity check passed"
    )
    
    if "%health_passed%"=="true" (
        call :log "INFO" "All health checks passed"
        exit /b 0
    ) else (
        call :log "ERROR" "Some health checks failed"
        exit /b 1
    )

:start_application
    set "app_mode=%~1"
    set "app_port=%~2"
    if "%app_port%"=="" set "app_port=8501"
    
    REM Use enhanced interface if enterprise setup is complete
    if exist "%ENTERPRISE_MARKER%" (
        set "interface=src\ui\enhanced_streamlit_app.py"
        set "ZENITH_ENV=production"
    ) else (
        set "interface=src\ui\simple_chat_app.py"
    )
    
    echo.
    call :log "INFO" "Application starting on http://localhost:%app_port%"
    
    if exist "%ENTERPRISE_MARKER%" (
        echo ✅ Enterprise features enabled
        echo ✅ Admin login required
    ) else (
        echo ⚠️  Demo admin login is automatically enabled
    )
    
    echo 💡 Press Ctrl+C to stop the application
    echo.
    
    REM Start the Streamlit application
    %PYTHON_CMD% -m streamlit run "%interface%" --server.port %app_port% --server.headless true
    goto :eof

:handle_reset_mode
    echo.
    call :log "WARN" "Reset Mode - This will reset system data!"
    echo ⚠️  WARNING: This will delete all user data and configurations!
    echo.
    
    set /p "confirm=Are you sure you want to proceed? (type 'RESET' to confirm): "
    
    if not "%confirm%"=="RESET" (
        call :log "INFO" "Reset cancelled by user"
        goto :eof
    )
    
    call :log "INFO" "Creating backup before reset..."
    
    REM Create backup
    for /f "tokens=1-4 delims=/ " %%a in ('date /t') do set "backup_date=%%c%%a%%b"
    for /f "tokens=1-2 delims=: " %%a in ('time /t') do set "backup_time=%%a%%b"
    set "backup_dir=.\data\backups\%backup_date%_%backup_time%_pre_reset"
    
    if exist ".\data" (
        mkdir "%backup_dir%" 2>nul
        xcopy ".\data\*" "%backup_dir%\" /s /e /q >nul 2>&1
        call :log "INFO" "Backup created at: %backup_dir%"
    )
    
    REM Perform reset
    call :log "INFO" "Performing system reset..."
    
    REM Remove enterprise marker
    if exist "%ENTERPRISE_MARKER%" del "%ENTERPRISE_MARKER%" >nul 2>&1
    
    REM Remove databases
    for /r ".\data" %%f in (*.db) do del "%%f" >nul 2>&1
    
    REM Remove configuration files
    for /r ".\data" %%f in (*.json *.yaml) do del "%%f" >nul 2>&1
    
    call :log "INFO" "System reset completed"
    call :log "INFO" "Backup available at: %backup_dir%"
    
    echo.
    set /p "setup_now=Do you want to run enterprise setup now? (y/n): "
    if /i "%setup_now%"=="y" (
        call :run_enterprise_setup
    )
    goto :eof

:log
    set "log_level=%~1"
    set "log_message=%~2"
    set "timestamp=%date% %time%"
    
    echo [%timestamp%] [%log_level%] %log_message% >> "%STARTUP_LOG%" 2>nul
    
    if "%log_level%"=="ERROR" echo ❌ %log_message%
    if "%log_level%"=="WARN" echo ⚠️  %log_message%
    if "%log_level%"=="INFO" echo ✅ %log_message%
    if "%log_level%"=="DEBUG" echo 🔍 %log_message%
    goto :eof

:error_exit
    echo.
    call :log "ERROR" "Startup failed"
    if "%interactive%"=="true" pause
    exit /b 1

:normal_exit
    echo.
    call :log "INFO" "👋 Zenith AI Chat stopped."
    if "%interactive%"=="true" pause
    exit /b 0