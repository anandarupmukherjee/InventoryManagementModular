import os
import yaml

def load_enabled_modules():
    # Support loading from config/module_config.yaml relative to project root
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "module_config.yaml")

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config.get("enabled_modules", [])
    except Exception as e:
        print(f"⚠️ Could not load module config: {e}")
        return []
