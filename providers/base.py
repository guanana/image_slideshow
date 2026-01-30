"""
Base Image Provider Interface

Defines the abstract base class that all image source providers must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class RefreshStatus(Enum):
    """Status of a refresh operation."""
    SUCCESS = "success"
    PARTIAL = "partial"  # Some images failed
    FAILED = "failed"
    NO_IMAGES = "no_images"


@dataclass
class RefreshResult:
    """Result of a provider refresh operation."""
    status: RefreshStatus
    message: str
    downloaded: int = 0
    skipped: int = 0
    failed: int = 0
    total: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "status": self.status.value,
            "message": self.message,
            "downloaded": self.downloaded,
            "skipped": self.skipped,
            "failed": self.failed,
            "total": self.total,
            "errors": self.errors,
        }


@dataclass
class ConfigField:
    """Definition of a configuration field for a provider."""
    key: str
    label: str
    field_type: str  # "text", "password", "select", "number", "boolean"
    required: bool = True
    default: Any = None
    description: str = ""
    options: List[Dict[str, str]] = None  # For select type: [{"value": "x", "label": "X"}]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "key": self.key,
            "label": self.label,
            "type": self.field_type,
            "required": self.required,
            "default": self.default,
            "description": self.description,
        }
        if self.options:
            result["options"] = self.options
        return result


class BaseImageProvider(ABC):
    """
    Abstract base class for all image source providers.
    
    Subclasses must define `name` and `display_name` class attributes,
    and implement all abstract methods.
    """
    
    # Unique identifier for this provider (e.g., "immich", "google_photos")
    name: str = ""
    
    # Human-readable display name
    display_name: str = ""
    
    # Optional description
    description: str = ""
    
    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._last_result: Optional[RefreshResult] = None
    
    @abstractmethod
    def get_config_fields(self) -> List[ConfigField]:
        """
        Return the configuration fields required by this provider.
        
        Returns:
            List of ConfigField objects describing each setting
        """
        pass
    
    @abstractmethod
    def configure(self, settings: Dict[str, Any]) -> None:
        """
        Apply configuration settings to this provider.
        
        Args:
            settings: Dictionary of setting key-value pairs
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> Tuple[bool, Optional[str]]:
        """
        Validate the current configuration.
        
        Returns:
            Tuple of (is_valid, error_message). error_message is None if valid.
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test the connection to the external service.
        
        Returns:
            Tuple of (success, message)
        """
        pass
    
    @abstractmethod
    def refresh(self, target_folder: str) -> RefreshResult:
        """
        Download/sync images to the target folder.
        
        Args:
            target_folder: Absolute path to the destination folder
            
        Returns:
            RefreshResult with download statistics
        """
        pass
    
    def get_config(self) -> Dict[str, Any]:
        """Get the current configuration (excluding sensitive fields)."""
        # Subclasses can override to hide passwords
        return self._config.copy()
    
    def get_last_result(self) -> Optional[RefreshResult]:
        """Get the result of the last refresh operation."""
        return self._last_result
    
    def get_config_schema(self) -> List[Dict[str, Any]]:
        """Get the configuration schema as a list of dictionaries."""
        return [field.to_dict() for field in self.get_config_fields()]
