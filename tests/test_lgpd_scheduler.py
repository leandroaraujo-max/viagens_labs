"""Testes do scheduler LGPD que processa solicitações de deleção expiradas."""

from datetime import datetime, timedelta

import pytest

from app.infrastructure.lgpd_scheduler import _processar_delecoes_expiradas
from app.infrastructure.orm.models import (
    LGPDSolicitacaoDelecaoModel,
    SolicitacaoModel,
    AuditoriaLGPDModel,
)


def test_processar_delecoes_expiradas_deleta_viagens_e_anonimiza(db_session):
    """Scheduler deve deletar viagens e anonimizar quando solicitação expira."""
    # Criar solicitação de viagem
    db_session.add(
        SolicitacaoModel(
            protocolo="REQ-DEL-001",
            solicitante_username="usuario.teste",
            destino_cidade="São Paulo",
            destino_estado="SP",
            data_ida=datetime(2026, 7, 1, 9, 0, 0),
            motivo_viagem="Teste de deleção",
            tipo_servico="Aereo",
        )
    )
    
    # Criar solicitação de deleção expirada
    db_session.add(
        LGPDSolicitacaoDelecaoModel(
            usuario_id="usuario.teste",
            status="PENDENTE",
            data_solicitacao=datetime.utcnow() - timedelta(days=35),
            data_execucao=datetime.utcnow() - timedelta(days=5),  # Expirado há 5 dias
            observacao="Teste de scheduler",
        )
    )
    db_session.commit()
    
    # Executar scheduler
    _processar_delecoes_expiradas(db_session)
    db_session.commit()
    
    # Verificar que viagem foi deletada
    viagem = (
        db_session.query(SolicitacaoModel)
        .filter_by(protocolo="REQ-DEL-001")
        .first()
    )
    assert viagem is None
    
    # Verificar que solicitação foi marcada como PROCESSADA
    solicitacao = (
        db_session.query(LGPDSolicitacaoDelecaoModel)
        .filter_by(usuario_id="usuario.teste")
        .first()
    )
    assert solicitacao.status == "PROCESSADA"
    assert solicitacao.data_processamento is not None
    assert "1 viagens deletadas" in solicitacao.observacao
    
    # Verificar que auditoria foi registrada
    auditoria = (
        db_session.query(AuditoriaLGPDModel)
        .filter_by(acao="DELECAO_AUTOMATICA")
        .first()
    )
    assert auditoria is not None
    assert auditoria.usuario_id == "SISTEMA_LGPD"
    assert "usuario:usuario.teste" in auditoria.recurso


def test_processar_delecoes_nao_processa_pendentes_nao_expiradas(db_session):
    """Scheduler não deve processar solicitações que ainda não expiraram."""
    # Criar solicitação de deleção NÃO expirada (futuro)
    db_session.add(
        LGPDSolicitacaoDelecaoModel(
            usuario_id="usuario.futuro",
            status="PENDENTE",
            data_solicitacao=datetime.utcnow(),
            data_execucao=datetime.utcnow() + timedelta(days=25),  # Ainda faltam 25 dias
            observacao="Não deve processar ainda",
        )
    )
    db_session.commit()
    
    # Executar scheduler
    _processar_delecoes_expiradas(db_session)
    db_session.commit()
    
    # Verificar que não foi processada
    solicitacao = (
        db_session.query(LGPDSolicitacaoDelecaoModel)
        .filter_by(usuario_id="usuario.futuro")
        .first()
    )
    assert solicitacao.status == "PENDENTE"
    assert solicitacao.data_processamento is None


def test_processar_delecoes_nao_reprocessa_ja_processadas(db_session):
    """Scheduler não deve reprocessar solicitações já marcadas como PROCESSADA."""
    # Criar solicitação já processada
    db_session.add(
        LGPDSolicitacaoDelecaoModel(
            usuario_id="usuario.processado",
            status="PROCESSADA",
            data_solicitacao=datetime.utcnow() - timedelta(days=35),
            data_execucao=datetime.utcnow() - timedelta(days=5),
            data_processamento=datetime.utcnow() - timedelta(days=4),
            observacao="Já foi processado anteriormente",
        )
    )
    db_session.commit()
    
    observacao_original = "Já foi processado anteriormente"
    
    # Executar scheduler
    _processar_delecoes_expiradas(db_session)
    db_session.commit()
    
    # Verificar que não foi reprocessada
    solicitacao = (
        db_session.query(LGPDSolicitacaoDelecaoModel)
        .filter_by(usuario_id="usuario.processado")
        .first()
    )
    assert solicitacao.observacao == observacao_original  # Não mudou
