import hashlib


def sha256_digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def format_document_hash(digest: str) -> str:
    return f"sha256:{digest.removeprefix('sha256:')}"