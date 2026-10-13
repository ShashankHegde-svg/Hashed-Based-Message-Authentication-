"""
hmac_core.py
------------
HMAC-SHA256 implemented from first principles, following RFC 2104.

Only the SHA-256 compression function is taken from the standard library
(hashlib). The HMAC construction itself -- key padding, the inner and outer
pads, the two-pass hashing -- is written out explicitly so the algorithm is
visible and auditable.

        HMAC(K, m) = H( (K' XOR opad) || H( (K' XOR ipad) || m ) )

where K' is the secret key adjusted to exactly one hash block (64 bytes for
SHA-256), ipad is the byte 0x36 repeated, and opad is the byte 0x5C repeated.
"""

import hashlib
import secrets

BLOCK_SIZE = 64      # SHA-256 processes 512-bit (64-byte) blocks
DIGEST_SIZE = 32     # SHA-256 produces a 256-bit (32-byte) digest
IPAD_BYTE = 0x36
OPAD_BYTE = 0x5C


def sha256(data: bytes) -> bytes:
    """The underlying hash function H. This is the only borrowed primitive."""
    return hashlib.sha256(data).digest()


def normalise_key(key: bytes) -> tuple[bytes, str]:
    """
    Turn a key of any length into K', exactly BLOCK_SIZE bytes long.

    RFC 2104 defines three cases:
      - longer than a block  -> hash it down, then zero-pad
      - shorter than a block -> zero-pad on the right
      - exactly a block      -> use as is
    """
    if len(key) > BLOCK_SIZE:
        key = sha256(key)
        note = f"key was longer than {BLOCK_SIZE} bytes, so it was hashed down to {DIGEST_SIZE} bytes first"
    elif len(key) < BLOCK_SIZE:
        note = f"key was shorter than {BLOCK_SIZE} bytes, so it was padded on the right with zero bytes"
    else:
        note = f"key was already exactly {BLOCK_SIZE} bytes, so it was used unchanged"

    return key.ljust(BLOCK_SIZE, b"\x00"), note


def xor_with_byte(block: bytes, pad_byte: int) -> bytes:
    """XOR every byte of the block with a single repeated pad byte."""
    return bytes(b ^ pad_byte for b in block)


def hmac_sha256(key: bytes, message: bytes) -> bytes:
    """Return the 32-byte HMAC-SHA256 tag for a message under a secret key."""
    key_prime, _ = normalise_key(key)
    inner = sha256(xor_with_byte(key_prime, IPAD_BYTE) + message)
    return sha256(xor_with_byte(key_prime, OPAD_BYTE) + inner)


def hmac_sha256_traced(key: bytes, message: bytes) -> dict:
    """
    Same computation as hmac_sha256, but returns every intermediate value
    so the steps can be displayed in the interface.
    """
    key_prime, key_note = normalise_key(key)
    inner_key = xor_with_byte(key_prime, IPAD_BYTE)
    outer_key = xor_with_byte(key_prime, OPAD_BYTE)
    inner_digest = sha256(inner_key + message)
    tag = sha256(outer_key + inner_digest)

    return {
        "tag": tag.hex(),
        "steps": [
            {
                "label": "Prepare the key (K')",
                "detail": key_note,
                "value": key_prime.hex(),
            },
            {
                "label": "K' XOR ipad",
                "detail": "every byte of K' exclusive-ORed with 0x36",
                "value": inner_key.hex(),
            },
            {
                "label": "Inner hash",
                "detail": "SHA-256 of (K' XOR ipad) followed by the message",
                "value": inner_digest.hex(),
            },
            {
                "label": "K' XOR opad",
                "detail": "every byte of K' exclusive-ORed with 0x5C",
                "value": outer_key.hex(),
            },
            {
                "label": "Outer hash — the MAC",
                "detail": "SHA-256 of (K' XOR opad) followed by the inner hash",
                "value": tag.hex(),
            },
        ],
    }


def constant_time_equals(a: bytes, b: bytes) -> bool:
    """
    Compare two byte strings without leaking where they first differ.

    A normal == returns as soon as it hits a mismatch, so an attacker can time
    repeated guesses and recover a tag byte by byte. This walks the full length
    every time and accumulates differences in a single value.
    """
    if len(a) != len(b):
        return False
    difference = 0
    for x, y in zip(a, b):
        difference |= x ^ y
    return difference == 0


def verify_hmac_sha256(key: bytes, message: bytes, candidate_tag: bytes) -> bool:
    """Recompute the tag and compare it to the one supplied, in constant time."""
    return constant_time_equals(hmac_sha256(key, message), candidate_tag)


def generate_key(length: int = 32) -> bytes:
    """Produce a cryptographically random secret key."""
    return secrets.token_bytes(length)
