import json
from pathlib import PurePath

_MAX_ATTR_LEN = 32_000


def _default_serializer(obj):
    if isinstance(obj, PurePath):
        return str(obj)
    if isinstance(obj, (set, frozenset)):
        return list(obj)
    if isinstance(obj, bytes):
        return obj.hex()
    if hasattr(obj, "model_dump"):
        try:
            return obj.model_dump()
        except Exception:
            pass
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
    return repr(obj)


def serialize(obj) -> str:
    try:
        raw = json.dumps(obj, default=_default_serializer, ensure_ascii=False)
    except (TypeError, ValueError, OverflowError):
        raw = repr(obj)

    if len(raw) > _MAX_ATTR_LEN:
        return raw[:_MAX_ATTR_LEN] + "…[truncated]"
    return raw
