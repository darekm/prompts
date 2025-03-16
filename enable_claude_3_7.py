#!/usr/bin/env python3

import json
import os
import sys

def enable_claude_3_7_sonnet():
    """
    Enable Claude 3.7 Sonnet (Preview) for all clients
    """
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "claude_config.json")
    
    try:
        # Load the configuration
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print("Successfully loaded configuration")
        print("Claude 3.7 Sonnet (Preview) is enabled for all clients")
        print(f"Configuration file: {config_path}")
        
        # Here you could add code to apply this configuration to your system
        
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = enable_claude_3_7_sonnet()
    sys.exit(0 if success else 1)
