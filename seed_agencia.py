"""
Seed para criar usuários de agência no banco PostgreSQL.
Executar uma vez:
    cd C:\Projetos\viagens_labs
    .\venv\Scripts\python seed_agencia.py

Usuários criados:
  - tastur_usuario / Tastur@2026  (agência Tastur)
  - kontrip_usuario / Kontrip@2026 (agência Kontrip)
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("PYTHONPATH", ".")

from app.infrastructure.database import SessionLocal, engine
from app.infrastructure.orm.models import Base, UsuarioAgenciaModel
from app.core.security import get_password_hash

# Garante que todas as tabelas existem (não-destrutivo)
Base.metadata.create_all(bind=engine)

USUARIOS = [
    {"username": "tastur_usuario",  "nome": "Usuário Tastur",  "agencia_nome": "Tastur",  "senha": "Tastur@2026"},
    {"username": "kontrip_usuario", "nome": "Usuário Kontrip", "agencia_nome": "Kontrip", "senha": "Kontrip@2026"},
]

with SessionLocal() as db:
    for u in USUARIOS:
        existente = db.query(UsuarioAgenciaModel).filter_by(username=u["username"]).first()
        if existente:
            print(f"[SKIP] {u['username']} já existe.")
            continue
        novo = UsuarioAgenciaModel(
            username=u["username"],
            nome=u["nome"],
            agencia_nome=u["agencia_nome"],
            senha_hash=get_password_hash(u["senha"]),
        )
        db.add(novo)
        print(f"[OK]   {u['username']} ({u['agencia_nome']}) criado.")
    db.commit()

print("\nSeed concluído.")
