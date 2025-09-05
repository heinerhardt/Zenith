#!/bin/bash
# Zenith AI Chat - Enhanced Enterprise Startup Script (Linux/macOS)
# Supports enterprise setup, multi-mode startup, and comprehensive health checks

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Configuration variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STARTUP_LOG="${SCRIPT_DIR}/data/logs/startup.log"
ENTERPRISE_MARKER="${SCRIPT_DIR}/data/enterprise/.enterprise_configured"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" >> "$STARTUP_LOG" 2>/dev/null || true
    
    case "$level" in
        "ERROR") echo -e "${RED}❌ $message${NC}" ;;
        "WARN")  echo -e "${YELLOW}⚠️  $message${NC}" ;;
        "INFO")  echo -e "${GREEN}✅ $message${NC}" ;;
        "DEBUG") echo -e "${CYAN}🔍 $message${NC}" ;;
        *)       echo "$message" ;;
    esac
}

# Print banner
print_banner() {
    echo ""
    echo -e "${PURPLE}===============================================${NC}"
    echo -e "${PURPLE}   🚀 Zenith AI - Enterprise Startup${NC}"
    echo -e "${PURPLE}===============================================${NC}"
    echo ""
}

# Show startup menu
show_startup_menu() {
    echo -e "${CYAN}Select startup mode:${NC}"
    echo "1) 🏢 Production Mode (Enterprise)"
    echo "2) 🛠️  Development Mode (Enhanced)"
    echo "3) 🎭 Demo Mode (Sample Data)"
    echo "4) ⚙️  Setup Mode (First-time Configuration)"
    echo "5) 🔄 Reset Mode (System Reset)"
    echo "6) 📊 Health Check Only"
    echo "7) 🔧 Simple Mode (Legacy Interface)"
    echo ""
    
    while true; do
        read -p "Enter your choice (1-7): " choice
        case $choice in
            [1-7]) break ;;
            *) log "WARN" "Invalid choice. Please enter 1-7." ;;
        esac
    done
    
    echo "$choice"
}

# Check system requirements
check_system_requirements() {
    log "INFO" "Checking system requirements..."
    
    # Check if we're in the right directory
    if [ ! -f "src/ui/simple_chat_app.py" ]; then
        log "ERROR" "simple_chat_app.py not found!"
        log "ERROR" "Please run this script from the Zenith project root directory."
        return 1
    fi
    
    # Check Python version
    if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" 2>/dev/null; then
        log "ERROR" "Python 3.9+ required"
        return 1
    fi
    
    # Check disk space (require at least 500MB)
    available_space=$(df . | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 512000 ]; then
        log "WARN" "Low disk space detected (< 500MB available)"
    fi
    
    log "INFO" "System requirements check passed"
    return 0
}

# Setup virtual environment
setup_virtual_environment() {
    if [ -f "venv/bin/activate" ]; then
        log "INFO" "Activating virtual environment..."
        source venv/bin/activate
    else
        log "WARN" "Virtual environment not found, using system Python"
        log "INFO" "Consider creating a virtual environment: python3 -m venv venv"
    fi
}

# Check if critical Python dependencies are installed
check_python_dependencies() {
    log "INFO" "Checking Python dependencies..."
    
    # List of critical dependencies to check
    local critical_deps=("streamlit" "langchain" "qdrant_client" "openai" "loguru")
    local missing_deps=()
    
    for dep in "${critical_deps[@]}"; do
        if ! python -c "import $dep" >/dev/null 2>&1; then
            missing_deps+=("$dep")
        fi
    done
    
    if [ ${#missing_deps[@]} -eq 0 ]; then
        log "INFO" "All critical dependencies are available"
        return 0
    else
        log "WARN" "Missing dependencies: ${missing_deps[*]}"
        return 1
    fi
}

# Install Python dependencies from requirements.txt
install_python_dependencies() {
    log "INFO" "Installing Python dependencies..."
    
    if [ ! -f "requirements.txt" ]; then
        log "ERROR" "requirements.txt not found!"
        return 1
    fi
    
    echo ""
    echo -e "${YELLOW}📦 Installing dependencies from requirements.txt...${NC}"
    echo -e "${CYAN}This may take a few minutes on first run.${NC}"
    echo ""
    
    # Install with progress feedback
    if python -m pip install --upgrade pip >/dev/null 2>&1; then
        log "INFO" "pip upgraded successfully"
    fi
    
    if python -m pip install -r requirements.txt --quiet --no-warn-script-location; then
        log "INFO" "Dependencies installed successfully"
        echo ""
        return 0
    else
        log "ERROR" "Failed to install some dependencies"
        echo ""
        log "INFO" "You may need to install them manually with: pip install -r requirements.txt"
        return 1
    fi
}

# Ensure Python dependencies are available
ensure_python_dependencies() {
    if ! check_python_dependencies; then
        echo ""
        if [ "$interactive" = true ]; then
            read -p "Install missing dependencies automatically? (y/n): " install_deps
            if [[ "$install_deps" =~ ^[Yy]$ ]]; then
                install_python_dependencies
                if [ $? -eq 0 ]; then
                    log "INFO" "Dependencies installed. Verifying..."
                    if ! check_python_dependencies; then
                        log "WARN" "Some dependencies may still be missing"
                    fi
                fi
            else
                log "WARN" "Proceeding with potentially missing dependencies"
                log "INFO" "Install them manually with: pip install -r requirements.txt"
            fi
        else
            log "INFO" "Non-interactive mode: Installing dependencies automatically..."
            install_python_dependencies
        fi
        echo ""
    fi
}

# Check enterprise setup status
check_enterprise_setup() {
    if [ -f "$ENTERPRISE_MARKER" ]; then
        log "INFO" "Enterprise setup detected"
        return 0
    else
        log "WARN" "Enterprise setup not found"
        return 1
    fi
}

# Run enterprise setup
run_enterprise_setup() {
    log "INFO" "Starting enterprise setup..."
    
    if python run_enterprise_setup.py; then
        log "INFO" "Enterprise setup completed successfully"
        return 0
    else
        log "ERROR" "Enterprise setup failed"
        return 1
    fi
}

# Comprehensive health check
run_health_check() {
    log "INFO" "Running comprehensive health check..."
    
    local health_passed=true
    
    # System health check
    if ! python main.py info >/dev/null 2>&1; then
        log "ERROR" "Basic system health check failed"
        health_passed=false
    fi
    
    # Enterprise components health check
    if [ -f "$ENTERPRISE_MARKER" ]; then
        if python -c "
import sys
sys.path.insert(0, 'src')
try:
    from setup.enterprise_setup import check_enterprise_setup_status
    status = check_enterprise_setup_status()
    if not status.get('is_complete', False):
        sys.exit(1)
except Exception as e:
    print(f'Enterprise health check failed: {e}')
    sys.exit(1)
" >/dev/null 2>&1; then
            log "INFO" "Enterprise components health check passed"
        else
            log "ERROR" "Enterprise components health check failed"
            health_passed=false
        fi
    fi
    
    # Database connectivity
    if python -c "
import sqlite3
import sys
try:
    conn = sqlite3.connect('./data/zenith.db' if not '$ENTERPRISE_MARKER' else './data/enterprise/zenith.db')
    conn.execute('SELECT 1')
    conn.close()
except Exception:
    sys.exit(1)
" >/dev/null 2>&1; then
        log "INFO" "Database connectivity check passed"
    else
        log "WARN" "Database connectivity check failed (may be first run)"
    fi
    
    # Qdrant connectivity
    if python -c "
import requests
import sys
try:
    response = requests.get('http://localhost:6333/health', timeout=5)
    sys.exit(0 if response.status_code == 200 else 1)
except Exception:
    sys.exit(1)
" >/dev/null 2>&1; then
        log "INFO" "Qdrant connectivity check passed"
    else
        log "WARN" "Qdrant not accessible (start with: docker-compose up -d qdrant)"
    fi
    
    if [ "$health_passed" = true ]; then
        log "INFO" "All health checks passed"
        return 0
    else
        log "ERROR" "Some health checks failed"
        return 1
    fi
}

# Start application based on mode
start_application() {
    local mode="$1"
    local port="${2:-8501}"
    local interface="${3:-src/ui/simple_chat_app.py}"
    
    case "$mode" in
        "production")
            log "INFO" "Starting in Production Mode..."
            export ZENITH_ENV=production
            ;;
        "development")
            log "INFO" "Starting in Development Mode..."
            export ZENITH_ENV=development
            export ZENITH_DEBUG=true
            ;;
        "demo")
            log "INFO" "Starting in Demo Mode..."
            export ZENITH_ENV=demo
            ;;
        "simple")
            log "INFO" "Starting in Simple Mode (Legacy)..."
            ;;
    esac
    
    echo ""
    log "INFO" "Application starting on http://localhost:$port"
    
    if [ -f "$ENTERPRISE_MARKER" ]; then
        echo -e "${GREEN}💡 Enterprise features enabled${NC}"
        echo -e "${GREEN}💡 Admin login required${NC}"
    else
        echo -e "${YELLOW}💡 Demo admin login is automatically enabled${NC}"
    fi
    
    echo -e "${BLUE}💡 Press Ctrl+C to stop the application${NC}"
    echo ""
    
    # Start the Streamlit application
    python -m streamlit run "$interface" --server.port "$port" --server.headless true
}

# Handle reset mode
handle_reset_mode() {
    echo ""
    log "WARN" "Reset Mode - This will reset system data!"
    echo -e "${RED}⚠️  WARNING: This will delete all user data and configurations!${NC}"
    echo ""
    
    read -p "Are you sure you want to proceed? (type 'RESET' to confirm): " confirm
    
    if [ "$confirm" != "RESET" ]; then
        log "INFO" "Reset cancelled by user"
        return 0
    fi
    
    log "INFO" "Creating backup before reset..."
    
    # Create backup
    backup_dir="./data/backups/$(date +%Y%m%d_%H%M%S)_pre_reset"
    mkdir -p "$backup_dir"
    
    if [ -d "./data" ]; then
        cp -r ./data/* "$backup_dir/" 2>/dev/null || true
        log "INFO" "Backup created at: $backup_dir"
    fi
    
    # Perform reset
    log "INFO" "Performing system reset..."
    
    # Remove enterprise marker
    [ -f "$ENTERPRISE_MARKER" ] && rm -f "$ENTERPRISE_MARKER"
    
    # Remove databases
    find ./data -name "*.db" -type f -delete 2>/dev/null || true
    
    # Remove configuration files
    find ./data \( -name "*.json" -o -name "*.yaml" \) -type f -delete 2>/dev/null || true
    
    log "INFO" "System reset completed"
    log "INFO" "Backup available at: $backup_dir"
    
    echo ""
    read -p "Do you want to run enterprise setup now? (y/n): " setup_now
    if [[ "$setup_now" =~ ^[Yy]$ ]]; then
        run_enterprise_setup
    fi
}

# Create required directories
create_directories() {
    local dirs=("data/logs" "data/enterprise" "data/backups")
    
    for dir in "${dirs[@]}"; do
        mkdir -p "$dir" 2>/dev/null || true
    done
    
    # Create startup log
    touch "$STARTUP_LOG" 2>/dev/null || true
}

# Main execution
main() {
    # Initialize
    create_directories
    
    # Parse command line arguments
    local mode=""
    local interactive=true
    local port=8501
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --mode=*)
                mode="${1#*=}"
                interactive=false
                shift
                ;;
            --port=*)
                port="${1#*=}"
                shift
                ;;
            --non-interactive)
                interactive=false
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --mode=MODE          Set startup mode (production|development|demo|setup|reset|health|simple)"
                echo "  --port=PORT          Set application port (default: 8501)"
                echo "  --non-interactive    Skip interactive prompts"
                echo "  --help              Show this help message"
                exit 0
                ;;
            *)
                log "ERROR" "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    print_banner
    log "INFO" "Zenith startup initiated"
    
    # System requirements check
    if ! check_system_requirements; then
        log "ERROR" "System requirements not met"
        exit 1
    fi
    
    # Setup virtual environment
    setup_virtual_environment
    
    # Ensure Python dependencies are available
    ensure_python_dependencies
    
    # Interactive mode selection if not specified
    if [ -z "$mode" ] && [ "$interactive" = true ]; then
        choice=$(show_startup_menu)
        case $choice in
            1) mode="production" ;;
            2) mode="development" ;;
            3) mode="demo" ;;
            4) mode="setup" ;;
            5) mode="reset" ;;
            6) mode="health" ;;
            7) mode="simple" ;;
        esac
    fi
    
    # Set default mode if still not specified
    [ -z "$mode" ] && mode="development"
    
    # Handle different startup modes
    case "$mode" in
        "setup")
            if ! run_enterprise_setup; then
                log "ERROR" "Enterprise setup failed"
                exit 1
            fi
            
            echo ""
            read -p "Setup completed. Start the application now? (y/n): " start_now
            if [[ "$start_now" =~ ^[Yy]$ ]]; then
                start_application "production" "$port"
            fi
            ;;
            
        "reset")
            handle_reset_mode
            ;;
            
        "health")
            run_health_check
            exit $?
            ;;
            
        "production"|"development"|"demo"|"simple")
            # Check if enterprise setup is required
            if [ "$mode" != "simple" ] && ! check_enterprise_setup; then
                log "WARN" "Enterprise setup required for $mode mode"
                echo ""
                read -p "Run enterprise setup now? (y/n): " run_setup
                if [[ "$run_setup" =~ ^[Yy]$ ]]; then
                    if ! run_enterprise_setup; then
                        log "ERROR" "Setup failed. Falling back to simple mode."
                        mode="simple"
                    fi
                else
                    log "INFO" "Falling back to simple mode"
                    mode="simple"
                fi
            fi
            
            # Run health check
            if ! run_health_check; then
                log "WARN" "Some health checks failed, but continuing..."
            fi
            
            # Start application
            start_application "$mode" "$port"
            ;;
            
        *)
            log "ERROR" "Unknown mode: $mode"
            exit 1
            ;;
    esac
    
    echo ""
    log "INFO" "👋 Zenith AI Chat stopped."
    
    # Only pause in interactive mode
    if [ "$interactive" = true ]; then
        read -p "Press Enter to exit..."
    fi
}

# Trap Ctrl+C and cleanup
trap 'echo ""; log "INFO" "Startup interrupted by user"; exit 130' INT

# Run main function
main "$@"