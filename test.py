import sys
import os
from pathlib import Path

def test_loguru_import():
    """Test if loguru can be imported"""
    print("🔍 Testing loguru import...")

    try:
        import loguru
        print("✅ loguru imported successfully")
        return True, loguru
    except ImportError as e:
        print(f"❌ Failed to import loguru: {e}")
        print("💡 Install with: pip install loguru")
        return False, None
    except Exception as e:
        print(f"❌ Unexpected error importing loguru: {e}")
        return False, None

def test_loguru_version(loguru_module):
    """Test loguru version information"""
    print("\n📋 Checking loguru version...")

    try:
        version = getattr(loguru_module, '__version__', 'Unknown')
        print(f"✅ loguru version: {version}")
        return True
    except Exception as e:
        print(f"⚠️  Could not get version info: {e}")
        return False

def test_basic_logger_functionality(loguru_module):
    """Test basic logger functionality"""
    print("\n🧪 Testing basic logger functionality...")

    try:
        from loguru import logger

        # Test basic logging levels
        logger.info("Test info message")
        logger.warning("Test warning message")
        logger.error("Test error message")

        print("✅ Basic logging functions work")
        return True
    except Exception as e:
        print(f"❌ Logger functionality test failed: {e}")
        return False

def test_logger_configuration(loguru_module):
    """Test logger configuration"""
    print("\n⚙️  Testing logger configuration...")

    try:
        from loguru import logger

        # Remove default handler
        logger.remove()

        # Add custom handler
        logger.add(
            sys.stdout,
            format="{time} | {level} | {message}",
            level="INFO"
        )

        logger.info("Test configured logger")

        print("✅ Logger configuration works")
        return True
    except Exception as e:
        print(f"❌ Logger configuration test failed: {e}")
        return False

def test_file_logging():
    """Test file logging capability"""
    print("\n📁 Testing file logging...")

    try:
        from loguru import logger

        # Create test log file
        test_log = Path("test_loguru.log")

        # Remove existing test log
        if test_log.exists():
            test_log.unlink()

        # Configure file logging
        logger.remove()
        logger.add(
            str(test_log),
            format="{time} | {level} | {message}",
            level="DEBUG"
        )

        logger.info("Test file logging message")
        logger.debug("Test debug message")

        # Check if file was created and has content
        if test_log.exists() and test_log.stat().st_size > 0:
            print(f"✅ File logging works - created {test_log}")

            # Show log content
            content = test_log.read_text()
            print(f"📄 Log content preview:\n{content[:200]}...")

            # Clean up
            test_log.unlink()
            return True
        else:
            print("❌ File logging failed - no log file created")
            return False

    except Exception as e:
        print(f"❌ File logging test failed: {e}")
        return False

def test_zenith_logger_integration():
    """Test integration with Zenith's logger pattern"""
    print("\n🚀 Testing Zenith logger integration pattern...")

    try:
        from loguru import logger

        # Simulate Zenith's logger pattern
        def get_logger(name):
            """Simulate Zenith's get_logger function"""
            return logger.bind(module=name)

        # Test the pattern
        test_logger = get_logger(__name__)
        test_logger.info("Test Zenith logger pattern")

        print("✅ Zenith logger pattern works")
        return True
    except Exception as e:
        print(f"❌ Zenith logger integration test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Loguru Installation and Import Test")
    print("=" * 50)

    # Test import
    import_success, loguru_module = test_loguru_import()
    if not import_success:
        print("\n❌ Cannot proceed - loguru not available")
        return False

    # Run all tests
    tests = [
        (test_loguru_version, loguru_module),
        (test_basic_logger_functionality, loguru_module),
        (test_logger_configuration, loguru_module),
        (test_file_logging, ),
        (test_zenith_logger_integration, )
    ]

    passed = 0
    total = len(tests) + 1  # +1 for import test

    if import_success:
        passed += 1

    for test_func, *args in tests:
        try:
            if test_func(*args):
                passed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")

    # Results summary
    print(f"\n📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All loguru tests passed! Installation is working correctly.")
        return True
    else:
        print(f"⚠️  {total - passed} test(s) failed. Loguru may not be working properly.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)