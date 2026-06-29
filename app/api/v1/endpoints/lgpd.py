from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.api.dependencies import get_db_session, require_auth
from app.infrastructure.orm.models import LGPDConsentimentoModel, SolicitacaoModel, LGPDSolicitacaoDelecaoModel
from app.domain.models import schemas

router = APIRouter(prefix="/lgpd", tags=["LGPD"])


@router.post("/consentimento")
def registrar_consentimento(
    request: Request,
    auth_info: tuple = Depends(require_auth),
    db: Session = Depends(get_db_session)
):
    """
    Registra a aceitação do consentimento LGPD pelo usuário.
    
    Body:
    {
        "aceito": true,
        "versao_politica": "1.0"
    }
    """
    usuario_id, perfil = auth_info
    
    try:
        # Capturar IP e User-Agent
        ip_origem = request.client.host if request.client else "0.0.0.0"
        user_agent = request.headers.get("user-agent", "")[:500]
        
        # Criar registro de consentimento
        consent = LGPDConsentimentoModel(
            usuario_id=usuario_id,
            aceito=True,
            data_aceito=datetime.utcnow(),
            versao_politica="1.0",
            ip_origem=ip_origem,
            user_agent=user_agent
        )
        
        db.add(consent)
        db.commit()
        db.refresh(consent)
        
        return {
            "status": "ok",
            "msg": "Consentimento registrado com sucesso",
            "data_aceito": consent.data_aceito.isoformat()
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao registrar consentimento: {str(e)}"
        )


@router.get("/meus-dados")
def meus_dados(
    auth_info: tuple = Depends(require_auth),
    db: Session = Depends(get_db_session)
):
    """
    Retorna todos os dados pessoais do usuário em JSON.
    Base Legal: Art. 18, LGPD (Direito de Acesso)
    
    Inclui: dados do usuário + todas as suas solicitações de viagem
    """
    usuario_id, perfil = auth_info
    
    try:
        # Buscar todas as solicitações do usuário
        viagens = db.query(SolicitacaoModel).filter(
            SolicitacaoModel.solicitante_username == usuario_id
        ).all()
        
        # Formatar resposta
        return {
            "usuario": {
                "id": usuario_id,
                "perfil": perfil,
                "data_acesso": datetime.utcnow().isoformat()
            },
            "viagens": [
                {
                    "protocolo": v.protocolo,
                    "data_ida": v.data_ida.isoformat() if v.data_ida else None,
                    "data_volta": v.data_volta.isoformat() if v.data_volta else None,
                    "destino": f"{v.destino_cidade}/{v.destino_estado}",
                    "status": v.status,
                    "classificacao": v.classificacao,
                    "tipo_servico": v.tipo_servico,
                    "motivo_viagem": v.motivo_viagem,
                    "data_criacao": v.data_criacao.isoformat() if v.data_criacao else None
                }
                for v in viagens
            ],
            "total_viagens": len(viagens),
            "msg": "Dados exportados conforme direito de portabilidade LGPD."
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao recuperar dados: {str(e)}"
        )


@router.post("/revogar-consentimento")
def revogar_consentimento(
    request: Request,
    auth_info: tuple = Depends(require_auth),
    db: Session = Depends(get_db_session)
):
    """
    Usuário revoga seu consentimento LGPD.
    Isso impactará o acesso ao sistema (banner de aviso será exibido).
    
    Base Legal: Art. 8, parágrafo 5º, LGPD
    """
    usuario_id, perfil = auth_info
    
    try:
        # Buscar consentimento mais recente do usuário
        consent = db.query(LGPDConsentimentoModel).filter(
            LGPDConsentimentoModel.usuario_id == usuario_id,
            LGPDConsentimentoModel.aceito == True,
            LGPDConsentimentoModel.data_revogacao == None
        ).order_by(LGPDConsentimentoModel.data_aceito.desc()).first()
        
        if not consent:
            return {
                "status": "info",
                "msg": "Nenhum consentimento ativo encontrado para revogar."
            }
        
        # Marcar como revogado
        consent.data_revogacao = datetime.utcnow()
        db.commit()
        
        return {
            "status": "ok",
            "msg": "Consentimento revogado. Você deixará de ter acesso ao sistema.",
            "data_revogacao": consent.data_revogacao.isoformat()
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao revogar consentimento: {str(e)}"
        )


@router.post("/solicitar-delecao")
def solicitar_delecao(
    auth_info: tuple = Depends(require_auth),
    db: Session = Depends(get_db_session)
):
    """
    Registra solicitação de deleção/anonimização de dados do titular.
    A execução fica agendada para 30 dias após a solicitação.
    """
    usuario_id, _perfil = auth_info

    try:
        pendente = (
            db.query(LGPDSolicitacaoDelecaoModel)
            .filter(
                LGPDSolicitacaoDelecaoModel.usuario_id == usuario_id,
                LGPDSolicitacaoDelecaoModel.status == "PENDENTE",
            )
            .order_by(LGPDSolicitacaoDelecaoModel.data_solicitacao.desc())
            .first()
        )
        if pendente:
            return {
                "status": "info",
                "msg": "Ja existe solicitacao de delecao pendente para este usuario.",
                "data_execucao": pendente.data_execucao.isoformat() if pendente.data_execucao else None,
            }

        agora = datetime.utcnow()
        solicitacao = LGPDSolicitacaoDelecaoModel(
            usuario_id=usuario_id,
            status="PENDENTE",
            data_solicitacao=agora,
            data_execucao=agora + timedelta(days=30),
            observacao="Solicitacao criada pelo proprio titular via portal LGPD.",
        )
        db.add(solicitacao)
        db.commit()
        db.refresh(solicitacao)

        return {
            "status": "ok",
            "msg": "Solicitacao de delecao registrada. O processamento ocorrera em ate 30 dias.",
            "protocolo": solicitacao.id,
            "data_execucao": solicitacao.data_execucao.isoformat(),
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao solicitar delecao: {str(e)}",
        )
