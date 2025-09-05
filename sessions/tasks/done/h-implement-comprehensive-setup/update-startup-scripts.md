# Update Start Zenith Scripts for Enterprise Setup

## Subtask Overview

Enhance the existing `start_zenith.sh` and `start_zenith.bat` scripts to support the new comprehensive enterprise setup system, providing intelligent startup workflows for different deployment modes.

## Current Script Analysis

**Existing functionality:**
- Directory validation (checks for `simple_chat_app.py`)
- Virtual environment activation
- System status check (`python main.py info`)
- Streamlit app startup on port 8501
- Basic error handling and user messaging

## Required Enhancements

### 1. Enterprise Setup Detection
- [ ] **First-run detection** - Identify if initial enterprise setup is needed
- [ ] **Setup wizard integration** - Guide users through initial admin account creation
- [ ] **Configuration validation** - Verify all enterprise components are properly configured
- [ ] **Database schema validation** - Check for required tables and migrations

### 2. Security & Authentication
- [ ] **Admin credentials check** - Verify admin account exists or guide creation
- [ ] **Secret management validation** - Ensure secure storage of API keys and secrets
- [ ] **TLS certificate validation** - Check SSL/TLS configuration for production mode
- [ ] **Security audit pre-flight** - Run basic security checks before startup

### 3. Multi-Mode Startup Support
- [ ] **Development mode** - Traditional startup with enhanced debugging
- [ ] **Production mode** - Enterprise-grade startup with full security validation
- [ ] **Demo mode** - Guided demonstration with sample data
- [ ] **Reset mode** - Controlled system reset workflow integration

### 4. Component Health Validation
- [ ] **Database connectivity** - SQLite and Qdrant health checks
- [ ] **AI provider validation** - Verify OpenAI/Anthropic/local model connectivity
- [ ] **Vector store readiness** - Ensure Qdrant collections are properly configured
- [ ] **Dependency verification** - Check all enterprise dependencies are available

### 5. Enhanced User Experience
- [ ] **Interactive menu system** - Allow users to choose startup mode
- [ ] **Progress indicators** - Visual feedback during startup process
- [ ] **Detailed error reporting** - Clear guidance when issues are detected
- [ ] **Auto-recovery suggestions** - Suggest fixes for common startup issues

### 6. Integration Points

#### With Setup System
```bash
# Example enhanced startup flow
if [[ ! -f ".enterprise_configured" ]]; then
    echo "🏗️ First-time setup detected..."
    python main.py setup --enterprise --interactive
fi
```

#### With Reset System
```bash
# Support reset workflow
if [[ "$1" == "--reset" ]]; then
    echo "🔄 Initiating controlled system reset..."
    python main.py reset --interactive --backup
fi
```

#### With Health Monitoring
```bash
# Enhanced health checks
echo "🔍 Running enterprise health checks..."
python main.py health --enterprise --verbose
```

### 7. Cross-Platform Consistency
- [ ] **Feature parity** - Ensure Windows (.bat) and Unix (.sh) scripts have identical functionality
- [ ] **Error handling consistency** - Same error codes and messages across platforms
- [ ] **Environment detection** - Proper handling of different OS environments
- [ ] **Path handling** - Robust file path management for both platforms

### 8. Configuration Management Integration
- [ ] **Dynamic port selection** - Support configurable ports from enterprise settings
- [ ] **Environment-specific startup** - Different behaviors for dev/staging/prod
- [ ] **Admin interface selection** - Choose between simple and enterprise interfaces
- [ ] **Backup verification** - Check backup systems before production startup

## Implementation Strategy

### Phase 1: Enhanced Validation
1. Add enterprise setup detection
2. Implement comprehensive health checks
3. Create interactive startup menu

### Phase 2: Multi-Mode Support
1. Implement development/production mode selection
2. Add reset workflow integration
3. Create demo mode for showcasing

### Phase 3: Security Integration
1. Add authentication validation
2. Implement secret management checks
3. Add TLS/security validation

### Phase 4: User Experience
1. Create progress indicators
2. Add detailed error reporting
3. Implement auto-recovery suggestions

## Success Criteria

- [ ] Scripts detect first-time enterprise setup and guide user through initialization
- [ ] Multi-mode startup (dev/prod/demo/reset) works consistently across platforms
- [ ] Comprehensive health checks validate all enterprise components before startup
- [ ] Clear error messages and recovery suggestions for common issues
- [ ] Interactive menu system for selecting startup options
- [ ] Backward compatibility maintained with existing simple startup workflow
- [ ] Integration with new admin interface and authentication system
- [ ] Support for enterprise configuration management and dynamic settings

## Integration Dependencies

- **Backend Security Agent**: Admin authentication validation
- **Database Agent**: Schema and migration validation  
- **Configuration Agent**: Dynamic settings and environment management
- **Deployment Agent**: Reset workflow integration
- **Frontend Agent**: Admin interface selection logic

## Files to Modify

- `start_zenith.sh` - Unix/Linux startup script
- `start_zenith.bat` - Windows startup script  
- `main.py` - Add enterprise setup/health/reset commands if needed
- Create `startup_utils.py` - Shared startup logic and validation functions