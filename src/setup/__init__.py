"""
Enterprise Setup Package

This package contains enterprise-grade setup functionality for the Zenith AI system,
including initial deployment, configuration management, and security setup.
"""

from .enterprise_setup import run_enterprise_setup, check_enterprise_setup_status

__all__ = ['run_enterprise_setup', 'check_enterprise_setup_status']
