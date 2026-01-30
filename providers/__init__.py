"""
Image Source Provider System

This module provides a plugin-based architecture for integrating
external image sources with the slideshow application.
"""

from typing import Dict, Type, List, Optional, Any
from .base import BaseImageProvider

# Provider registry
_PROVIDERS: Dict[str, Type[BaseImageProvider]] = {}


def register_provider(provider_class: Type[BaseImageProvider]) -> Type[BaseImageProvider]:
    """
    Register a provider class in the registry.
    Can be used as a decorator or called directly.
    
    Args:
        provider_class: The provider class to register
        
    Returns:
        The same provider class (for decorator usage)
    """
    _PROVIDERS[provider_class.name] = provider_class
    return provider_class


def get_provider(name: str) -> Optional[BaseImageProvider]:
    """
    Get an instance of a registered provider by name.
    
    Args:
        name: The unique provider identifier
        
    Returns:
        A new instance of the provider, or None if not found
    """
    if name in _PROVIDERS:
        return _PROVIDERS[name]()
    return None


def list_providers() -> List[str]:
    """
    List all registered provider names.
    
    Returns:
        List of provider identifiers
    """
    return list(_PROVIDERS.keys())


def get_all_providers() -> Dict[str, BaseImageProvider]:
    """
    Get instances of all registered providers.
    
    Returns:
        Dictionary mapping provider names to instances
    """
    return {name: cls() for name, cls in _PROVIDERS.items()}


def get_provider_info(name: str) -> Optional[Dict[str, Any]]:
    """
    Get metadata about a provider without full instantiation.
    
    Args:
        name: The unique provider identifier
        
    Returns:
        Dictionary with provider metadata, or None if not found
    """
    if name in _PROVIDERS:
        cls = _PROVIDERS[name]
        return {
            "name": cls.name,
            "display_name": cls.display_name,
            "description": getattr(cls, 'description', ''),
        }
    return None


# Auto-register built-in providers
from .immich import ImmichProvider
register_provider(ImmichProvider)
