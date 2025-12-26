"""
Módulo de segurança e criptografia.

Fornece funções para hashing e verificação de senhas.
"""

from passlib.hash import pbkdf2_sha256, bcrypt

def hash_password(plain: str) -> str:
    """
    Gera o hash de uma senha em texto plano.

    Args:
        plain (str): Senha em texto plano.

    Returns:
        str: Hash da senha usando PBKDF2-SHA256.
    """
    return pbkdf2_sha256.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    """
    Verifica se uma senha corresponde ao hash fornecido.
    Suporta hashes PBKDF2-SHA256 e Bcrypt.

    Args:
        plain (str): Senha em texto plano.
        hashed (str): Hash armazenado.

    Returns:
        bool: True se a senha for válida, False caso contrário.
    """
    try:
        if hashed.startswith("$pbkdf2-sha256$"):
            return pbkdf2_sha256.verify(plain, hashed)
        return bcrypt.verify(plain, hashed)
    except Exception:
        return False