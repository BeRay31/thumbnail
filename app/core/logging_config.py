import sys
import json
from pathlib import Path
from typing import Dict, Any

def load_logging_config() -> Dict[str, Any]:
    """
    Load logging configuration from JSON file in project root.
    
    Returns:
        Dictionary containing logging configuration
    """
    # Go up to project root from app/core/
    project_root = Path(__file__).parent.parent.parent
    config_file = project_root / "logging_config.json"
    
    if not config_file.exists():
        raise FileNotFoundError(f"Logging config file not found: {config_file}")
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    # Convert ext://sys.stdout back to actual sys.stdout object for console handler
    if 'handlers' in config and 'console' in config['handlers']:
        if config['handlers']['console'].get('stream') == 'ext://sys.stdout':
            config['handlers']['console']['stream'] = sys.stdout
    
    return config

# Load the configuration from JSON file in project root
LOGGING_CONFIG: Dict[str, Any] = load_logging_config()
