def make_error(code, message, *, hint=None, request_id=None, details=None):
    err = {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
        }
    }
    if hint:
        err["error"]["hint"] = hint
    if details:
        err["error"]["details"] = details
    if request_id:
        err["request_id"] = request_id
    return err


def make_ok(data=None, *, request_id=None):
    res = {"ok": True}
    if data is not None:
        res["data"] = data
    if request_id:
        res["request_id"] = request_id
    return res
