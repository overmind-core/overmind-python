import json


def serialize(obj):
    return json.dumps(obj, default=lambda x: x.model_dump())
