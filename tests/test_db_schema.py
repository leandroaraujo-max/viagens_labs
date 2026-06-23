import pytest
from sqlalchemy import create_engine, inspect, text

from app.core.config import settings
from app.infrastructure.orm.models import LGPDConsentimentoModel


EXPECTED_COLUMNS = {
    "id",
    "usuario_id",
    "aceito",
    "data_aceito",
    "data_revogacao",
    "versao_politica",
    "ip_origem",
    "user_agent",
    "criado_em",
}


def test_lgpd_model_define_colunas_esperadas():
    defined_columns = {c.name for c in LGPDConsentimentoModel.__table__.columns}
    assert EXPECTED_COLUMNS.issubset(defined_columns)


@pytest.mark.integration
def test_postgres_lgpd_tabela_e_colunas():
    if not settings.DATABASE_URL.startswith("postgresql"):
        pytest.skip("DATABASE_URL nao aponta para PostgreSQL")

    engine = create_engine(settings.DATABASE_URL)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        inspector = inspect(engine)
        assert inspector.has_table("lgpd_consentimento") is True

        cols = {c["name"] for c in inspector.get_columns("lgpd_consentimento")}
        assert EXPECTED_COLUMNS.issubset(cols)
    finally:
        engine.dispose()
