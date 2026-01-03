import time
import webbrowser
import shutil
from pathlib import Path
from config import CURRENT_BUILD, START_TIME, LAN_MODE, DEFAULT_HTML, WEB_PREVIEW_DIR
from state import get_build_dir, set_build_dir

def _stage_build(build_dir: Path) -> Path:
    if WEB_PREVIEW_DIR.exists():
        shutil.rmtree(WEB_PREVIEW_DIR)
    
    WEB_PREVIEW_DIR.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(build_dir, WEB_PREVIEW_DIR)
    return WEB_PREVIEW_DIR

def _open_html(html: Path, source: str):
    webbrowser.open(html.resolve().as_uri())
    return {
        "ok": True,
        "source": source,
        "path": str(html)
    }

def cmd_handshake(_data):
    return {
        "runtime": "Messiah",
        "version": CURRENT_BUILD,
        "lan_mode": LAN_MODE,
        "uptime_sec": int(time.time() - START_TIME),
        "build_dir": str(get_build_dir())
    }

def cmd_get_version(_data):
    return {"version": CURRENT_BUILD}

def cmd_list_commands(_data):
    return {"commands": sorted(COMMANDS.keys())}

def cmd_get_build_dir(_data):
    return {
        "build_dir": str(get_build_dir())
    }

def cmd_set_build_dir(data):
    path = data.get("path")
    if not path:
        raise ValueError("Missing 'path'")
    
    new_dir = set_build_dir(path)
    return {
        "build_dir": str(new_dir)
    }

def cmd_test_web_build(data):
    path = data.get("path")
    if path:
        p = Path(path)
        if p.exists() and p.suffix.lower() == ".html":
            return _open_html(p, "explicit")
    
    build_dir = Path(get_build_dir())
    if not build_dir.exists():
        if DEFAULT_HTML.exists():
            return _open_html(DEFAULT_HTML, "default")
        raise FileNotFoundError("[Error] Build directory does not exist")
    
    staged = _stage_build(build_dir)

    index = staged / "index.html"
    if index.exists():
        return _open_html(index, "staged:index")
    
    html_files = sorted(staged.rglob("*.html"))
    if html_files:
        return _open_html(html_files[0], "staged:first_html")
    
    if DEFAULT_HTML.exists():
        return _open_html(DEFAULT_HTML, "default")
    
    raise FileNotFoundError(
        "[Error] No HTML file found (explicit, staged build, or default)"
    )

COMMANDS = {
    "handshake": cmd_handshake,
    "get_version": cmd_get_version,
    "list_commands": cmd_list_commands,
    "get_build_dir": cmd_get_build_dir,
    "set_build_dir": cmd_set_build_dir,
    "test_web_build": cmd_test_web_build
}