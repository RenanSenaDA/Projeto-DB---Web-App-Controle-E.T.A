"""
Módulo de segurança e criptografia.

Fornece funções para hashing/verificação de senhas e para emissão/validação
de tokens de acesso JWT (HS256) usados na autenticação da API.
"""

import logging
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from passlib.hash import pbkdf2_sha256, bcrypt

from core.config import settings

logger = logging.getLogger(__name__)

# Resolve o segredo do JWT uma única vez, na importação do módulo.
# Em produção JWT_SECRET deve vir do .env. Se estiver vazio, geramos um
# segredo efêmero (vive só enquanto o processo viver) e avisamos — assim a
# API sobe normalmente, mas os tokens caem a cada restart e NÃO funcionam
# entre múltiplos workers/containers. Nunca rode em produção sem JWT_SECRET.
_JWT_SECRET = settings.JWT_SECRET.strip()
if not _JWT_SECRET:
    _JWT_SECRET = secrets.token_hex(32)
    logger.warning(
        "JWT_SECRET não configurado — usando segredo efêmero. Os tokens serão "
        "invalidados a cada restart e não funcionam com múltiplos workers. "
        "Defina JWT_SECRET no .env (ex.: `openssl rand -hex 32`) em produção."
    )


def create_access_token(user_id: int, role: str) -> str:
    """
    Cria um token de acesso JWT assinado (HS256) para o usuário.

    Args:
        user_id (int): ID do usuário (vai no claim `sub`, como string).
        role (str): Perfil do usuário (claim informativo `role`).

    Returns:
        str: JWT assinado com expiração definida por JWT_EXPIRE_MIN.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_EXPIRE_MIN),
    }
    return jwt.encode(payload, _JWT_SECRET, algorithm=settings.JWT_ALG)


def decode_access_token(token: str) -> dict:
    """
    Decodifica e valida (assinatura + expiração) um token de acesso JWT.

    Args:
        token (str): Token JWT a validar.

    Returns:
        dict: Payload decodificado (contém `sub`, `role`, `iat`, `exp`).

    Raises:
        jwt.ExpiredSignatureError: Token expirado.
        jwt.InvalidTokenError: Token inválido (assinatura/formato).
    """
    return jwt.decode(token, _JWT_SECRET, algorithms=[settings.JWT_ALG])

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