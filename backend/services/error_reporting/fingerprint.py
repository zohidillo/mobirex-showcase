import hashlib


def compute_fingerprint(source, error_type, request_path, status_code, kind):
    raw = "|".join([
        str(source or ""),
        str(error_type or ""),
        str(request_path or ""),
        str(status_code or ""),
        str(kind or ""),
    ])
    return hashlib.sha256(raw.encode()).hexdigest()[:64]
