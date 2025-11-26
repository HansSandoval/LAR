"""Database module"""
from .db import execute_query, execute_query_one, execute_insert_returning, execute_insert_update_delete

# Dummy Base class for backward compatibility with old ORM models
# (not used anymore - we use PostgreSQL direct queries now)
class Base:
    pass

__all__ = ['execute_query', 'execute_query_one', 'execute_insert_returning', 'execute_insert_update_delete', 'Base']
