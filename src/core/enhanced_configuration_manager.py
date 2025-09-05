"""
Enhanced Enterprise Configuration Management System for Zenith
Dynamic configuration with validation, secrets integration, environment-specific
settings, and real-time updates with rollback capabilities.
"""

import os
import json
import yaml
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple, Union, Callable
from enum import Enum
from pathlib import Path
import sqlite3
from dataclasses import dataclass, asdict
import threading
import time
from abc import ABC, abstractmethod

# Pydantic for validation
from pydantic import BaseModel, Field, ValidationError, validator
from pydantic.types import StrictStr, StrictInt, StrictBool, StrictFloat

from .secrets_manager import get_secrets_manager, SecretType
from ..utils.database_security import secure_database_connection
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ConfigScope(Enum):
    """Configuration scope levels"""
    SYSTEM = "system"
    APPLICATION = "application"
    USER = "user"
    SESSION = "session"


class ConfigValueType(Enum):
    """Configuration value types"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    SECRET = "secret"
    FILE_PATH = "file_path"
    URL = "url"
    EMAIL = "email"


class EnvironmentType(Enum):
    """Environment types for configuration"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


@dataclass
class ConfigValidationRule:
    """Configuration validation rule"""
    rule_type: str  # 'range', 'regex', 'choices', 'custom'
    parameters: Dict[str, Any]
    error_message: str = None
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """Validate value against rule"""
        try:
            if self.rule_type == 'range':
                min_val = self.parameters.get('min')
                max_val = self.parameters.get('max')
                
                if min_val is not None and value < min_val:
                    return False, f"Value must be >= {min_val}"
                if max_val is not None and value > max_val:
                    return False, f"Value must be <= {max_val}"
                    
            elif self.rule_type == 'regex':
                import re
                pattern = self.parameters.get('pattern')
                if pattern and not re.match(pattern, str(value)):
                    return False, self.error_message or f"Value must match pattern: {pattern}"
                    
            elif self.rule_type == 'choices':
                choices = self.parameters.get('choices', [])
                if choices and value not in choices:
                    return False, f"Value must be one of: {choices}"
                    
            elif self.rule_type == 'custom':
                validator_func = self.parameters.get('function')
                if validator_func and callable(validator_func):
                    return validator_func(value)
            
            return True, None
            
        except Exception as e:
            return False, f"Validation error: {e}"


class ConfigSchema(BaseModel):
    """Configuration schema definition"""
    key: str
    display_name: str
    description: str = ""
    value_type: ConfigValueType
    default_value: Any = None
    is_required: bool = False
    is_secret: bool = False
    is_readonly: bool = False
    scope: ConfigScope = ConfigScope.APPLICATION
    category: str = "general"
    validation_rules: List[Dict[str, Any]] = Field(default_factory=list)
    environment_specific: bool = False
    restart_required: bool = False
    deprecated: bool = False
    deprecation_message: str = ""
    
    @validator('key')
    def validate_key(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("Key must be a non-empty string")
        if not v.replace('_', '').replace('.', '').isalnum():
            raise ValueError("Key can only contain alphanumeric characters, underscores, and dots")
        return v
    
    def validate_value(self, value: Any) -> Tuple[bool, Optional[str]]:
        """Validate value against schema"""
        # Type validation
        try:
            if self.value_type == ConfigValueType.STRING:
                if not isinstance(value, (str, type(None))):
                    return False, "Value must be a string"
            elif self.value_type == ConfigValueType.INTEGER:
                if not isinstance(value, (int, type(None))) or isinstance(value, bool):
                    return False, "Value must be an integer"
            elif self.value_type == ConfigValueType.FLOAT:
                if not isinstance(value, (float, int, type(None))) or isinstance(value, bool):
                    return False, "Value must be a number"
            elif self.value_type == ConfigValueType.BOOLEAN:
                if not isinstance(value, (bool, type(None))):
                    return False, "Value must be a boolean"
            elif self.value_type == ConfigValueType.JSON:
                if value is not None:
                    try:
                        json.dumps(value)
                    except (TypeError, ValueError):
                        return False, "Value must be JSON serializable"
            elif self.value_type == ConfigValueType.URL:
                if value and not self._is_valid_url(value):
                    return False, "Value must be a valid URL"
            elif self.value_type == ConfigValueType.EMAIL:
                if value and not self._is_valid_email(value):
                    return False, "Value must be a valid email address"
                    
        except Exception as e:
            return False, f"Type validation error: {e}"
        
        # Custom validation rules
        for rule_data in self.validation_rules:
            try:
                rule = ConfigValidationRule(**rule_data)
                is_valid, error = rule.validate(value)
                if not is_valid:
                    return False, error
            except Exception as e:
                logger.warning(f"Validation rule error for {self.key}: {e}")
        
        return True, None
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        import re
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(url) is not None
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        import re
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        return email_pattern.match(email) is not None


class ConfigurationStore(ABC):
    """Abstract configuration storage backend"""
    
    @abstractmethod
    def get_value(self, key: str, environment: str = None) -> Optional[Any]:
        """Get configuration value"""
        pass
    
    @abstractmethod
    def set_value(self, key: str, value: Any, environment: str = None) -> bool:
        """Set configuration value"""
        pass
    
    @abstractmethod
    def delete_value(self, key: str, environment: str = None) -> bool:
        """Delete configuration value"""
        pass
    
    @abstractmethod
    def list_keys(self, environment: str = None) -> List[str]:
        """List configuration keys"""
        pass


class DatabaseConfigurationStore(ConfigurationStore):
    """Database-backed configuration storage"""
    
    def __init__(self, database_path: str):
        """Initialize database configuration store"""
        self.database_path = database_path
        self._initialize_database()
        logger.info("Initialized database configuration store")
    
    def _initialize_database(self):
        """Initialize configuration database tables"""
        with secure_database_connection(self.database_path) as conn:
            # Configuration values table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS configuration_values (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL,
                    value TEXT,
                    value_type TEXT NOT NULL,
                    environment TEXT DEFAULT 'default',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT,
                    updated_by TEXT,
                    UNIQUE(key, environment)
                )
            """)
            
            # Configuration history for rollback
            conn.execute("""
                CREATE TABLE IF NOT EXISTS configuration_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    value_type TEXT NOT NULL,
                    environment TEXT NOT NULL,
                    change_type TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    changed_by TEXT,
                    reason TEXT
                )
            """)
            
            # Configuration schemas
            conn.execute("""
                CREATE TABLE IF NOT EXISTS configuration_schemas (
                    key TEXT PRIMARY KEY,
                    schema_json TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def get_value(self, key: str, environment: str = "default") -> Optional[Any]:
        """Get configuration value from database"""
        try:
            with secure_database_connection(self.database_path) as conn:
                cursor = conn.execute("""
                    SELECT value, value_type FROM configuration_values 
                    WHERE key = ? AND environment = ?
                """, (key, environment))
                
                row = cursor.fetchone()
                if row:
                    value_str, value_type = row
                    return self._deserialize_value(value_str, value_type)
                
        except Exception as e:
            logger.error(f"Error getting config value {key}: {e}")
        
        return None
    
    def set_value(self, key: str, value: Any, environment: str = "default", 
                  changed_by: str = "system", reason: str = None) -> bool:
        """Set configuration value in database"""
        try:
            with secure_database_connection(self.database_path) as conn:
                # Get old value for history
                cursor = conn.execute("""
                    SELECT value, value_type FROM configuration_values 
                    WHERE key = ? AND environment = ?
                """, (key, environment))
                
                old_row = cursor.fetchone()
                old_value = old_row[0] if old_row else None
                
                # Serialize new value
                value_str, value_type = self._serialize_value(value)
                
                # Insert or update value
                conn.execute("""
                    INSERT OR REPLACE INTO configuration_values 
                    (key, value, value_type, environment, updated_at, updated_by)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                """, (key, value_str, value_type, environment, changed_by))
                
                # Record history
                change_type = "update" if old_row else "create"
                conn.execute("""
                    INSERT INTO configuration_history 
                    (key, old_value, new_value, value_type, environment, change_type, changed_by, reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (key, old_value, value_str, value_type, environment, change_type, changed_by, reason))
                
                conn.commit()
                logger.info(f"Set config value: {key} = {value} (env: {environment})")
                return True
                
        except Exception as e:
            logger.error(f"Error setting config value {key}: {e}")
            return False
    
    def delete_value(self, key: str, environment: str = "default", 
                     changed_by: str = "system", reason: str = None) -> bool:
        """Delete configuration value"""
        try:
            with secure_database_connection(self.database_path) as conn:
                # Get old value for history
                cursor = conn.execute("""
                    SELECT value, value_type FROM configuration_values 
                    WHERE key = ? AND environment = ?
                """, (key, environment))
                
                old_row = cursor.fetchone()
                if not old_row:
                    return False
                
                # Delete value
                conn.execute("""
                    DELETE FROM configuration_values 
                    WHERE key = ? AND environment = ?
                """, (key, environment))
                
                # Record history
                conn.execute("""
                    INSERT INTO configuration_history 
                    (key, old_value, new_value, value_type, environment, change_type, changed_by, reason)
                    VALUES (?, ?, NULL, ?, ?, 'delete', ?, ?)
                """, (key, old_row[0], old_row[1], environment, changed_by, reason))
                
                conn.commit()
                logger.info(f"Deleted config value: {key} (env: {environment})")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting config value {key}: {e}")
            return False
    
    def list_keys(self, environment: str = "default") -> List[str]:
        """List configuration keys"""
        try:
            with secure_database_connection(self.database_path) as conn:
                cursor = conn.execute("""
                    SELECT key FROM configuration_values 
                    WHERE environment = ? 
                    ORDER BY key
                """, (environment,))
                
                return [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error listing config keys: {e}")
            return []
    
    def get_history(self, key: str = None, environment: str = None, 
                   limit: int = 100) -> List[Dict[str, Any]]:
        """Get configuration change history"""
        try:
            with secure_database_connection(self.database_path) as conn:
                query = """
                    SELECT key, old_value, new_value, value_type, environment, 
                           change_type, timestamp, changed_by, reason
                    FROM configuration_history
                """
                params = []
                
                conditions = []
                if key:
                    conditions.append("key = ?")
                    params.append(key)
                if environment:
                    conditions.append("environment = ?")
                    params.append(environment)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                cursor = conn.execute(query, params)
                
                return [
                    {
                        'key': row[0],
                        'old_value': row[1],
                        'new_value': row[2],
                        'value_type': row[3],
                        'environment': row[4],
                        'change_type': row[5],
                        'timestamp': row[6],
                        'changed_by': row[7],
                        'reason': row[8]
                    }
                    for row in cursor.fetchall()
                ]
                
        except Exception as e:
            logger.error(f"Error getting config history: {e}")
            return []
    
    def store_schema(self, schema: ConfigSchema) -> bool:
        """Store configuration schema"""
        try:
            with secure_database_connection(self.database_path) as conn:
                schema_json = json.dumps(schema.dict())
                
                conn.execute("""
                    INSERT OR REPLACE INTO configuration_schemas 
                    (key, schema_json, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (schema.key, schema_json))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error storing schema for {schema.key}: {e}")
            return False
    
    def get_schema(self, key: str) -> Optional[ConfigSchema]:
        """Get configuration schema"""
        try:
            with secure_database_connection(self.database_path) as conn:
                cursor = conn.execute("""
                    SELECT schema_json FROM configuration_schemas WHERE key = ?
                """, (key,))
                
                row = cursor.fetchone()
                if row:
                    schema_data = json.loads(row[0])
                    return ConfigSchema(**schema_data)
                
        except Exception as e:
            logger.error(f"Error getting schema for {key}: {e}")
        
        return None
    
    def _serialize_value(self, value: Any) -> Tuple[str, str]:
        """Serialize value for database storage"""
        if value is None:
            return None, "null"
        elif isinstance(value, bool):
            return str(value), "boolean"
        elif isinstance(value, int):
            return str(value), "integer"
        elif isinstance(value, float):
            return str(value), "float"
        elif isinstance(value, str):
            return value, "string"
        else:
            # JSON serialize complex types
            return json.dumps(value), "json"
    
    def _deserialize_value(self, value_str: str, value_type: str) -> Any:
        """Deserialize value from database"""
        if value_str is None or value_type == "null":
            return None
        elif value_type == "boolean":
            return value_str.lower() == "true"
        elif value_type == "integer":
            return int(value_str)
        elif value_type == "float":
            return float(value_str)
        elif value_type == "string":
            return value_str
        elif value_type == "json":
            return json.loads(value_str)
        else:
            return value_str


class EnhancedConfigurationManager:
    """Enhanced enterprise configuration manager"""
    
    def __init__(self, 
                 database_path: str,
                 environment: str = "development",
                 enable_hot_reload: bool = True):
        """Initialize enhanced configuration manager"""
        self.database_path = database_path
        self.environment = environment
        self.enable_hot_reload = enable_hot_reload
        
        # Initialize storage
        self.store = DatabaseConfigurationStore(database_path)
        
        # Configuration cache
        self._config_cache: Dict[str, Any] = {}
        self._cache_timestamp: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(seconds=60)  # Cache for 60 seconds
        
        # Schema registry
        self._schemas: Dict[str, ConfigSchema] = {}
        
        # Change callbacks
        self._change_callbacks: Dict[str, List[Callable]] = {}
        
        # Hot reload thread
        self._reload_thread = None
        self._reload_stop_event = threading.Event()
        
        if enable_hot_reload:
            self._start_hot_reload()
        
        # Initialize with default schemas
        self._register_default_schemas()
        
        logger.info(f"Initialized enhanced configuration manager (env: {environment})")
    
    def register_schema(self, schema: ConfigSchema) -> bool:
        """Register configuration schema"""
        try:
            # Validate schema
            if not schema.key:
                raise ValueError("Schema key is required")
            
            # Store schema
            self._schemas[schema.key] = schema
            success = self.store.store_schema(schema)
            
            if success:
                logger.info(f"Registered config schema: {schema.key}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error registering schema {schema.key}: {e}")
            return False
    
    def get_config(self, key: str, default: Any = None, 
                   use_cache: bool = True, environment: str = None) -> Any:
        """Get configuration value with caching and validation"""
        env = environment or self.environment
        cache_key = f"{key}:{env}"
        
        # Check cache
        if use_cache and cache_key in self._config_cache:
            if (cache_key in self._cache_timestamp and 
                datetime.now() - self._cache_timestamp[cache_key] < self._cache_ttl):
                return self._config_cache[cache_key]
        
        # Get value from store
        value = self.store.get_value(key, env)
        
        # Use default if no value found
        if value is None:
            schema = self._schemas.get(key)
            if schema and schema.default_value is not None:
                value = schema.default_value
            else:
                value = default
        
        # Handle secrets
        if value is not None and self._is_secret_reference(value):
            value = self._resolve_secret_reference(value)
        
        # Validate against schema if available
        schema = self._schemas.get(key)
        if schema and value is not None:
            is_valid, error = schema.validate_value(value)
            if not is_valid:
                logger.warning(f"Invalid config value for {key}: {error}. Using default.")
                value = schema.default_value if schema.default_value is not None else default
        
        # Update cache
        if use_cache:
            self._config_cache[cache_key] = value
            self._cache_timestamp[cache_key] = datetime.now()
        
        return value
    
    def set_config(self, key: str, value: Any, environment: str = None,
                   changed_by: str = "system", reason: str = None,
                   validate: bool = True) -> bool:
        """Set configuration value with validation"""
        env = environment or self.environment
        
        # Validate against schema if available
        if validate:
            schema = self._schemas.get(key)
            if schema:
                is_valid, error = schema.validate_value(value)
                if not is_valid:
                    logger.error(f"Invalid config value for {key}: {error}")
                    return False
                
                # Check if readonly
                if schema.is_readonly:
                    logger.error(f"Cannot modify readonly config: {key}")
                    return False
        
        # Store value
        success = self.store.set_value(key, value, env, changed_by, reason)
        
        if success:
            # Invalidate cache
            cache_key = f"{key}:{env}"
            self._config_cache.pop(cache_key, None)
            self._cache_timestamp.pop(cache_key, None)
            
            # Trigger change callbacks
            self._trigger_change_callbacks(key, value, env)
            
            logger.info(f"Updated config: {key} (env: {env})")
        
        return success
    
    def delete_config(self, key: str, environment: str = None,
                     changed_by: str = "system", reason: str = None) -> bool:
        """Delete configuration value"""
        env = environment or self.environment
        
        # Check if readonly
        schema = self._schemas.get(key)
        if schema and schema.is_readonly:
            logger.error(f"Cannot delete readonly config: {key}")
            return False
        
        success = self.store.delete_value(key, env, changed_by, reason)
        
        if success:
            # Invalidate cache
            cache_key = f"{key}:{env}"
            self._config_cache.pop(cache_key, None)
            self._cache_timestamp.pop(cache_key, None)
            
            # Trigger change callbacks
            self._trigger_change_callbacks(key, None, env)
        
        return success
    
    def list_configs(self, environment: str = None, category: str = None) -> List[str]:
        """List configuration keys"""
        env = environment or self.environment
        keys = self.store.list_keys(env)
        
        # Filter by category if specified
        if category:
            filtered_keys = []
            for key in keys:
                schema = self._schemas.get(key)
                if schema and schema.category == category:
                    filtered_keys.append(key)
            return filtered_keys
        
        return keys
    
    def get_config_info(self, key: str) -> Optional[Dict[str, Any]]:
        """Get configuration information including schema and current value"""
        schema = self._schemas.get(key)
        if not schema:
            return None
        
        current_value = self.get_config(key)
        
        return {
            'key': key,
            'display_name': schema.display_name,
            'description': schema.description,
            'value_type': schema.value_type.value,
            'current_value': current_value if not schema.is_secret else "[REDACTED]",
            'default_value': schema.default_value,
            'is_required': schema.is_required,
            'is_secret': schema.is_secret,
            'is_readonly': schema.is_readonly,
            'scope': schema.scope.value,
            'category': schema.category,
            'environment_specific': schema.environment_specific,
            'restart_required': schema.restart_required,
            'deprecated': schema.deprecated,
            'deprecation_message': schema.deprecation_message
        }
    
    def export_config(self, environment: str = None, format: str = "json") -> str:
        """Export configuration to string format"""
        env = environment or self.environment
        keys = self.list_configs(env)
        
        config_data = {}
        for key in keys:
            value = self.get_config(key, environment=env)
            schema = self._schemas.get(key)
            
            # Don't export secrets
            if schema and schema.is_secret:
                config_data[key] = "[REDACTED]"
            else:
                config_data[key] = value
        
        if format.lower() == "yaml":
            return yaml.dump(config_data, default_flow_style=False)
        else:
            return json.dumps(config_data, indent=2, default=str)
    
    def import_config(self, config_data: str, format: str = "json",
                     environment: str = None, changed_by: str = "system",
                     dry_run: bool = False) -> Tuple[bool, List[str]]:
        """Import configuration from string format"""
        env = environment or self.environment
        messages = []
        
        try:
            # Parse configuration data
            if format.lower() == "yaml":
                data = yaml.safe_load(config_data)
            else:
                data = json.loads(config_data)
            
            if not isinstance(data, dict):
                return False, ["Configuration data must be a dictionary"]
            
            # Validate all values first
            validation_errors = []
            for key, value in data.items():
                schema = self._schemas.get(key)
                if schema:
                    is_valid, error = schema.validate_value(value)
                    if not is_valid:
                        validation_errors.append(f"{key}: {error}")
                    elif schema.is_readonly:
                        validation_errors.append(f"{key}: Cannot import readonly configuration")
            
            if validation_errors:
                return False, validation_errors
            
            if dry_run:
                messages.append(f"Would import {len(data)} configuration values")
                for key in data.keys():
                    messages.append(f"  - {key}")
                return True, messages
            
            # Import values
            success_count = 0
            for key, value in data.items():
                if self.set_config(key, value, env, changed_by, f"Bulk import"):
                    success_count += 1
                    messages.append(f"Imported: {key}")
                else:
                    messages.append(f"Failed to import: {key}")
            
            messages.append(f"Successfully imported {success_count}/{len(data)} configurations")
            return success_count == len(data), messages
            
        except Exception as e:
            return False, [f"Import failed: {e}"]
    
    def rollback_config(self, key: str, steps: int = 1, 
                       environment: str = None) -> bool:
        """Rollback configuration to previous value"""
        env = environment or self.environment
        
        try:
            # Get history
            history = self.store.get_history(key, env, steps + 1)
            
            if len(history) <= steps:
                logger.error(f"Not enough history to rollback {steps} steps for {key}")
                return False
            
            # Get target value
            target_entry = history[steps]
            if target_entry['change_type'] == 'delete':
                # If target was a delete, we need to go further back
                target_value = None
                for entry in history[steps:]:
                    if entry['change_type'] in ['create', 'update']:
                        target_value = self.store._deserialize_value(
                            entry['new_value'], entry['value_type']
                        )
                        break
            else:
                target_value = self.store._deserialize_value(
                    target_entry['old_value'], target_entry['value_type']
                )
            
            # Set value
            if target_value is not None:
                success = self.set_config(key, target_value, env, "system", 
                                        f"Rollback {steps} steps")
            else:
                success = self.delete_config(key, env, "system", 
                                           f"Rollback {steps} steps (delete)")
            
            if success:
                logger.info(f"Rolled back config {key} by {steps} steps")
            
            return success
            
        except Exception as e:
            logger.error(f"Rollback failed for {key}: {e}")
            return False
    
    def register_change_callback(self, key: str, callback: Callable):
        """Register callback for configuration changes"""
        if key not in self._change_callbacks:
            self._change_callbacks[key] = []
        
        self._change_callbacks[key].append(callback)
        logger.debug(f"Registered change callback for {key}")
    
    def _trigger_change_callbacks(self, key: str, new_value: Any, environment: str):
        """Trigger change callbacks for key"""
        callbacks = self._change_callbacks.get(key, [])
        
        for callback in callbacks:
            try:
                callback(key, new_value, environment)
            except Exception as e:
                logger.error(f"Error in change callback for {key}: {e}")
    
    def _is_secret_reference(self, value: Any) -> bool:
        """Check if value is a secret reference"""
        return (isinstance(value, str) and 
                value.startswith("${secret:") and 
                value.endswith("}"))
    
    def _resolve_secret_reference(self, value: str) -> Optional[str]:
        """Resolve secret reference to actual value"""
        try:
            # Extract secret key from ${secret:key} format
            secret_key = value[9:-1]  # Remove "${secret:" and "}"
            
            secrets_manager = get_secrets_manager()
            return secrets_manager.retrieve_secret(secret_key)
            
        except Exception as e:
            logger.error(f"Failed to resolve secret reference {value}: {e}")
            return None
    
    def _start_hot_reload(self):
        """Start hot reload monitoring thread"""
        def hot_reload_worker():
            while not self._reload_stop_event.is_set():
                try:
                    # Clear cache periodically to pick up external changes
                    if self._config_cache:
                        current_time = datetime.now()
                        expired_keys = [
                            key for key, timestamp in self._cache_timestamp.items()
                            if current_time - timestamp > self._cache_ttl
                        ]
                        
                        for key in expired_keys:
                            self._config_cache.pop(key, None)
                            self._cache_timestamp.pop(key, None)
                    
                    time.sleep(30)  # Check every 30 seconds
                    
                except Exception as e:
                    logger.error(f"Hot reload error: {e}")
                    time.sleep(60)  # Wait longer on error
        
        self._reload_thread = threading.Thread(target=hot_reload_worker, daemon=True)
        self._reload_thread.start()
        logger.info("Started configuration hot reload monitoring")
    
    def _register_default_schemas(self):
        """Register default configuration schemas"""
        default_schemas = [
            ConfigSchema(
                key="app.name",
                display_name="Application Name",
                description="Name of the application",
                value_type=ConfigValueType.STRING,
                default_value="Zenith AI",
                category="application"
            ),
            ConfigSchema(
                key="app.port",
                display_name="Application Port",
                description="Port for the web server",
                value_type=ConfigValueType.INTEGER,
                default_value=8501,
                validation_rules=[{
                    'rule_type': 'range',
                    'parameters': {'min': 1024, 'max': 65535}
                }],
                category="server"
            ),
            ConfigSchema(
                key="database.url",
                display_name="Database URL",
                description="Database connection URL",
                value_type=ConfigValueType.URL,
                default_value="sqlite:///./data/zenith.db",
                category="database"
            ),
            ConfigSchema(
                key="qdrant.url",
                display_name="Qdrant URL",
                description="Qdrant vector database URL",
                value_type=ConfigValueType.URL,
                default_value="http://localhost:6333",
                category="vector_database"
            ),
            ConfigSchema(
                key="openai.api_key",
                display_name="OpenAI API Key",
                description="OpenAI API key for chat and embeddings",
                value_type=ConfigValueType.SECRET,
                is_secret=True,
                is_required=False,
                category="ai_providers"
            ),
            ConfigSchema(
                key="security.jwt_secret",
                display_name="JWT Secret Key",
                description="Secret key for JWT token signing",
                value_type=ConfigValueType.SECRET,
                is_secret=True,
                is_required=True,
                category="security"
            ),
            ConfigSchema(
                key="logging.level",
                display_name="Logging Level",
                description="Application logging level",
                value_type=ConfigValueType.STRING,
                default_value="INFO",
                validation_rules=[{
                    'rule_type': 'choices',
                    'parameters': {'choices': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']}
                }],
                category="logging"
            )
        ]
        
        for schema in default_schemas:
            self.register_schema(schema)
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on configuration system"""
        status = {
            'database_accessible': False,
            'schemas_loaded': len(self._schemas),
            'cache_entries': len(self._config_cache),
            'hot_reload_active': self.enable_hot_reload and self._reload_thread and self._reload_thread.is_alive(),
            'environment': self.environment,
            'errors': []
        }
        
        try:
            # Test database access
            test_keys = self.store.list_keys(self.environment)
            status['database_accessible'] = True
            status['total_configs'] = len(test_keys)
            
        except Exception as e:
            status['errors'].append(f"Database error: {e}")
        
        return status
    
    def shutdown(self):
        """Shutdown configuration manager"""
        if self._reload_thread:
            self._reload_stop_event.set()
            self._reload_thread.join(timeout=5)
        
        logger.info("Configuration manager shut down")


# Global configuration manager instance
_config_manager: Optional[EnhancedConfigurationManager] = None


def get_config_manager(database_path: str = None, environment: str = None) -> EnhancedConfigurationManager:
    """Get global configuration manager instance"""
    global _config_manager
    
    if _config_manager is None:
        if database_path is None:
            raise ValueError("Database path required for first initialization")
        _config_manager = EnhancedConfigurationManager(
            database_path, 
            environment or os.getenv('ZENITH_ENV', 'development')
        )
    
    return _config_manager


def initialize_configuration_management(database_path: str, environment: str = None):
    """Initialize configuration management system"""
    global _config_manager
    
    env = environment or os.getenv('ZENITH_ENV', 'development')
    _config_manager = EnhancedConfigurationManager(database_path, env)
    logger.info(f"Configuration management system initialized (env: {env})")


# Convenience functions
def get_config(key: str, default: Any = None) -> Any:
    """Get configuration value using global manager"""
    return get_config_manager().get_config(key, default)


def set_config(key: str, value: Any) -> bool:
    """Set configuration value using global manager"""
    return get_config_manager().set_config(key, value)