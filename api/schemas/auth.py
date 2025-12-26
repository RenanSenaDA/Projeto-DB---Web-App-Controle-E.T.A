"""
Esquemas Pydantic para autenticação e usuários.
"""

from pydantic import BaseModel, EmailStr, field_validator
import re

class LoginIn(BaseModel):
    """
    Esquema de entrada para login.
    """
    email: EmailStr
    password: str

class InviteIn(BaseModel):
    """
    Esquema de entrada para criação de convites.
    """
    email: EmailStr

class RegisterInviteIn(BaseModel):
    """
    Esquema de entrada para registro via convite.
    """
    token: str
    name: str
    password: str

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v: str) -> str:
        """Valida o comprimento do nome."""
        v = (v or "").strip()
        if len(v) < 2: raise ValueError("Nome muito curto")
        return v

    @field_validator("password")
    @classmethod
    def _validate_password(cls, v: str) -> str:
        """
        Valida a complexidade da senha.
        Requer: min 8 chars, 1 maiúscula, 1 minúscula, 1 número, 1 símbolo.
        """
        if not v or len(v) < 8: raise ValueError("Senha fraca: mínimo 8 caracteres")
        if not re.search(r"[A-Z]", v): raise ValueError("Senha fraca: incluir letra maiúscula")
        if not re.search(r"[a-z]", v): raise ValueError("Senha fraca: incluir letra minúscula")
        if not re.search(r"\d", v): raise ValueError("Senha fraca: incluir número")
        if not re.search(r"[^A-Za-z0-9]", v): raise ValueError("Senha fraca: incluir símbolo")
        return v

class UserOut(BaseModel):
    """
    Esquema de saída para dados de usuário.
    """
    id: int
    name: str
    email: EmailStr
    role: str
    is_active: bool