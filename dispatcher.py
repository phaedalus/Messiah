import json
import traceback
from protocol import make_error, make_ok
from commands import COMMANDS

def handle_message(message: str) -> str:
    try:
        data = json.loads(message)
    except json.JSONDecodeError as e:
        return json.dumps(make_error(
            "INVALID_JSON",
            "Failed to parse JSON",
            hint="Ensure the payload is valid JSON and newline-terminated",
            details=str(e)
        ))

    if not isinstance(data, dict):
        return json.dumps(make_error(
            "INVALID_PAYLOAD",
            "JSON payload must be an object"
        ))

    request_id = data.get("request_id")
    cmd = data.get("cmd")

    if not cmd:
        return json.dumps(make_error(
            "MISSING_CMD",
            "No 'cmd' field provided",
            request_id=request_id
        ))

    handler = COMMANDS.get(cmd.lower())
    if not handler:
        return json.dumps(make_error(
            "UNKNOWN_CMD",
            f"Command '{cmd}' is not registered",
            request_id=request_id
        ))

    try:
        result = handler(data)
        return json.dumps(make_ok(result, request_id=request_id))
    except Exception:
        return json.dumps(make_error(
            "INTERNAL_ERROR",
            "Command execution failed",
            details=traceback.format_exc(),
            request_id=request_id
        ))