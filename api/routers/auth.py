"""
Rotas de autenticação e gestão de usuários.
"""

import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from database.connection import get_engine
from schemas.auth import LoginIn, InviteIn, RegisterInviteIn, UserOut
from core.security import hash_password, verify_password
from deps import get_current_admin
from services.email_service import send_brevo_invite
from core.config import settings

router = APIRouter()

@router.post("/login")
def auth_login(payload: LoginIn):
    """
    Realiza o login de um usuário.

    Verifica email e senha, e retorna um token de acesso "dummy".
    """
    eng = get_engine()
    with eng.connect() as conn:
        row = conn.execute(text("SELECT id, email, name, password_hash, role FROM eta.app_user WHERE lower(email)=:e;"), 
                        {"e": payload.email.lower().strip()}).fetchone()
        if not row: raise HTTPException(401, "Usuário não encontrado")
        if not verify_password(payload.password, row._mapping["password_hash"]): raise HTTPException(401, "Senha inválida")
        
        token = f"dummy-{row._mapping['id']}-{int(datetime.utcnow().timestamp())}"
        return {"token": token, "user": {"id": row._mapping["id"], "email": row._mapping["email"], "name": row._mapping["name"], "role": row._mapping["role"]}}

@router.post("/invite")
def create_invite(payload: InviteIn, user_id: int = Depends(get_current_admin)):
    """
    Cria e envia um convite para um novo usuário.
    
    Apenas administradores podem convidar.
    """
    eng = get_engine()
    with eng.connect() as conn:
        if conn.execute(text("SELECT 1 FROM eta.app_user WHERE lower(email)=:e"), {"e": payload.email.lower()}).fetchone():
            raise HTTPException(409, "Email já cadastrado.")
    
    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(hours=24)
    
    with eng.begin() as conn:
        conn.execute(text("INSERT INTO eta.user_invites (token, email, created_by, expires_at) VALUES (:t, :e, :u, :x)"),
                    {"t": token, "e": payload.email.lower(), "u": user_id, "x": expires})
    
    send_brevo_invite(payload.email, f"{settings.FRONTEND_URL}/register?token={token}")
    return {"ok": True, "message": f"Convite enviado para {payload.email}"}

@router.get("/validate-invite/{token}")
def validate_invite(token: str):
    """
    Valida se um token de convite é válido e não expirou.
    """
    eng = get_engine()
    with eng.connect() as conn:
        row = conn.execute(text("SELECT email, expires_at, used FROM eta.user_invites WHERE token = :t"), {"t": token}).fetchone()
    if not row: raise HTTPException(404, "Convite inválido.")
    if row._mapping["used"] or datetime.utcnow() > row._mapping["expires_at"]: raise HTTPException(400, "Convite inválido ou expirado.")
    return {"valid": True, "email": row._mapping["email"]}

@router.post("/register-invite")
def register_with_invite(payload: RegisterInviteIn):
    """
    Registra um novo usuário utilizando um convite válido.
    """
    eng = get_engine()
    with eng.connect() as conn:
        inv = conn.execute(text("SELECT email, used, expires_at FROM eta.user_invites WHERE token=:t"), {"t": payload.token}).fetchone()
    
    if not inv or inv._mapping["used"] or datetime.utcnow() > inv._mapping["expires_at"]:
        raise HTTPException(400, "Convite inválido.")
    
    email = inv._mapping["email"]
    with eng.begin() as conn:
        if conn.execute(text("SELECT 1 FROM eta.app_user WHERE lower(email)=:e"), {"e": email}).fetchone():
            raise HTTPException(409, "Usuário já existe.")
        conn.execute(text("INSERT INTO eta.app_user(email, name, password_hash, role, is_active) VALUES (:e, :n, :p, 'user', TRUE)"),
                    {"e": email, "n": payload.name.strip(), "p": hash_password(payload.password)})
        conn.execute(text("UPDATE eta.user_invites SET used=TRUE WHERE token=:t"), {"t": payload.token})
    return {"ok": True, "message": "Conta criada."}

@router.get("/users", response_model=list[UserOut])
def list_users(uid: int = Depends(get_current_admin)):
    """
    Lista todos os usuários cadastrados.
    
    Apenas administradores podem listar.
    """
    eng = get_engine()
    with eng.connect() as conn:
        rows = conn.execute(text("SELECT id, name, email, role, is_active FROM eta.app_user ORDER BY id")).fetchall()
        return [{"id": r._mapping["id"], "name": r._mapping["name"], "email": r._mapping["email"], "role": r._mapping["role"], "is_active": r._mapping["is_active"]} for r in rows]

@router.delete("/users/{user_id}")
def delete_user(user_id: int, uid: int = Depends(get_current_admin)):
    """
    Exclui um usuário pelo ID.
    
    Apenas administradores podem excluir. Um admin não pode excluir a si mesmo.
    """
    if user_id == uid: raise HTTPException(400, "Não pode excluir a si mesmo.")
    eng = get_engine()
    with eng.begin() as conn:
        res = conn.execute(text("DELETE FROM eta.app_user WHERE id=:id"), {"id": user_id})
        if res.rowcount == 0: raise HTTPException(404, "Usuário não encontrado.")
    return {"ok": True}