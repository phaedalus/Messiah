import os
import time
from pathlib import Path

CURRENT_BUILD = "Messiah Runtime V0.1"
START_TIME = time.time()
LAN_MODE = os.getenv("MESSIAH_LAN", "0") == "1"
PORT = int(os.getenv("MESSIAH_PORT", "42207"))
DEFAULT_BUILD_DIR = Path(os.getenv("MESSIAH_BUILD_DIR", "./build")).resolve()
DEFAULT_HTML = Path(__file__).parent / "default.html"
WEB_PREVIEW_DIR = Path(".messiah/web_preview/current")