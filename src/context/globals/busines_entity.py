"""
Global Business Entity Tree Definition.

This dictionary represents the hierarchical structure of business entities.
It will be used at application startup to populate the database with entities
and their hierarchical relationships.
"""

BUSINESS_ENTITY_TREE: dict = {"global": {"cash": {"current": {}, "custom": {}}}}
