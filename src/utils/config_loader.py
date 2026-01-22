from pathlib import Path
import configparser

def get_project_root() -> Path:
    """
    Always resolves project root regardless of:
    - Streamlit
    - CLI
    - Module execution
    """
    return Path(__file__).resolve().parents[2]

def load_config():
    project_root = get_project_root()
    config_path = project_root / "config" / "config.ini"

    if not config_path.exists():
        raise FileNotFoundError(f"Config not found at {config_path}")

    config = configparser.ConfigParser()
    config.read(config_path)

    return config, project_root

if __name__ == "__main__":
    config, project_root = load_config()
    print(f"Config loaded from {project_root / 'config' / 'config.ini'}")