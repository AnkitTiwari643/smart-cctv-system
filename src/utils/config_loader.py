"""
Configuration loader utility.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from loguru import logger


class ConfigLoader:
    """Configuration manager for the Smart CCTV System."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize configuration loader.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.load()
    
    def load(self):
        """Load configuration from YAML file."""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
            
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            
            # Replace environment variable placeholders
            self._resolve_env_vars(self.config)
            
            logger.info(f"Configuration loaded from {self.config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _resolve_env_vars(self, obj):
        """Recursively resolve environment variable placeholders."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                    env_var = value[2:-1]
                    obj[key] = os.getenv(env_var, value)
                elif isinstance(value, (dict, list)):
                    self._resolve_env_vars(value)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, str) and item.startswith("${") and item.endswith("}"):
                    env_var = item[2:-1]
                    obj[i] = os.getenv(env_var, item)
                elif isinstance(item, (dict, list)):
                    self._resolve_env_vars(item)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot notation key.
        
        Args:
            key: Configuration key (e.g., 'system.log_level')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        Set configuration value by dot notation key.
        
        Args:
            key: Configuration key (e.g., 'system.log_level')
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self, path: Optional[str] = None):
        """
        Save configuration to file.
        
        Args:
            path: Output path (default: original config path)
        """
        output_path = Path(path) if path else self.config_path
        
        try:
            with open(output_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"Configuration saved to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise
    
    def validate(self) -> bool:
        """
        Validate configuration.
        
        Returns:
            True if valid, False otherwise
        """
        required_keys = [
            'system.name',
            'system.data_dir',
            'cameras',
            'processing.detection.model',
            'alert_rules'
        ]
        
        for key in required_keys:
            if self.get(key) is None:
                logger.error(f"Missing required configuration key: {key}")
                return False
        
        # Validate cameras
        cameras = self.get('cameras', [])
        if not cameras:
            logger.error("No cameras configured")
            return False
        
        for cam in cameras:
            if 'id' not in cam or 'url' not in cam:
                logger.error(f"Invalid camera configuration: {cam}")
                return False
        
        logger.success("Configuration validation passed")
        return True
