"""
Seed para criar agências no banco PostgreSQL.
Executar da raiz do projeto:
    python scripts/seed_agencia.py
"""
import sys
import os

# Adiciona o diretório pai (raiz do projeto) ao sys.path para importar app corretamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.infrastructure.database import SessionLocal, engine
from app.infrastructure.orm.models import Base, AgenciaModel

# Garante que todas as tabelas existem (não-destrutivo)
Base.metadata.create_all(bind=engine)

AGENCIAS = [
    {
        "agencia_nome": "Tastur",
        "razao_social": "Tastur Viagens e Turismo Ltda",
        "cnpj": "12.345.678/0001-90",
        "email": "contato@tastur.com.br",
        "ativo": True
    },
    {
        "agencia_nome": "Kontrip",
        "razao_social": "Kontrip Corporate Travel",
        "cnpj": "98.765.432/0001-10",
        "email": "atendimento@kontrip.com.br",
        "ativo": True
    },
]

with SessionLocal() as db:
    for a in AGENCIAS:
        existente = db.query(AgenciaModel).filter_by(agencia_nome=a["agencia_nome"]).first()
        if existente:
            print(f"[SKIP] Agência {a['agencia_nome']} já existe.")
            continue
        nova = AgenciaModel(
            agencia_nome=a["agencia_nome"],
            razao_social=a["razao_social"],
            cnpj=a["cnpj"],
            email=a["email"],
            ativo=a["ativo"]
        )
        db.add(nova)
        print(f"[OK]   Agência {a['agencia_nome']} criada.")
    db.commit()

print("\nSeed concluído.")
