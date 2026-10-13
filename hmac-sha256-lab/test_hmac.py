"""
test_hmac.py
------------
Correctness checks for hmac_core.

The test vectors are the official HMAC-SHA256 cases published in RFC 4231.
Matching them is the accepted way to show an independent HMAC implementation
is correct. Each result is also cross-checked against Python's own hmac
module, which is a completely separate implementation.

Run with:  python test_hmac.py
"""

import hmac as reference_hmac
import hashlib

from hmac_core import (
    hmac_sha256,
    verify_hmac_sha256,
    constant_time_equals,
    normalise_key,
    BLOCK_SIZE,
)

# (description, key, message, expected tag) -- RFC 4231, section 4
RFC_4231_VECTORS = [
    (
        "Case 1: 20-byte key of 0x0b",
        bytes.fromhex("0b" * 20),
        b"Hi There",
        "b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7",
    ),
    (
        "Case 2: short ASCII key",
        b"Jefe",
        b"what do ya want for nothing?",
        "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843",
    ),
    (
        "Case 3: 20-byte key, 50 bytes of 0xdd",
        bytes.fromhex("aa" * 20),
        bytes.fromhex("dd" * 50),
        "773ea91e36800e46854db8ebd09181a72959098b3ef8c122d9635514ced565fe",
    ),
    (
        "Case 4: longer key and message",
        bytes.fromhex("0102030405060708090a0b0c0d0e0f10111213141516171819"),
        bytes.fromhex("cd" * 50),
        "82558a389a443c0ea4cc819899f2083a85f0faa3e578f8077a2e3ff46729665b",
    ),
    (
        "Case 6: 131-byte key, longer than one block",
        bytes.fromhex("aa" * 131),
        b"Test Using Larger Than Block-Size Key - Hash Key First",
        "60e431591ee0b67f0d8a26aacbf5b77f8e0bc6213728c5140546040f0ee37f54",
    ),
    (
        "Case 7: 131-byte key with a long message",
        bytes.fromhex("aa" * 131),
        b"This is a test using a larger than block-size key and a larger "
        b"than block-size data. The key needs to be hashed before being used"
        b" by the HMAC algorithm.",
        "9b09ffa71b942fcb27635fbcd5b0e944bfdc63644f0713938a7f51535c3a35e2",
    ),
]


def run_rfc_vectors() -> int:
    failures = 0
    print("RFC 4231 test vectors")
    for description, key, message, expected in RFC_4231_VECTORS:
        produced = hmac_sha256(key, message).hex()
        ok = produced == expected
        failures += 0 if ok else 1
        print(f"  [{'pass' if ok else 'FAIL'}] {description}")
        if not ok:
            print(f"         expected {expected}")
            print(f"         produced {produced}")
    return failures


def run_cross_check() -> int:
    failures = 0
    print("\nCross-check against Python's hmac module")
    samples = [
        (b"secret-key", b"Transfer 5000 to account 12345"),
        (b"", b""),
        (b"k" * 200, b"a longer key than one SHA-256 block"),
        ("पासवर्ड".encode(), "संदेश".encode()),
    ]
    for key, message in samples:
        mine = hmac_sha256(key, message).hex()
        theirs = reference_hmac.new(key, message, hashlib.sha256).hexdigest()
        ok = mine == theirs
        failures += 0 if ok else 1
        label = message[:34].decode(errors="replace") or "(empty message)"
        print(f"  [{'pass' if ok else 'FAIL'}] {label}")
    return failures


def run_behaviour_checks() -> int:
    failures = 0
    print("\nBehaviour checks")

    key, message = b"secret-key", b"Transfer 5000 to account 12345"
    tag = hmac_sha256(key, message)

    cases = [
        ("correct key and message verify", verify_hmac_sha256(key, message, tag) is True),
        ("a tampered message is rejected",
         verify_hmac_sha256(key, b"Transfer 9000 to account 12345", tag) is False),
        ("a wrong key is rejected", verify_hmac_sha256(b"wrong-key", message, tag) is False),
        ("a truncated tag is rejected", verify_hmac_sha256(key, message, tag[:-1]) is False),
        ("constant-time compare matches equal inputs", constant_time_equals(b"abc", b"abc") is True),
        ("constant-time compare separates unequal inputs", constant_time_equals(b"abc", b"abd") is False),
        ("a short key is padded to one block", len(normalise_key(b"k")[0]) == BLOCK_SIZE),
        ("an oversized key is padded to one block", len(normalise_key(b"k" * 300)[0]) == BLOCK_SIZE),
        ("one changed bit changes the tag",
         hmac_sha256(key, b"A") != hmac_sha256(key, b"B")),
    ]
    for description, ok in cases:
        failures += 0 if ok else 1
        print(f"  [{'pass' if ok else 'FAIL'}] {description}")
    return failures


if __name__ == "__main__":
    total = run_rfc_vectors() + run_cross_check() + run_behaviour_checks()
    print()
    if total == 0:
        print("All checks passed.")
    else:
        print(f"{total} check(s) failed.")
        raise SystemExit(1)
