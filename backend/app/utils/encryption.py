from cryptography.fernet import Fernet
import json
import base64
from ..config import get_settings

settings = get_settings()


def get_cipher():
    """Get Fernet cipher instance."""
    # In production, use a proper encryption key from settings
    key = settings.encryption_key.encode()
    # Ensure key is properly formatted (32 url-safe base64-encoded bytes)
    if len(key) < 32:
        key = base64.urlsafe_b64encode(key.ljust(32, b'0'))
    return Fernet(key)


def encrypt_credentials(credentials: dict) -> str:
    """Encrypt cloud provider credentials.

    Args:
        credentials: Dictionary of credentials

    Returns:
        Encrypted credentials as string
    """
    try:
        cipher = get_cipher()
        json_data = json.dumps(credentials)
        encrypted = cipher.encrypt(json_data.encode())
        return encrypted.decode()
    except Exception as e:
        print(f"Encryption failed: {e}")
        raise


def decrypt_credentials(encrypted_data: str) -> dict:
    """Decrypt cloud provider credentials.

    Args:
        encrypted_data: Encrypted credentials string

    Returns:
        Dictionary of credentials
    """
    try:
        cipher = get_cipher()
        decrypted = cipher.decrypt(encrypted_data.encode())
        return json.loads(decrypted.decode())
    except Exception as e:
        print(f"Decryption failed: {e}")
        raise
