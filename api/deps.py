"""
Módulo de dependências da API.

Contém funções para injeção de dependência, como obtenção do usuário atual e verificação de administrador.
"""

from fastapi import Header, HTTPException, Depends
from sqlalchemy import text
from database.connection import get_engine    

def get_current_user(authorization: str = Header(None)):
    """
    Dependência para validar o token de autenticação e obter o ID do usuário.
    
    Espera um cabeçalho Authorization no formato "Bearer dummy-{user_id}-timestamp".
    
    Args:
        authorization (str, optional): Cabeçalho Authorization.
        
    Returns:
        int: ID do usuário autenticado.
        
    Raises:
        HTTPException: Se o token for ausente, inválido ou malformado.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Token ausente")
    token = authorization.replace("Bearer ", "").strip()
    try:
        parts = token.split("-")
        if len(parts) < 3 or parts[0] != "dummy":
            raise HTTPException(status_code=401, detail="Token inválido")
        return int(parts[1])
    except:
        raise HTTPException(status_code=401, detail="Token malformado")

def get_current_admin(user_id: int = Depends(get_current_user)):
    """
    Dependência para garantir que o usuário atual tenha privilégios de administrador.
    
    Args:
        user_id (int): ID do usuário obtido via get_current_user.
        
    Returns:
        int: ID do administrador confirmado.
        
    Raises:
        HTTPException: Se o usuário não tiver permissão de administrador.
    """
    eng = get_engine()
    with eng.connect() as conn:
        row = conn.execute(text("SELECT role FROM eta.app_user WHERE id=:id"), {"id": user_id}).fetchone()
        if not row or row._mapping["role"] != 'admin':
             raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    return user_id
