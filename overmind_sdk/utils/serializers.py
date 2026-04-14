import json


def _default_serializer(obj):
    if hasattr(obj, "model_dump"):
        try:
            return obj.model_dump()
        except Exception:
            pass
    if hasattr(obj, "__dict__"):
        return str(obj)
    return str(obj)


def serialize(obj):
    return json.dumps(obj, default=_default_serializer)
