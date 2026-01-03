from pathlib import Path
from config import DEFAULT_BUILD_DIR

_build_dir = DEFAULT_BUILD_DIR

def get_build_dir() -> Path:
    return _build_dir

def set_build_dir(path: str) -> Path:
    global _build_dir
    p = Path(path).expanduser().resolve()
    _build_dir = p
    return _build_dir