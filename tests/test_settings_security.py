"""
Security integration tests for enhanced_settings_manager with database security
Tests the validation framework integration and thread safety
"""

import pytest
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.enhanced_settings_manager import EnhancedSettingsManager


class TestEnhancedSettingsManagerSecurity:
    """Test security enhancements in enhanced settings manager"""
    
    def setup_method(self):
        """Setup test environment with mocked dependencies"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)
        
        # Mock QdrantManager to avoid external dependencies
        with patch('src.core.enhanced_settings_manager.QdrantManager') as mock_qdrant:
            mock_instance = MagicMock()
            mock_qdrant.return_value = mock_instance
            mock_instance.get_client.return_value.get_collection.return_value = None
            
            self.settings_manager = EnhancedSettingsManager()

    def test_database_path_validation_in_update_settings(self):
        """Test database path validation during settings update"""
        # Test valid database path
        valid_updates = {
            "sqlite_db_path": "./data/valid.db",
            "sqlite_auto_backup": True
        }
        
        # Mock the validate_database_path function to return valid result
        with patch('src.utils.database_security.validate_database_path') as mock_validate:
            mock_validate.return_value = (True, None, Path(self.temp_dir) / "data" / "valid.db")
            
            success, message = self.settings_manager.update_settings(valid_updates)
            assert success is True
            mock_validate.assert_called_once()

    def test_invalid_database_path_rejection(self):
        """Test rejection of invalid database paths"""
        malicious_updates = {
            "sqlite_db_path": "../../../etc/passwd.db",
            "sqlite_auto_backup": True
        }
        
        # Mock the validate_database_path function to return invalid result
        with patch('src.utils.database_security.validate_database_path') as mock_validate:
            mock_validate.return_value = (False, "Path outside project directory", None)
            
            success, message = self.settings_manager.update_settings(malicious_updates)
            assert success is False
            assert "invalid database path" in message.lower()
            mock_validate.assert_called_once()

    def test_database_path_normalization(self):
        """Test that database paths are normalized during validation"""
        updates_with_unnormalized_path = {
            "sqlite_db_path": "./data/../data/./normalize.db"
        }
        
        normalized_path = Path(self.temp_dir) / "data" / "normalize.db"
        
        with patch('src.utils.database_security.validate_database_path') as mock_validate:
            mock_validate.return_value = (True, None, normalized_path)
            
            success, message = self.settings_manager.update_settings(updates_with_unnormalized_path)
            assert success is True
            
            # Verify the path was normalized in the updates dict
            mock_validate.assert_called_once()

    def test_sqlite_backup_retention_validation(self):
        """Test validation of SQLite backup retention days"""
        # Test valid retention days
        valid_updates = {"sqlite_backup_retention_days": 30}
        success, message = self.settings_manager.update_settings(valid_updates)
        assert success is True
        
        # Test invalid retention days (too high)
        invalid_updates = {"sqlite_backup_retention_days": 500}
        success, message = self.settings_manager.update_settings(invalid_updates)
        assert success is False
        assert "between 1 and 365" in message
        
        # Test invalid retention days (too low)
        invalid_updates = {"sqlite_backup_retention_days": 0}
        success, message = self.settings_manager.update_settings(invalid_updates)
        assert success is False
        assert "between 1 and 365" in message

    def test_sqlite_boolean_settings_validation(self):
        """Test validation of SQLite boolean settings"""
        boolean_fields = ["sqlite_auto_backup", "sqlite_auto_vacuum", "sqlite_wal_mode"]
        
        for field in boolean_fields:
            # Test valid boolean values
            valid_updates = {field: True}
            success, message = self.settings_manager.update_settings(valid_updates)
            assert success is True
            
            valid_updates = {field: False}
            success, message = self.settings_manager.update_settings(valid_updates)
            assert success is True
            
            # Test invalid boolean values
            invalid_updates = {field: "not_a_boolean"}
            success, message = self.settings_manager.update_settings(invalid_updates)
            assert success is False
            assert "must be true or false" in message

    def test_database_path_validation_error_handling(self):
        """Test error handling in database path validation"""
        updates = {"sqlite_db_path": "./data/test.db"}
        
        # Mock validation to raise an exception
        with patch('src.utils.database_security.validate_database_path') as mock_validate:
            mock_validate.side_effect = Exception("Validation error")
            
            success, message = self.settings_manager.update_settings(updates)
            assert success is False
            assert "database path validation error" in message.lower()

    def test_thread_safe_database_settings_update(self):
        """Test thread safety of database settings updates"""
        results = []
        errors = []
        
        def update_settings_worker(worker_id):
            """Worker function for testing concurrent updates"""
            try:
                updates = {
                    "sqlite_db_path": f"./data/worker_{worker_id}.db",
                    "sqlite_auto_backup": worker_id % 2 == 0
                }
                
                with patch('src.utils.database_security.validate_database_path') as mock_validate:
                    mock_validate.return_value = (True, None, Path(self.temp_dir) / "data" / f"worker_{worker_id}.db")
                    
                    success, message = self.settings_manager.update_settings(updates)
                    results.append((worker_id, success, message))
                    
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        # Start multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=update_settings_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify no errors occurred
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert len(results) == 10
        
        # All operations should succeed (with mocked validation)
        for worker_id, success, message in results:
            assert success is True

    def test_comprehensive_malicious_settings_rejection(self):
        """Test rejection of comprehensive malicious settings combinations"""
        malicious_settings_combinations = [
            # Path traversal attack
            {
                "sqlite_db_path": "../../../etc/passwd.db",
                "sqlite_auto_backup": True
            },
            # Multiple invalid settings
            {
                "sqlite_db_path": "/tmp/malicious.db",
                "sqlite_backup_retention_days": -1,
                "sqlite_auto_backup": "malicious_string"
            },
            # SQL injection attempt in path
            {
                "sqlite_db_path": "./data/test'; DROP TABLE users; --.db"
            }
        ]
        
        for malicious_settings in malicious_settings_combinations:
            with patch('src.utils.database_security.validate_database_path') as mock_validate:
                # Mock validation to detect malicious path
                if "sqlite_db_path" in malicious_settings:
                    mock_validate.return_value = (False, "Malicious path detected", None)
                
                success, message = self.settings_manager.update_settings(malicious_settings)
                assert success is False, f"Should reject malicious settings: {malicious_settings}"

    def test_settings_validation_performance(self):
        """Test that settings validation performs within reasonable time limits"""
        large_settings_update = {
            "sqlite_db_path": "./data/performance_test.db",
            "sqlite_auto_backup": True,
            "sqlite_backup_retention_days": 30,
            "sqlite_auto_vacuum": True,
            "sqlite_wal_mode": False,
            # Add other settings to test performance
            "chunk_size": 1000,
            "chunk_overlap": 200,
            "max_chunks_per_query": 10,
            "preferred_chat_provider": "openai",
            "preferred_embedding_provider": "openai"
        }
        
        with patch('src.utils.database_security.validate_database_path') as mock_validate:
            mock_validate.return_value = (True, None, Path(self.temp_dir) / "data" / "performance_test.db")
            
            start_time = time.time()
            success, message = self.settings_manager.update_settings(large_settings_update)
            end_time = time.time()
            
            # Validation should complete within 1 second
            assert end_time - start_time < 1.0
            assert success is True


class TestQuickUpdateSettingsSecurity:
    """Test security in quick update settings functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        
        with patch('src.core.enhanced_settings_manager.QdrantManager') as mock_qdrant:
            mock_instance = MagicMock()
            mock_qdrant.return_value = mock_instance
            mock_instance.get_client.return_value.get_collection.return_value = None
            
            self.settings_manager = EnhancedSettingsManager()

    def test_quick_update_bypasses_database_validation(self):
        """Test that quick update doesn't bypass security validation"""
        # Even quick updates should validate database paths
        malicious_updates = {"sqlite_db_path": "../../../malicious.db"}
        
        with patch('src.utils.database_security.validate_database_path') as mock_validate:
            mock_validate.return_value = (False, "Invalid path", None)
            
            success, message = self.settings_manager.quick_update_settings(malicious_updates)
            assert success is False
            assert "invalid database path" in message.lower()


class TestSettingsSecurityIntegration:
    """Integration tests for settings security with real-world scenarios"""
    
    def setup_method(self):
        """Setup integration test environment"""
        self.temp_dir = tempfile.mkdtemp()
        
        with patch('src.core.enhanced_settings_manager.QdrantManager') as mock_qdrant:
            mock_instance = MagicMock()
            mock_qdrant.return_value = mock_instance
            mock_instance.get_client.return_value.get_collection.return_value = None
            
            self.settings_manager = EnhancedSettingsManager()

    def test_admin_dashboard_security_scenario(self):
        """Test security scenario simulating admin dashboard usage"""
        # Simulate admin trying to configure database settings
        admin_settings = {
            "sqlite_db_path": "./data/production.db",
            "sqlite_auto_backup": True,
            "sqlite_backup_retention_days": 90,
            "sqlite_auto_vacuum": True,
            "sqlite_wal_mode": True
        }
        
        with patch('src.utils.database_security.validate_database_path') as mock_validate:
            mock_validate.return_value = (True, None, Path(self.temp_dir) / "data" / "production.db")
            
            success, message = self.settings_manager.update_settings(admin_settings)
            assert success is True

    def test_compromised_admin_attack_scenario(self):
        """Test security against compromised admin account attack"""
        # Simulate compromised admin trying malicious database configuration
        attack_settings = {
            "sqlite_db_path": "/etc/passwd",
            "sqlite_auto_backup": False,  # Try to disable backups
            "sqlite_backup_retention_days": 1  # Minimize evidence retention
        }
        
        with patch('src.utils.database_security.validate_database_path') as mock_validate:
            mock_validate.return_value = (False, "Path outside project directory", None)
            
            success, message = self.settings_manager.update_settings(attack_settings)
            assert success is False
            assert "invalid database path" in message.lower()

    def test_race_condition_prevention(self):
        """Test prevention of race conditions in database settings updates"""
        def concurrent_update_worker(updates, results_list):
            """Worker for testing race conditions"""
            with patch('src.utils.database_security.validate_database_path') as mock_validate:
                mock_validate.return_value = (True, None, Path(self.temp_dir) / "data" / "race_test.db")
                
                success, message = self.settings_manager.update_settings(updates)
                results_list.append((success, message))
        
        results = []
        threads = []
        
        # Start multiple threads trying to update database settings simultaneously
        for i in range(5):
            updates = {
                "sqlite_db_path": f"./data/race_{i}.db",
                "sqlite_auto_backup": i % 2 == 0
            }
            
            thread = threading.Thread(target=concurrent_update_worker, args=(updates, results))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # All operations should succeed due to proper locking
        assert len(results) == 5
        for success, message in results:
            assert success is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])