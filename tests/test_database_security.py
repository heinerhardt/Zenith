"""
Comprehensive security tests for database_security.py module
Tests path validation, directory traversal protection, and SQLite security
"""

import pytest
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import patch, MagicMock
import os
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.database_security import (
    validate_database_path,
    secure_sqlite_connection,
    sanitize_database_settings,
    check_database_connection
)


class TestDatabasePathValidation:
    """Test comprehensive database path validation and security"""
    
    def setup_method(self):
        """Setup test environment with temporary directory"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir) / "project"
        self.project_root.mkdir(exist_ok=True)
        self.data_dir = self.project_root / "data"
        self.data_dir.mkdir(exist_ok=True)

    def test_valid_relative_path_in_data_directory(self):
        """Test valid relative path within data directory"""
        test_path = "./data/zenith.db"
        is_valid, error_msg, validated_path = validate_database_path(test_path, self.project_root)
        
        assert is_valid is True
        assert error_msg is None
        assert validated_path.name == "zenith.db"
        assert "data" in str(validated_path)

    def test_valid_absolute_path_within_project(self):
        """Test valid absolute path within project boundaries"""
        test_path = str(self.data_dir / "test.db")
        is_valid, error_msg, validated_path = validate_database_path(test_path, self.project_root)
        
        assert is_valid is True
        assert error_msg is None
        assert validated_path == self.data_dir / "test.db"

    def test_directory_traversal_attack_relative(self):
        """Test prevention of directory traversal with ../"""
        test_path = "../../../etc/passwd.db"
        is_valid, error_msg, validated_path = validate_database_path(test_path, self.project_root)
        
        assert is_valid is False
        assert "outside project directory" in error_msg.lower()
        assert validated_path is None

    def test_directory_traversal_attack_absolute(self):
        """Test prevention of absolute path outside project"""
        test_path = "/etc/malicious.db"
        is_valid, error_msg, validated_path = validate_database_path(test_path, self.project_root)
        
        assert is_valid is False
        assert "outside project directory" in error_msg.lower()
        assert validated_path is None

    def test_empty_path_validation(self):
        """Test empty path handling"""
        test_path = ""
        is_valid, error_msg, validated_path = validate_database_path(test_path, self.project_root)
        
        assert is_valid is False
        assert "cannot be empty" in error_msg.lower()
        assert validated_path is None

    def test_none_path_validation(self):
        """Test None path handling"""
        test_path = None
        is_valid, error_msg, validated_path = validate_database_path(test_path, self.project_root)
        
        assert is_valid is False
        assert "cannot be empty" in error_msg.lower()
        assert validated_path is None

    def test_non_db_extension_rejection(self):
        """Test rejection of non-database file extensions"""
        test_path = "./data/malicious.txt"
        is_valid, error_msg, validated_path = validate_database_path(test_path, self.project_root)
        
        assert is_valid is False
        assert "invalid extension" in error_msg.lower()
        assert validated_path is None

    def test_hidden_file_rejection(self):
        """Test rejection of hidden files"""
        test_path = "./data/.hidden.db"
        is_valid, error_msg, validated_path = validate_database_path(test_path, self.project_root)
        
        assert is_valid is False
        assert "hidden files" in error_msg.lower()
        assert validated_path is None

    def test_path_too_long(self):
        """Test rejection of excessively long paths"""
        long_name = "x" * 300
        test_path = f"./data/{long_name}.db"
        is_valid, error_msg, validated_path = validate_database_path(test_path, self.project_root)
        
        assert is_valid is False
        assert "too long" in error_msg.lower()
        assert validated_path is None

    def test_forbidden_path_components(self):
        """Test rejection of forbidden path components"""
        forbidden_paths = [
            "./data/CON.db",     # Windows reserved name
            "./data/aux.db",     # Windows reserved name
            "./data/tmp.db",     # Forbidden component
            "./data/temp.db",    # Forbidden component
        ]
        
        for test_path in forbidden_paths:
            is_valid, error_msg, validated_path = validate_database_path(test_path, self.project_root)
            assert is_valid is False
            assert "forbidden" in error_msg.lower()
            assert validated_path is None


class TestSecureSQLiteConnection:
    """Test secure SQLite connection context manager"""
    
    def setup_method(self):
        """Setup test database"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"

    def test_successful_connection_and_cleanup(self):
        """Test successful connection and automatic cleanup"""
        with secure_sqlite_connection(self.db_path) as conn:
            assert conn is not None
            cursor = conn.cursor()
            cursor.execute("SELECT sqlite_version()")
            version = cursor.fetchone()[0]
            assert version is not None
            assert isinstance(version, str)

    def test_connection_security_pragmas(self):
        """Test that security PRAGMA settings are applied"""
        with secure_sqlite_connection(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check foreign keys are enabled
            cursor.execute("PRAGMA foreign_keys")
            assert cursor.fetchone()[0] == 1
            
            # Check secure_delete is enabled
            cursor.execute("PRAGMA secure_delete")
            assert cursor.fetchone()[0] == 1

    def test_connection_timeout(self):
        """Test connection timeout handling"""
        # Create a locked database to test timeout
        lock_conn = sqlite3.connect(str(self.db_path))
        lock_conn.execute("BEGIN EXCLUSIVE")
        
        try:
            with pytest.raises(Exception):  # Should timeout or fail
                with secure_sqlite_connection(self.db_path) as conn:
                    conn.execute("CREATE TABLE test (id INTEGER)")
        finally:
            lock_conn.close()

    def test_exception_handling_and_cleanup(self):
        """Test that exceptions are properly handled and connections cleaned up"""
        with pytest.raises(sqlite3.Error):
            with secure_sqlite_connection(self.db_path) as conn:
                # Execute invalid SQL to trigger exception
                conn.execute("INVALID SQL SYNTAX")


class TestDatabaseSettingsSanitization:
    """Test database settings sanitization and validation"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

    def test_valid_settings_sanitization(self):
        """Test sanitization of valid database settings"""
        raw_settings = {
            "sqlite_db_path": "./data/test.db",
            "sqlite_auto_backup": True,
            "sqlite_backup_retention_days": 30,
            "sqlite_auto_vacuum": True,
            "sqlite_wal_mode": False,
            "other_setting": "preserved"
        }
        
        sanitized = sanitize_database_settings(raw_settings, self.project_root)
        
        assert "sqlite_db_path" in sanitized
        assert sanitized["sqlite_auto_backup"] is True
        assert sanitized["sqlite_backup_retention_days"] == 30
        assert sanitized["other_setting"] == "preserved"

    def test_invalid_path_sanitization(self):
        """Test handling of invalid database paths"""
        raw_settings = {
            "sqlite_db_path": "../../../malicious.db",
            "sqlite_auto_backup": True
        }
        
        with pytest.raises(ValueError) as excinfo:
            sanitize_database_settings(raw_settings, self.project_root)
        
        assert "invalid database path" in str(excinfo.value).lower()

    def test_type_coercion_and_validation(self):
        """Test type coercion and validation of settings"""
        raw_settings = {
            "sqlite_db_path": "./data/test.db",
            "sqlite_auto_backup": "true",  # String to be coerced
            "sqlite_backup_retention_days": "15",  # String to be coerced
            "sqlite_auto_vacuum": 1,  # Integer to be coerced
            "sqlite_wal_mode": "false"  # String to be coerced
        }
        
        sanitized = sanitize_database_settings(raw_settings, self.project_root)
        
        assert sanitized["sqlite_auto_backup"] is True
        assert sanitized["sqlite_backup_retention_days"] == 15
        assert sanitized["sqlite_auto_vacuum"] is True
        assert sanitized["sqlite_wal_mode"] is False

    def test_range_validation(self):
        """Test range validation for numeric settings"""
        raw_settings = {
            "sqlite_db_path": "./data/test.db",
            "sqlite_backup_retention_days": 500  # Out of valid range
        }
        
        with pytest.raises(ValueError) as excinfo:
            sanitize_database_settings(raw_settings, self.project_root)
        
        assert "retention days" in str(excinfo.value).lower()


class TestDatabaseConnectionTest:
    """Test secure database connection testing function"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        self.data_dir = self.project_root / "data"

    def test_successful_connection_test_with_directory_creation(self):
        """Test successful connection test with automatic directory creation"""
        db_path = "./data/new_test.db"
        success, message, db_info = check_database_connection(db_path, self.project_root)
        
        assert success is True
        assert "successful" in message.lower()
        assert "version" in db_info
        assert "created_directory" in db_info
        assert db_info["created_directory"] is True

    def test_successful_connection_test_existing_directory(self):
        """Test successful connection test with existing directory"""
        self.data_dir.mkdir(exist_ok=True)
        db_path = "./data/existing_test.db"
        success, message, db_info = check_database_connection(db_path, self.project_root)
        
        assert success is True
        assert "successful" in message.lower()
        assert "version" in db_info
        assert db_info.get("created_directory", False) is False

    def test_invalid_path_connection_test(self):
        """Test connection test with invalid path"""
        db_path = "../../../malicious.db"
        success, message, db_info = check_database_connection(db_path, self.project_root)
        
        assert success is False
        assert "invalid" in message.lower()
        assert db_info == {}

    def test_connection_failure_handling(self):
        """Test handling of connection failures"""
        # Use a path that would cause connection failure
        invalid_db_path = "/dev/null/impossible.db"
        success, message, db_info = check_database_connection(invalid_db_path, self.project_root)
        
        assert success is False
        assert "failed" in message.lower() or "error" in message.lower()


class TestSecurityIntegration:
    """Integration tests for overall database security"""
    
    def setup_method(self):
        """Setup integration test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

    def test_end_to_end_secure_database_operation(self):
        """Test complete secure database operation workflow"""
        # 1. Validate path
        db_path = "./data/integration.db"
        is_valid, error_msg, validated_path = validate_database_path(db_path, self.project_root)
        assert is_valid is True
        
        # 2. Test connection
        success, message, db_info = check_database_connection(db_path, self.project_root)
        assert success is True
        
        # 3. Use secure connection
        with secure_sqlite_connection(validated_path) as conn:
            # Create a test table
            conn.execute("CREATE TABLE security_test (id INTEGER PRIMARY KEY, data TEXT)")
            conn.execute("INSERT INTO security_test (data) VALUES (?)", ("test_data",))
            conn.commit()
            
            # Verify data
            cursor = conn.cursor()
            cursor.execute("SELECT data FROM security_test WHERE id = 1")
            result = cursor.fetchone()[0]
            assert result == "test_data"

    def test_attack_scenario_prevention(self):
        """Test prevention of common attack scenarios"""
        attack_paths = [
            "../../../etc/passwd.db",
            "/etc/shadow.db",
            "\\..\\..\\windows\\system32\\config\\sam.db",
            "./data/../../../sensitive.db",
            "data/../../outside.db"
        ]
        
        for attack_path in attack_paths:
            is_valid, error_msg, validated_path = validate_database_path(attack_path, self.project_root)
            assert is_valid is False, f"Attack path should be invalid: {attack_path}"
            assert validated_path is None

    def test_settings_integration_security(self):
        """Test integration with settings sanitization"""
        malicious_settings = {
            "sqlite_db_path": "../../../malicious.db",
            "sqlite_auto_backup": "true",
            "sqlite_backup_retention_days": "999",
            "malicious_injection": "'; DROP TABLE users; --"
        }
        
        with pytest.raises(ValueError):
            sanitize_database_settings(malicious_settings, self.project_root)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])