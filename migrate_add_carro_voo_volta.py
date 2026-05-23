"""Migration: adiciona carro_data_retirada, carro_data_devolucao, preferencia_voo_volta"""
from app.infrastructure.database import engine
from sqlalchemy import text

sqls = [
    "ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS carro_data_retirada VARCHAR(20) DEFAULT ''",
    "ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS carro_data_devolucao VARCHAR(20) DEFAULT ''",
    "ALTER TABLE solicitacoes ADD COLUMN IF NOT EXISTS preferencia_voo_volta TEXT",
]

with engine.connect() as conn:
    for sql in sqls:
        conn.execute(text(sql))
    conn.commit()

print("Migration OK — 3 colunas adicionadas.")
