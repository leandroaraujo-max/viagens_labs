from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.dependencies import get_db_session, require_auth, require_dev
from app.api.v1.routers import api_router
from app.infrastructure.orm.models import (
    LGPDConsentimentoModel,
    LGPDSolicitacaoDelecaoModel,
    SolicitacaoModel,
    AuditoriaLGPDModel,
    TokenAprovacaoModel,
)


@pytest.fixture()
def db_session(tmp_path):
    db_path = tmp_path / "qa_suite.sqlite3"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    LGPDConsentimentoModel.__table__.create(bind=engine, checkfirst=True)
    LGPDSolicitacaoDelecaoModel.__table__.create(bind=engine, checkfirst=True)
    AuditoriaLGPDModel.__table__.create(bind=engine, checkfirst=True)
    SolicitacaoModel.__table__.create(bind=engine, checkfirst=True)
    TokenAprovacaoModel.__table__.create(bind=engine, checkfirst=True)

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _build_app(db_session, override_auth=True):
    app = FastAPI(title="QA Test App")
    app.include_router(api_router, prefix="/api/v1")

    def _override_db():
        yield db_session

    app.dependency_overrides[get_db_session] = _override_db
    if override_auth:
        app.dependency_overrides[require_auth] = lambda: ("qa.user", "viajante")
    return app


@pytest.fixture()
def client(db_session):
    app = _build_app(db_session, override_auth=True)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def client_no_auth(db_session):
    app = _build_app(db_session, override_auth=False)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def client_dev(db_session):
    app = _build_app(db_session, override_auth=False)
    app.dependency_overrides[require_dev] = lambda: "qa.dev"
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def sample_solicitacao():
    return {
        "protocolo": "REQ-QA-001",
        "solicitante_username": "qa.user",
        "destino_cidade": "Sao Paulo",
        "destino_estado": "SP",
        "data_ida": datetime(2026, 6, 23, 8, 0, 0),
        "motivo_viagem": "Reuniao corporativa",
        "tipo_servico": "Aereo",
    }
