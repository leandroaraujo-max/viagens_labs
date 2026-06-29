from datetime import datetime

from app.infrastructure.orm.models import LGPDConsentimentoModel, LGPDSolicitacaoDelecaoModel, SolicitacaoModel


def test_consentimento_registra_no_banco(client, db_session):
    response = client.post(
        "/api/v1/lgpd/consentimento",
        json={"aceito": True, "versao_politica": "1.0"},
        headers={"user-agent": "pytest-suite"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "data_aceito" in body

    row = (
        db_session.query(LGPDConsentimentoModel)
        .filter(LGPDConsentimentoModel.usuario_id == "qa.user")
        .order_by(LGPDConsentimentoModel.id.desc())
        .first()
    )
    assert row is not None
    assert row.aceito is True
    assert row.user_agent == "pytest-suite"


def test_meus_dados_retorna_somente_solicitacoes_do_usuario(client, db_session, sample_solicitacao):
    db_session.add(SolicitacaoModel(**sample_solicitacao))
    db_session.add(
        SolicitacaoModel(
            protocolo="REQ-QA-002",
            solicitante_username="outro.usuario",
            destino_cidade="Rio de Janeiro",
            destino_estado="RJ",
            data_ida=datetime(2026, 6, 24, 9, 0, 0),
            motivo_viagem="Treinamento",
            tipo_servico="Aereo",
        )
    )
    db_session.commit()

    response = client.get("/api/v1/lgpd/meus-dados")

    assert response.status_code == 200
    body = response.json()
    assert body["usuario"]["id"] == "qa.user"
    assert body["total_viagens"] == 1
    assert body["viagens"][0]["protocolo"] == "REQ-QA-001"


def test_revogar_consentimento_marca_data_revogacao(client, db_session):
    db_session.add(
        LGPDConsentimentoModel(
            usuario_id="qa.user",
            aceito=True,
            data_aceito=datetime(2026, 6, 23, 10, 0, 0),
            versao_politica="1.0",
            ip_origem="127.0.0.1",
            user_agent="pytest-suite",
        )
    )
    db_session.commit()

    response = client.post("/api/v1/lgpd/revogar-consentimento")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"

    row = (
        db_session.query(LGPDConsentimentoModel)
        .filter(LGPDConsentimentoModel.usuario_id == "qa.user")
        .order_by(LGPDConsentimentoModel.id.desc())
        .first()
    )
    assert row is not None
    assert row.data_revogacao is not None


def test_revogar_sem_consentimento_retorna_info(client):
    response = client.post("/api/v1/lgpd/revogar-consentimento")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "info"


def test_solicitar_delecao_registra_pendente(client, db_session):
    response = client.post("/api/v1/lgpd/solicitar-delecao")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "protocolo" in body
    assert "data_execucao" in body

    row = (
        db_session.query(LGPDSolicitacaoDelecaoModel)
        .filter(LGPDSolicitacaoDelecaoModel.usuario_id == "qa.user")
        .order_by(LGPDSolicitacaoDelecaoModel.id.desc())
        .first()
    )
    assert row is not None
    assert row.status == "PENDENTE"


def test_solicitar_delecao_retorna_info_se_ja_existir_pendente(client, db_session):
    db_session.add(
        LGPDSolicitacaoDelecaoModel(
            usuario_id="qa.user",
            status="PENDENTE",
            data_solicitacao=datetime(2026, 6, 23, 10, 0, 0),
            data_execucao=datetime(2026, 7, 23, 10, 0, 0),
            observacao="solicitacao anterior",
        )
    )
    db_session.commit()

    response = client.post("/api/v1/lgpd/solicitar-delecao")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "info"
    assert "data_execucao" in body


def test_endpoints_lgpd_exigem_token_valido(client_no_auth):
    r1 = client_no_auth.post("/api/v1/lgpd/consentimento", json={"aceito": True})
    r2 = client_no_auth.get("/api/v1/lgpd/meus-dados")
    r3 = client_no_auth.post("/api/v1/lgpd/revogar-consentimento")
    r4 = client_no_auth.post("/api/v1/lgpd/solicitar-delecao")

    assert r1.status_code == 401
    assert r2.status_code == 401
    assert r3.status_code == 401
    assert r4.status_code == 401
