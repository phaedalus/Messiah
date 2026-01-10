import time
import json
import webbrowser
import shutil
import tempfile
from pathlib import Path

from helpers import (
    pick_entry_html, 
    extract_html_title, 
    write_manifest_and_shim,
    zip_dir_to_bytes
)
from config import (
    CURRENT_BUILD, START_TIME, LAN_MODE,
    DEFAULT_HTML, WEB_PREVIEW_DIR, MAGIC
)
from state import (
    get_build_dir,
    set_build_dir,
    get_export_dir,
    set_export_dir
)

def _stage_build(build_dir: Path) -> Path:
    if WEB_PREVIEW_DIR.exists():
        shutil.rmtree(WEB_PREVIEW_DIR)
    
    WEB_PREVIEW_DIR.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(build_dir, WEB_PREVIEW_DIR)
    return WEB_PREVIEW_DIR

def _open_html(html: Path, source: str):
    webbrowser.open(html.resolve().as_uri())
    return { "ok": True, "source": source, "path": str(html) }

def _pick_entry_html(root: Path) -> Path | None:
    idx = root / "index.html"
    if idx.exists():
        return idx
    html_files = sorted(root.rglob("*html"))
    return html_files[0] if html_files else None

def _ensure_index_html(root: Path) -> Path:
    idx = root / "index.html"
    if idx.exists():
        return idx
    
    first = _pick_entry_html(root)
    if first:
        shutil.copy2(first, idx)
        return idx
    
    if DEFAULT_HTML.exists():
        shutil.copy2(DEFAULT_HTML, idx)
        return idx
    
    raise FileNotFoundError("No HTML entry point found at DEFAULT_HTML missing")

def _write_manifest(export_dir: Path, kind: str, extra: dict | None = None):
    data = {
        "tool": "Messiah",
        "kind": kind,
        "version": CURRENT_BUILD,
        "created_at": int(time.time()),
        "entry": "index.html"
    }
    if extra:
        data.update(extra)
    (export_dir / "export.json").write_text(json.dumps(data, indent=2), encoding="utf-8")

def _zip_folder(folder: Path, out_zip: Path) -> Path:
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    base = str(out_zip.with_suffix(""))
    archive_path = shutil.make_archive(base, "zip", root_dir=str(folder))
    return Path(archive_path)

def cmd_handshake(_data):
    return {
        "runtime": "Messiah",
        "version": CURRENT_BUILD,
        "lan_mode": LAN_MODE,
        "uptime_sec": int(time.time() - START_TIME),
        "build_dir": str(get_build_dir()),
        "protocol": { "format": "newline-json", "version": 1, "language": "python" }
    }

def cmd_get_version(_data):
    return {"version": CURRENT_BUILD}

def cmd_list_commands(_data):
    return {"commands": sorted(COMMANDS.keys())}

def cmd_get_build_dir(_data):
    return { "build_dir": str(get_build_dir()) }

def cmd_set_build_dir(data):
    path = data.get("path")
    if not path:
        raise ValueError("Missing 'path'")
    new_dir = set_build_dir(path)
    return { "build_dir": str(new_dir) }

def cmd_get_export_dir(_data):
    return {"export_dir": str(get_export_dir())}

def cmd_set_export_dir(data):
    path = data.get("path")
    if not path:
        raise ValueError("Missing 'path'")
    new_dir = set_export_dir(path)
    return {"export_dir": str(new_dir)}

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
    entry = _ensure_index_html(staged)
    return _open_html(entry, "staged:index")

def cmd_export_web(data):
    build_dir = Path(get_build_dir())
    if not build_dir.exists():
        raise FileNotFoundError("Build directory does not exist")

    out_dir = Path(data.get("out_dir") or get_export_dir()).expanduser().resolve()
    name = data.get("name") or f"web-export-{int(time.time())}"
    export_dir = out_dir / name

    if export_dir.exists():
        shutil.rmtree(export_dir)

    export_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(build_dir, export_dir)

    entry = _ensure_index_html(export_dir)
    _write_manifest(export_dir, "web", {"source_build_dir": str(build_dir)})

    zip_path = None
    if bool(data.get("zip")):
        zip_path = _zip_folder(export_dir, export_dir.with_suffix(".zip"))

    return {
        "export_dir": str(export_dir),
        "entry": str(entry),
        "zip": str(zip_path) if zip_path else None
    }

def cmd_export_desktop(data):
    build_dir = Path(get_build_dir())
    if not build_dir.exists():
        raise FileNotFoundError("Build directory does not exist")
    
    out_dir = Path(data.get("out_dir") or get_export_dir())
    name = data.get("name", "App")

    stub = Path("runtimes/windows/pywebview/webview_stub.exe")
    if not stub.exists():
        raise FileNotFoundError("pywebview stub not found")
    
    entry = pick_entry_html(build_dir, data.get("entry"))
    
    title = data.get("title")
    if not title:
        title = extract_html_title(entry) or name
    
    window = data.get("window") or {}

    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp)
        shutil.copytree(build_dir, stage, dirs_exist_ok=True)

        write_manifest_and_shim(stage, entry, title, window)
        
        zip_bytes = zip_dir_to_bytes(stage)
    
    out_dir.mkdir(parents=True, exist_ok=True)
    out_exe = out_dir / f"{name}.exe"

    shutil.copy2(stub, out_exe)

    with open(out_exe, "ab") as f:
        f.write(zip_bytes)
        f.write(MAGIC)
        f.write(len(zip_bytes).to_bytes(8, "little"))
    
    return {
        "exe": str(out_exe),
        "title": title,
        "entry": entry.name,
        "mode": "native-singlefile-pywebview"
    }


COMMANDS = {
    "handshake": cmd_handshake,
    "get_version": cmd_get_version,
    "list_commands": cmd_list_commands,
    "get_build_dir": cmd_get_build_dir,
    "set_build_dir": cmd_set_build_dir,
    "get_export_dir": cmd_get_export_dir,
    "set_export_dir": cmd_set_export_dir,
    "test_web_build": cmd_test_web_build,
    "export_web_build": cmd_export_web
}