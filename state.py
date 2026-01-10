from pathlib import Path
from config import DEFAULT_BUILD_DIR, EXPORTS_DIR

_build_dir = DEFAULT_BUILD_DIR
_export_dir = EXPORTS_DIR

def get_build_dir() -> Path:
    return _build_dir

def set_build_dir(path: str) -> Path:
    global _build_dir
    p = Path(path).expanduser().resolve()
    _build_dir = p
    return _build_dir

def get_export_dir() -> Path:
    return _export_dir

def set_export_dir(path: str) -> Path:
    global _export_dir
    p = Path(path).expanduser().resolve()
    _export_dir = p
    return _export_dir