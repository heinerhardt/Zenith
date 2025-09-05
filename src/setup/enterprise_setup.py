"""
Enterprise Setup Initialization System for Zenith
Master orchestrator for enterprise-grade deployment and setup following
the comprehensive specification from template/setup.md.
"""

import os
import sys
import json
import secrets
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple, Callable
from enum import Enum
from pathlib import Path
import sqlite3
import shutil
import asyncio
from dataclasses import dataclass, asdict

# Enterprise components
from database.enterprise_schema import EnterpriseDatabase, UserRole
from database.migrations import get_migration_manager, initialize_migration_system
from auth.enterprise_auth_manager import (
    initialize_enterprise_auth, get_enterprise_auth_manager
)
from utils.enterprise_security import (
    initialize_enterprise_security, PasswordPolicy, get_enterprise_security_manager
)
from core.secrets_manager import (
    initialize_secrets_management, get_secrets_manager, SecretType
)
from core.enhanced_configuration_manager import (
    initialize_configuration_management, get_config_manager, ConfigSchema, ConfigValueType
)
from utils.logger import get_logger

logger = get_logger(__name__)


class SetupPhase(Enum):
    """Setup phase enumeration"""
    INITIALIZATION = "initialization"
    DATABASE_SETUP = "database_setup"
    MIGRATION_EXECUTION = "migration_execution"
    SECRETS_MANAGEMENT = "secrets_management"
    CONFIGURATION_SETUP = "configuration_setup"
    ADMIN_ACCOUNT_CREATION = "admin_account_creation"
    SYSTEM_VALIDATION = "system_validation"
    FINALIZATION = "finalization"


class SetupStatus(Enum):
    """Setup status enumeration"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class SetupResult:
    """Setup operation result"""
    phase: SetupPhase
    status: SetupStatus
    message: str
    details: Dict[str, Any] = None
    duration_seconds: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.details is None:
            self.details = {}


@dataclass
class EnterpriseSetupConfig:
    """Enterprise setup configuration"""
    # Database configuration
    database_path: str = "./data/enterprise/zenith.db"
    enable_wal_mode: bool = True
    backup_before_setup: bool = True
    
    # Admin user configuration
    admin_username: str = "admin"
    admin_email: str = "admin@zenith.local"
    admin_password: Optional[str] = None  # Will be generated if not provided
    admin_full_name: str = "System Administrator"
    
    # Security configuration
    password_policy: Optional[Dict[str, Any]] = None
    jwt_secret_key: Optional[str] = None
    encryption_key: Optional[str] = None
    
    # Secrets management configuration
    secrets_backend: str = "local_encrypted"
    secrets_storage_path: str = "./data/enterprise/secrets"
    
    # Environment configuration
    environment: str = "production"
    debug_mode: bool = False
    
    # Feature flags
    enable_hot_config_reload: bool = True
    enable_audit_logging: bool = True
    enable_security_monitoring: bool = True
    
    # External integrations
    qdrant_url: str = "http://localhost:6333"
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnterpriseSetupConfig':
        """Create from dictionary"""
        return cls(**data)
    
    @classmethod
    def from_file(cls, config_path: str) -> 'EnterpriseSetupConfig':
        """Load from configuration file"""
        config_path = Path(config_path)
        
        if not config_path.exists():
            logger.info(f"Config file not found: {config_path}. Using defaults.")
            return cls()
        
        with open(config_path, 'r') as f:
            if config_path.suffix.lower() == '.yaml':
                import yaml
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        
        return cls.from_dict(data)


class EnterpriseSetupManager:
    """Enterprise setup manager - orchestrates complete setup process"""
    
    def __init__(self, config: EnterpriseSetupConfig = None):
        """Initialize enterprise setup manager"""
        self.config = config or EnterpriseSetupConfig()
        self.setup_results: List[SetupResult] = []
        self.setup_start_time = None
        self.current_phase = None
        
        # Ensure data directories exist
        self._ensure_directories()
        
        logger.info("Initialized enterprise setup manager")
    
    def _ensure_directories(self):
        """Ensure required directories exist"""
        directories = [
            Path(self.config.database_path).parent,
            Path(self.config.secrets_storage_path),
            Path("./data/enterprise/backups"),
            Path("./data/enterprise/logs"),
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    async def run_complete_setup(self, 
                                interactive: bool = False,
                                force_recreate: bool = False) -> Tuple[bool, List[SetupResult]]:
        """
        Run complete enterprise setup process
        
        Args:
            interactive: Enable interactive prompts for configuration
            force_recreate: Force recreation of existing components
            
        Returns:
            Tuple of (success, setup_results)
        """
        logger.info("Starting enterprise setup process")
        self.setup_start_time = datetime.utcnow()
        self.setup_results.clear()
        
        setup_phases = [
            (SetupPhase.INITIALIZATION, self._phase_initialization),
            (SetupPhase.DATABASE_SETUP, self._phase_database_setup),
            (SetupPhase.MIGRATION_EXECUTION, self._phase_migration_execution),
            (SetupPhase.SECRETS_MANAGEMENT, self._phase_secrets_management),
            (SetupPhase.CONFIGURATION_SETUP, self._phase_configuration_setup),
            (SetupPhase.ADMIN_ACCOUNT_CREATION, self._phase_admin_account_creation),
            (SetupPhase.SYSTEM_VALIDATION, self._phase_system_validation),
            (SetupPhase.FINALIZATION, self._phase_finalization),
        ]
        
        success = True
        
        for phase, phase_func in setup_phases:
            self.current_phase = phase
            logger.info(f"Starting setup phase: {phase.value}")
            
            phase_start = datetime.utcnow()
            
            try:
                if interactive:
                    # Interactive prompts for configuration
                    await self._interactive_phase_config(phase)
                
                result = await phase_func(force_recreate)
                result.duration_seconds = (datetime.utcnow() - phase_start).total_seconds()
                
                self.setup_results.append(result)
                
                if result.status == SetupStatus.FAILED:
                    logger.error(f"Setup phase failed: {phase.value} - {result.message}")
                    success = False
                    break
                elif result.status == SetupStatus.COMPLETED:
                    logger.info(f"Setup phase completed: {phase.value} - {result.message}")
                else:
                    logger.info(f"Setup phase {result.status.value}: {phase.value} - {result.message}")
                
            except Exception as e:
                error_result = SetupResult(
                    phase=phase,
                    status=SetupStatus.FAILED,
                    message=f"Unexpected error: {str(e)}",
                    duration_seconds=(datetime.utcnow() - phase_start).total_seconds()
                )
                self.setup_results.append(error_result)
                logger.error(f"Setup phase error: {phase.value} - {e}")
                success = False
                break
        
        total_duration = (datetime.utcnow() - self.setup_start_time).total_seconds()
        
        if success:
            logger.info(f"Enterprise setup completed successfully in {total_duration:.2f} seconds")
            self._save_setup_completion_marker()
        else:
            logger.error(f"Enterprise setup failed after {total_duration:.2f} seconds")
        
        return success, self.setup_results
    
    async def _interactive_phase_config(self, phase: SetupPhase):
        """Interactive configuration for setup phase"""
        if phase == SetupPhase.ADMIN_ACCOUNT_CREATION:
            if not self.config.admin_password:
                print(f"\n=== Admin Account Setup ===")
                print(f"Default admin username: {self.config.admin_username}")
                print(f"Default admin email: {self.config.admin_email}")
                
                custom_username = input(f"Enter admin username (default: {self.config.admin_username}): ").strip()
                if custom_username:
                    self.config.admin_username = custom_username
                
                custom_email = input(f"Enter admin email (default: {self.config.admin_email}): ").strip()
                if custom_email:
                    self.config.admin_email = custom_email
                
                print("Leave password empty to generate a secure random password.")
                custom_password = input("Enter admin password: ").strip()
                if custom_password:
                    self.config.admin_password = custom_password
    
    async def _phase_initialization(self, force_recreate: bool) -> SetupResult:
        """Phase 1: Initialization and pre-flight checks"""
        try:
            # Check system requirements
            checks = {
                'python_version': sys.version_info >= (3, 9),
                'write_permissions': self._check_write_permissions(),
                'disk_space': self._check_disk_space(),
                'dependencies': self._check_dependencies()
            }
            
            failed_checks = [name for name, passed in checks.items() if not passed]
            
            if failed_checks:
                return SetupResult(
                    phase=SetupPhase.INITIALIZATION,
                    status=SetupStatus.FAILED,
                    message=f"System checks failed: {', '.join(failed_checks)}",
                    details={'checks': checks}
                )
            
            # Initialize logging
            self._setup_enterprise_logging()
            
            return SetupResult(
                phase=SetupPhase.INITIALIZATION,
                status=SetupStatus.COMPLETED,
                message="System initialization completed successfully",
                details={'checks': checks}
            )
            
        except Exception as e:
            return SetupResult(
                phase=SetupPhase.INITIALIZATION,
                status=SetupStatus.FAILED,
                message=f"Initialization failed: {str(e)}"
            )
    
    async def _phase_database_setup(self, force_recreate: bool) -> SetupResult:
        """Phase 2: Database infrastructure setup"""
        try:
            database_path = Path(self.config.database_path)
            
            # Backup existing database if it exists
            if database_path.exists() and self.config.backup_before_setup:
                backup_path = self._create_database_backup()
                logger.info(f"Created database backup: {backup_path}")
            
            # Initialize enterprise database
            enterprise_db = EnterpriseDatabase(str(database_path))
            
            if force_recreate and database_path.exists():
                logger.warning("Force recreating database")
                database_path.unlink()
            
            # Initialize database with enterprise schema
            success = enterprise_db.initialize_database()
            
            if not success:
                return SetupResult(
                    phase=SetupPhase.DATABASE_SETUP,
                    status=SetupStatus.FAILED,
                    message="Failed to initialize enterprise database"
                )
            
            # Perform health check
            health_status = enterprise_db.health_check()
            
            return SetupResult(
                phase=SetupPhase.DATABASE_SETUP,
                status=SetupStatus.COMPLETED,
                message="Database infrastructure setup completed",
                details={'health_status': health_status}
            )
            
        except Exception as e:
            return SetupResult(
                phase=SetupPhase.DATABASE_SETUP,
                status=SetupStatus.FAILED,
                message=f"Database setup failed: {str(e)}"
            )
    
    async def _phase_migration_execution(self, force_recreate: bool) -> SetupResult:
        """Phase 3: Database migration execution"""
        try:
            # Initialize migration system
            initialize_migration_system(self.config.database_path)
            migration_manager = get_migration_manager()
            
            # Run migrations
            success, messages = migration_manager.migrate_up()
            
            if not success:
                return SetupResult(
                    phase=SetupPhase.MIGRATION_EXECUTION,
                    status=SetupStatus.FAILED,
                    message="Database migrations failed",
                    details={'messages': messages}
                )
            
            # Get migration status
            migration_status = migration_manager.get_migration_status()
            
            return SetupResult(
                phase=SetupPhase.MIGRATION_EXECUTION,
                status=SetupStatus.COMPLETED,
                message="Database migrations completed successfully",
                details={'status': migration_status, 'messages': messages}
            )
            
        except Exception as e:
            return SetupResult(
                phase=SetupPhase.MIGRATION_EXECUTION,
                status=SetupStatus.FAILED,
                message=f"Migration execution failed: {str(e)}"
            )
    
    async def _phase_secrets_management(self, force_recreate: bool) -> SetupResult:
        """Phase 4: Secrets management setup"""
        try:
            # Configure secrets management
            secrets_config = {
                'backends': [{
                    'type': self.config.secrets_backend,
                    'name': 'default',
                    'primary': True,
                    'config': {
                        'storage_path': self.config.secrets_storage_path
                    }
                }],
                'storage_path': self.config.secrets_storage_path
            }
            
            # Initialize secrets management
            initialize_secrets_management(secrets_config)
            secrets_manager = get_secrets_manager()
            
            # Generate and store essential secrets
            secrets_to_create = []
            
            if not self.config.jwt_secret_key:
                jwt_secret = secrets.token_urlsafe(64)
                secrets_manager.store_secret('jwt_secret_key', jwt_secret, SecretType.JWT_SECRET)
                secrets_to_create.append('jwt_secret_key')
            
            if not self.config.encryption_key:
                encryption_key = secrets.token_urlsafe(32)
                secrets_manager.store_secret('encryption_key', encryption_key, SecretType.ENCRYPTION_KEY)
                secrets_to_create.append('encryption_key')
            
            # Store external API keys if provided
            if self.config.openai_api_key:
                secrets_manager.store_secret('openai_api_key', self.config.openai_api_key, SecretType.API_KEY)
                secrets_to_create.append('openai_api_key')
            
            if self.config.anthropic_api_key:
                secrets_manager.store_secret('anthropic_api_key', self.config.anthropic_api_key, SecretType.API_KEY)
                secrets_to_create.append('anthropic_api_key')
            
            # Perform health check
            health_status = secrets_manager.health_check()
            
            return SetupResult(
                phase=SetupPhase.SECRETS_MANAGEMENT,
                status=SetupStatus.COMPLETED,
                message="Secrets management setup completed",
                details={
                    'secrets_created': secrets_to_create,
                    'health_status': health_status
                }
            )
            
        except Exception as e:
            return SetupResult(
                phase=SetupPhase.SECRETS_MANAGEMENT,
                status=SetupStatus.FAILED,
                message=f"Secrets management setup failed: {str(e)}"
            )
    
    async def _phase_configuration_setup(self, force_recreate: bool) -> SetupResult:
        """Phase 5: Configuration management setup"""
        try:
            # Initialize configuration management
            initialize_configuration_management(
                self.config.database_path,
                self.config.environment
            )
            config_manager = get_config_manager()
            
            # Set enterprise configuration values
            enterprise_configs = {
                'app.name': 'Zenith Enterprise',
                'app.environment': self.config.environment,
                'app.debug': self.config.debug_mode,
                'database.path': self.config.database_path,
                'qdrant.url': self.config.qdrant_url,
                'security.jwt_secret': '${secret:jwt_secret_key}',
                'security.encryption_key': '${secret:encryption_key}',
                'features.hot_config_reload': self.config.enable_hot_config_reload,
                'features.audit_logging': self.config.enable_audit_logging,
                'features.security_monitoring': self.config.enable_security_monitoring,
            }
            
            # Set API key references if available
            if self.config.openai_api_key:
                enterprise_configs['openai.api_key'] = '${secret:openai_api_key}'
            
            if self.config.anthropic_api_key:
                enterprise_configs['anthropic.api_key'] = '${secret:anthropic_api_key}'
            
            # Apply configurations
            config_errors = []
            for key, value in enterprise_configs.items():
                if not config_manager.set_config(key, value, changed_by="enterprise_setup"):
                    config_errors.append(key)
            
            if config_errors:
                return SetupResult(
                    phase=SetupPhase.CONFIGURATION_SETUP,
                    status=SetupStatus.FAILED,
                    message=f"Failed to set configurations: {', '.join(config_errors)}"
                )
            
            # Perform health check
            health_status = config_manager.health_check()
            
            return SetupResult(
                phase=SetupPhase.CONFIGURATION_SETUP,
                status=SetupStatus.COMPLETED,
                message="Configuration management setup completed",
                details={
                    'configurations_set': len(enterprise_configs),
                    'health_status': health_status
                }
            )
            
        except Exception as e:
            return SetupResult(
                phase=SetupPhase.CONFIGURATION_SETUP,
                status=SetupStatus.FAILED,
                message=f"Configuration setup failed: {str(e)}"
            )
    
    async def _phase_admin_account_creation(self, force_recreate: bool) -> SetupResult:
        """Phase 6: Administrator account creation"""
        try:
            # Initialize enterprise security
            password_policy = None
            if self.config.password_policy:
                from ..utils.enterprise_security import PasswordPolicy
                password_policy = PasswordPolicy(**self.config.password_policy)
            
            initialize_enterprise_security(
                password_policy=password_policy,
                jwt_secret_key=self.config.jwt_secret_key
            )
            
            # Initialize enterprise authentication
            initialize_enterprise_auth(self.config.database_path, password_policy)
            auth_manager = get_enterprise_auth_manager()
            security_manager = get_enterprise_security_manager()
            
            # Generate admin password if not provided
            admin_password = self.config.admin_password
            if not admin_password:
                admin_password = security_manager.generate_secure_password(16)
                logger.info("Generated secure admin password")
            
            # Hash password
            password_hash = security_manager.hash_password(admin_password, "admin_user")
            
            # Create admin user in database
            enterprise_db = EnterpriseDatabase(self.config.database_path)
            admin_uuid = enterprise_db.create_admin_user(
                username=self.config.admin_username,
                email=self.config.admin_email,
                password_hash=password_hash,
                full_name=self.config.admin_full_name
            )
            
            if not admin_uuid:
                return SetupResult(
                    phase=SetupPhase.ADMIN_ACCOUNT_CREATION,
                    status=SetupStatus.FAILED,
                    message="Failed to create administrator account"
                )
            
            # Save admin credentials securely
            credentials_info = {
                'username': self.config.admin_username,
                'email': self.config.admin_email,
                'password': admin_password,  # This will be shown to user once
                'uuid': admin_uuid,
                'created_at': datetime.utcnow().isoformat()
            }
            
            return SetupResult(
                phase=SetupPhase.ADMIN_ACCOUNT_CREATION,
                status=SetupStatus.COMPLETED,
                message="Administrator account created successfully",
                details={
                    'admin_uuid': admin_uuid,
                    'credentials': credentials_info
                }
            )
            
        except Exception as e:
            return SetupResult(
                phase=SetupPhase.ADMIN_ACCOUNT_CREATION,
                status=SetupStatus.FAILED,
                message=f"Admin account creation failed: {str(e)}"
            )
    
    async def _phase_system_validation(self, force_recreate: bool) -> SetupResult:
        """Phase 7: System validation and health checks"""
        try:
            validation_results = {}
            
            # Database health check
            enterprise_db = EnterpriseDatabase(self.config.database_path)
            validation_results['database'] = enterprise_db.health_check()
            
            # Migration system health check
            migration_manager = get_migration_manager()
            validation_results['migrations'] = migration_manager.get_migration_status()
            
            # Secrets management health check
            secrets_manager = get_secrets_manager()
            validation_results['secrets'] = secrets_manager.health_check()
            
            # Configuration management health check
            config_manager = get_config_manager()
            validation_results['configuration'] = config_manager.health_check()
            
            # Authentication system validation
            try:
                auth_manager = get_enterprise_auth_manager()
                # Test authentication components are accessible
                validation_results['authentication'] = {
                    'initialized': True,
                    'user_store_available': auth_manager.user_store is not None,
                    'security_manager_available': auth_manager.security_manager is not None
                }
            except Exception as e:
                validation_results['authentication'] = {
                    'initialized': False,
                    'error': str(e)
                }
            
            # Check for critical failures
            critical_failures = []
            for component, status in validation_results.items():
                if isinstance(status, dict):
                    if status.get('database_accessible') is False:
                        critical_failures.append(f"{component}: database not accessible")
                    if status.get('available_backends', 0) == 0:
                        critical_failures.append(f"{component}: no backends available")
                    if status.get('initialized') is False:
                        critical_failures.append(f"{component}: not initialized")
            
            if critical_failures:
                return SetupResult(
                    phase=SetupPhase.SYSTEM_VALIDATION,
                    status=SetupStatus.FAILED,
                    message=f"Critical system validation failures: {'; '.join(critical_failures)}",
                    details={'validation_results': validation_results}
                )
            
            return SetupResult(
                phase=SetupPhase.SYSTEM_VALIDATION,
                status=SetupStatus.COMPLETED,
                message="System validation completed successfully",
                details={'validation_results': validation_results}
            )
            
        except Exception as e:
            return SetupResult(
                phase=SetupPhase.SYSTEM_VALIDATION,
                status=SetupStatus.FAILED,
                message=f"System validation failed: {str(e)}"
            )
    
    async def _phase_finalization(self, force_recreate: bool) -> SetupResult:
        """Phase 8: Finalization and cleanup"""
        try:
            # Create setup completion marker
            completion_info = {
                'setup_version': '1.0.0',
                'completed_at': datetime.utcnow().isoformat(),
                'environment': self.config.environment,
                'database_path': self.config.database_path,
                'configuration': self.config.to_dict()
            }
            
            marker_path = Path(self.config.database_path).parent / ".enterprise_setup_complete"
            with open(marker_path, 'w') as f:
                json.dump(completion_info, f, indent=2)
            
            # Generate setup summary
            total_duration = (datetime.utcnow() - self.setup_start_time).total_seconds()
            successful_phases = sum(1 for r in self.setup_results if r.status == SetupStatus.COMPLETED)
            
            summary = {
                'total_duration_seconds': total_duration,
                'successful_phases': successful_phases,
                'total_phases': len(self.setup_results),
                'environment': self.config.environment,
                'database_path': self.config.database_path,
                'completion_marker': str(marker_path)
            }
            
            return SetupResult(
                phase=SetupPhase.FINALIZATION,
                status=SetupStatus.COMPLETED,
                message="Enterprise setup finalization completed",
                details=summary
            )
            
        except Exception as e:
            return SetupResult(
                phase=SetupPhase.FINALIZATION,
                status=SetupStatus.FAILED,
                message=f"Finalization failed: {str(e)}"
            )
    
    def _check_write_permissions(self) -> bool:
        """Check write permissions for required directories"""
        try:
            test_paths = [
                Path(self.config.database_path).parent,
                Path(self.config.secrets_storage_path)
            ]
            
            for path in test_paths:
                path.mkdir(parents=True, exist_ok=True)
                test_file = path / f".write_test_{secrets.token_hex(4)}"
                test_file.write_text("test")
                test_file.unlink()
            
            return True
            
        except Exception as e:
            logger.error(f"Write permission check failed: {e}")
            return False
    
    def _check_disk_space(self, required_mb: int = 100) -> bool:
        """Check available disk space"""
        try:
            db_path = Path(self.config.database_path).parent
            stat = shutil.disk_usage(db_path)
            available_mb = stat.free / (1024 * 1024)
            return available_mb >= required_mb
            
        except Exception as e:
            logger.error(f"Disk space check failed: {e}")
            return False
    
    def _check_dependencies(self) -> bool:
        """Check required Python dependencies"""
        try:
            required_packages = [
                'argon2-cffi', 'cryptography', 'pydantic', 'sqlite3'
            ]
            
            for package in required_packages:
                try:
                    if package == 'sqlite3':
                        import sqlite3
                    else:
                        __import__(package.replace('-', '_'))
                except ImportError:
                    logger.error(f"Required package not found: {package}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Dependency check failed: {e}")
            return False
    
    def _setup_enterprise_logging(self):
        """Setup enterprise logging configuration"""
        # Enhanced logging setup would go here
        pass
    
    def _create_database_backup(self) -> str:
        """Create database backup before setup"""
        db_path = Path(self.config.database_path)
        backup_dir = db_path.parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"zenith_backup_{timestamp}.db"
        
        shutil.copy2(db_path, backup_path)
        return str(backup_path)
    
    def _save_setup_completion_marker(self):
        """Save setup completion marker"""
        marker_path = Path(self.config.database_path).parent / ".enterprise_configured"
        
        completion_data = {
            'completed_at': datetime.utcnow().isoformat(),
            'setup_version': '1.0.0',
            'environment': self.config.environment,
            'phases_completed': [r.phase.value for r in self.setup_results if r.status == SetupStatus.COMPLETED]
        }
        
        with open(marker_path, 'w') as f:
            json.dump(completion_data, f, indent=2)
    
    def get_setup_summary(self) -> Dict[str, Any]:
        """Get comprehensive setup summary"""
        if not self.setup_results:
            return {'status': 'not_started'}
        
        total_duration = 0
        if self.setup_start_time:
            total_duration = (datetime.utcnow() - self.setup_start_time).total_seconds()
        
        phase_summaries = []
        for result in self.setup_results:
            phase_summaries.append({
                'phase': result.phase.value,
                'status': result.status.value,
                'message': result.message,
                'duration_seconds': result.duration_seconds,
                'timestamp': result.timestamp.isoformat() if result.timestamp else None
            })
        
        return {
            'status': 'completed' if all(r.status == SetupStatus.COMPLETED for r in self.setup_results) else 'failed',
            'total_duration_seconds': total_duration,
            'environment': self.config.environment,
            'phases': phase_summaries,
            'current_phase': self.current_phase.value if self.current_phase else None
        }
    
    def is_enterprise_setup_complete(self) -> bool:
        """Check if enterprise setup has been completed"""
        marker_path = Path(self.config.database_path).parent / ".enterprise_configured"
        return marker_path.exists()


# Convenience functions
async def run_enterprise_setup(config_path: str = None, 
                              interactive: bool = False,
                              force_recreate: bool = False) -> Tuple[bool, List[SetupResult]]:
    """Run enterprise setup with configuration file"""
    if config_path:
        config = EnterpriseSetupConfig.from_file(config_path)
    else:
        config = EnterpriseSetupConfig()
    
    setup_manager = EnterpriseSetupManager(config)
    return await setup_manager.run_complete_setup(interactive, force_recreate)


def check_enterprise_setup_status(database_path: str = "./data/enterprise/zenith.db") -> Dict[str, Any]:
    """Check enterprise setup status without running setup"""
    config = EnterpriseSetupConfig(database_path=database_path)
    setup_manager = EnterpriseSetupManager(config)
    
    return {
        'is_complete': setup_manager.is_enterprise_setup_complete(),
        'database_exists': Path(database_path).exists(),
        'marker_exists': Path(database_path).parent.joinpath(".enterprise_configured").exists()
    }