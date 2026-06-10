"""
Cryptography module for encrypting and decrypting data.
"""
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def encrypt(data: bytes, key: bytes) -> bytes:
    """
    Encrypts data using AES-256-GCM.
    """
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    return nonce + aesgcm.encrypt(nonce, data, None)

def decrypt(token: bytes, key: bytes) -> bytes:
    """
    Decrypts data using AES-256-GCM.
    """
    aesgcm = AESGCM(key)
    nonce = token[:12]
    ciphertext = token[12:]
    return aesgcm.decrypt(nonce, ciphertext, None)
