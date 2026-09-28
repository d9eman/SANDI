from __future__ import annotations

import hashlib
import secrets

_WORDS = (
    "anchor", "apple", "beacon", "bird", "bridge", "cactus", "candle", "cedar",
    "cloud", "coral", "dawn", "eagle", "ember", "field", "garden", "harbor",
    "hill", "island", "juniper", "lake", "maple", "meadow", "moon", "ocean",
    "olive", "orchid", "pebble", "pine", "river", "sage", "shell", "star",
    "stone", "sunset", "trail", "valley", "willow", "wind", "yellow", "zinnia",
)


def generate_recovery_phrase() -> str:
    return "-".join(secrets.choice(_WORDS) for _ in range(4))


def hash_recovery_phrase(phrase: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", normalize(phrase).encode("utf-8"), salt, 200_000)
    return f"{salt.hex()}${digest.hex()}"


def verify_recovery_phrase(phrase: str, encoded: str) -> bool:
    try:
        salt_hex, expected_hex = encoded.split("$", 1)
        digest = hashlib.pbkdf2_hmac("sha256", normalize(phrase).encode("utf-8"), bytes.fromhex(salt_hex), 200_000)
        return secrets.compare_digest(digest.hex(), expected_hex)
    except (ValueError, TypeError):
        return False


def normalize(phrase: str) -> str:
    return phrase.strip().lower().replace(" ", "-")
