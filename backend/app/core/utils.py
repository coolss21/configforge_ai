import hashlib
import json

def generate_hash(data: dict) -> str:
    normalized = json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
