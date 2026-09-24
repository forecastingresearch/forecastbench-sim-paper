"""Cached-reporting digest only; prompt construction remains restricted."""
import base64,hashlib

def prompt_hash(prompt: str) -> str:
    """Short stable digest of a prompt, used to detect a changed statement set.

    SHA-256 rather than hash(), which is randomized per process and so would
    differ between runs. The digest is urlsafe-base64 encoded and truncated to
    8 characters — enough to spot a changed prompt, and filename-safe.
    """
    digest = hashlib.sha256(prompt.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii")[:8]
