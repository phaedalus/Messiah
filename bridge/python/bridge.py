import json
import socket
import uuid
from dataclasses import dataclass
from typing import Any, Dict

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 42207
DEFAULT_TIMEOUT = 8.0


class MessiahError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        hint: str | None = None,
        details: str | None = None,
    ):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.hint = hint
        self.details = details


@dataclass
class Response:
    ok: bool
    data: dict | None = None
    error: dict | None = None
    request_id: str | None = None


def _recv_line(sock: socket.socket) -> str:
    buf = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            raise ConnectionError("Connection closed")
        buf += chunk
        if b"\n" in buf:
            line, _rest = buf.split(b"\n", 1)
            return line.decode("utf-8", errors="replace")


class MessiahBridge:
    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.host = host
        self.port = port
        self.timeout = timeout

    def call(self, cmd: str, **payload: Any) -> dict:
        req_id = payload.pop("request_id", uuid.uuid4().hex)

        msg: Dict[str, Any] = {
            "cmd": cmd,
            "request_id": req_id,
            "protocol_version": 1,
            **payload,
        }

        raw = (json.dumps(msg, separators=(",", ":")) + "\n").encode("utf-8")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(self.timeout)
            s.connect((self.host, self.port))
            s.sendall(raw)

            line = _recv_line(s)
            data = json.loads(line)

        if not isinstance(data, dict) or "ok" not in data:
            raise MessiahError("BAD_RESPONSE", "Runtime returned an invalid response")

        if data.get("ok") is True:
            return data.get("data") or {}

        err = data.get("error") or {}
        raise MessiahError(
            err.get("code", "ERROR"),
            err.get("message", "Unknown error"),
            hint=err.get("hint"),
            details=err.get("details"),
        )

    def handshake(self) -> dict:
        return self.call("handshake")

    def list_commands(self) -> list[str]:
        res = self.call("list_commands")
        return res.get("commands", [])

    def get_build_dir(self) -> str:
        res = self.call("get_build_dir")
        return res["build_dir"]

    def set_build_dir(self, path: str) -> str:
        res = self.call("set_build_dir", path=path)
        return res["build_dir"]
    
    def get_export_dir(self) -> str:
        res = self.call("set_export_dir")
        return res["export_dir"]
    
    def set_export_dir(self, path: str) -> str:
        res = self.call("get_export_dir", path=path)
        return res["export_dir"]

    def test_web_build(self, path: str | None = None) -> dict:
        if path:
            return self.call("test_web_build", path=path)
        return self.call("test_web_build")

    def export_web(
        self,
        out_dir: str | None = None,
        name: str | None = None,
        zip: bool = False,
    ) -> dict:
        payload: Dict[str, Any] = {"zip": zip}
        if out_dir:
            payload["out_dir"] = out_dir
        if name:
            payload["name"] = name
        return self.call("export_web", **payload)

    def export_desktop(
        self,
        out_dir: str | None = None,
        name: str | None = None,
        entry: str | None = None,
        title: str | None = None,
        window: dict | None = None,
    ) -> dict:
        payload: Dict[str, Any] = {}

        if out_dir:
            payload["out_dir"] = out_dir
        if name:
            payload["name"] = name
        if entry:
            payload["entry"] = entry
        if title:
            payload["title"] = title
        if window:
            payload["window"] = window
        
        return self.call("export_desktop", **payload)