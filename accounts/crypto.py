import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from django.conf import settings


_INFO = b"classy-havens-staff-documents-v1"


def _master_key_bytes() -> bytes:
    raw = settings.ENCRYPTION_KEY
    try:
        decoded = base64.urlsafe_b64decode(raw)
    except Exception:
        raise ValueError(
            "ENCRYPTION_KEY is not valid base64. Regenerate it with: "
            "python -c \"from cryptography.fernet import Fernet; "
            "print(Fernet.generate_key().decode())\""
        )
    if len(decoded) != 32:
        raise ValueError(
            f"ENCRYPTION_KEY must decode to 32 bytes (got {len(decoded)})."
        )
    return decoded


def _derive_fernet_key(salt: bytes) -> bytes:
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        info=_INFO,
    )
    derived = hkdf.derive(_master_key_bytes())
    return base64.urlsafe_b64encode(derived)


def encrypt_document(plaintext: bytes) -> tuple[bytes, bytes]:
    """Return (ciphertext, salt). Store both with the row."""
    salt = os.urandom(16)
    f = Fernet(_derive_fernet_key(salt))
    return f.encrypt(plaintext), salt


def decrypt_document(ciphertext: bytes, salt: bytes) -> bytes:
    f = Fernet(_derive_fernet_key(salt))
    return f.decrypt(ciphertext)