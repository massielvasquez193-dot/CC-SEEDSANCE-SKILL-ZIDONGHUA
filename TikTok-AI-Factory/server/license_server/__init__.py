"""
License Server — Online authorization and client management.
"""
from .database import Database
from .license_api import app, create_app

__all__ = ["Database", "app", "create_app"]
