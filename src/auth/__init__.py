"""
Authentication Package

This package provides authentication and authorization functionality for the Zenith AI system,
including JWT-based sessions, user management, and enterprise-grade security features.
"""

from .auth_manager import AuthenticationManager

try:
    from .enterprise_auth_manager import initialize_enterprise_auth, get_enterprise_auth_manager
    __all__ = ['AuthenticationManager', 'initialize_enterprise_auth', 'get_enterprise_auth_manager']
except ImportError:
    # Enterprise auth not available
    __all__ = ['AuthenticationManager']
