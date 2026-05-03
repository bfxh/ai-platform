#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.secure_utils import SecureKeyManager


def main():
    print("=== /python Secure Key Initialization ===\n")

    keys = [
        ("remote-control", "remote-control/secret", "Remote Control WebSocket Secret"),
        ("hybrid-cache", "hmac_key", "Hybrid Cache HMAC Key"),
    ]

    km_instances = {}
    for service, key, description in keys:
        km = SecureKeyManager(service)
        km_instances[service] = km
        existing = km.get(key)
        if existing:
            print(f"[OK] {description}: already exists (length={len(existing)})")
        else:
            value = km.generate_and_store(key)
            print(f"[NEW] {description}: generated (length={len(value)})")

    print("\n=== Key Initialization Complete ===")
    print("Keys are stored in system keyring (or .env file as fallback).")
    print("Run this script again to verify key status.")


if __name__ == "__main__":
    main()
