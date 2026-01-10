import re
import json
import io
import zipfile

TITLE_RE = re.compile(
    r"<title[^>]*>(.*?)</title>",
    re.IGNORECASE | re.DOTALL
)

def extract_html_title(html_path):
    try:
        text = html_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None
    
    match = TITLE_RE.search(text)
    if not match:
        return None
    
    title = match.group(1).strip()
    return re.sub(r"\s+", " ", title) if title else None

def pick_entry_html(build_dir, requested=None):
    if requested:
        p = build_dir / requested
        if p.exists():
            return p
    
    idx = build_dir / "index.html"
    if idx.exists():
        return idx
    
    htmls = sorted(build_dir.rglob("*.html"))
    if htmls:
        return htmls[0]
    
    raise FileNotFoundError("No HTML entry point found")

def write_manifest_and_shim(staging_dir, entry_path, title, window):
    rel_entry = entry_path.relative_to(staging_dir).as_posix()

    manifest = {
        "entry": rel_entry,
        "title": title,
        "window": window,
    }

    (staging_dir / "messiah.app.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8"
    )

    idx = staging_dir / "index.html"
    if rel_entry != "index.html":
        idx.write_text(
            "<!doctype html><meta charset'utf-8'>"
            f"<meta http-equiv'refresh' content='0; url./{rel_entry}'>"
            "<title>Launching...</title>",
            encoding="utf-8"
        )

def zip_dir_to_bytes(root):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for path in root.rglob("*"):
            if path.is_file():
                z.write(path, path.relative_to(root))
    return buf.getvalue()