"""
Portal do Desenvolvedor — endpoints exclusivos para G_ACCESS_VIAGENSLABS_DEV.
Acesso irrestrito a toda a plataforma: métricas, solicitações, agências, configuração.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional
import logging

from app.api.dependencies import get_db_session, require_dev
from app.infrastructure.orm.models import (
    SolicitacaoModel, AgenciaModel, CotacaoModel, VoucherModel, TokenAprovacaoModel
)
from app.core.config import settings
from app.core.security import get_password_hash

router = APIRouter()

# ── Stats gerais ──────────────────────────────────────────────────────────────

@router.get("/stats")
def stats_gerais(
    db: Session = Depends(get_db_session),
    _: str = Depends(require_dev),
):
    """Métricas globais da plataforma para o dashboard do dev."""
    total = db.query(func.count(SolicitacaoModel.id)).scalar() or 0

    por_status = (
        db.query(SolicitacaoModel.status, func.count(SolicitacaoModel.id))
        .group_by(SolicitacaoModel.status)
        .all()
    )

    agencias = db.query(func.count(AgenciaModel.id)).scalar() or 0
    cotacoes = db.query(func.count(CotacaoModel.id)).scalar() or 0
    vouchers = db.query(func.count(VoucherModel.id)).scalar() or 0

    return {
        "total_solicitacoes": total,
        "por_status": {s: c for s, c in por_status},
        "total_agencias": agencias,
        "total_cotacoes": cotacoes,
        "total_vouchers": vouchers,
    }


# ── Solicitações (irrestrito) ─────────────────────────────────────────────────

@router.get("/solicitacoes")
def listar_solicitacoes(
    status: Optional[str] = Query(None),
    busca: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: Session = Depends(get_db_session),
    _: str = Depends(require_dev),
):
    q = db.query(SolicitacaoModel)
    if status:
        q = q.filter(SolicitacaoModel.status == status)
    if busca:
        like = f"%{busca}%"
        q = q.filter(
            SolicitacaoModel.protocolo.ilike(like)
            | SolicitacaoModel.solicitante_username.ilike(like)
            | SolicitacaoModel.destino_cidade.ilike(like)
            | SolicitacaoModel.viajante_nome.ilike(like)
        )
    total = q.count()
    itens = q.order_by(desc(SolicitacaoModel.data_criacao)).offset(offset).limit(limit).all()

    return {
        "total": total,
        "itens": [
            {
                "id": s.id,
                "protocolo": s.protocolo,
                "solicitante": s.solicitante_username,
                "viajante_nome": s.viajante_nome,
                "destino": f"{s.destino_cidade}/{s.destino_estado}",
                "data_ida": s.data_ida.isoformat() if s.data_ida else None,
                "tipo_servico": s.tipo_servico,
                "status": s.status,
                "classificacao": s.classificacao,
                "data_criacao": s.data_criacao.isoformat() if s.data_criacao else None,
            }
            for s in itens
        ],
    }


# ── Agências ──────────────────────────────────────────────────────────────────

@router.get("/agencias")
def listar_agencias(
    db: Session = Depends(get_db_session),
    _: str = Depends(require_dev),
):
    agencias = db.query(AgenciaModel).order_by(AgenciaModel.nome_fantasia).all()
    return [
        {
            "id": a.id,
            "nome_fantasia": a.nome_fantasia,
            "razao_social": a.razao_social,
            "cnpj": a.cnpj,
            "email_contato": a.email_contato,
            "ativa": a.ativa,
            "data_criacao": a.data_criacao.isoformat() if a.data_criacao else None,
        }
        for a in agencias
    ]


@router.patch("/agencias/{agencia_id}/toggle-ativa")
def toggle_agencia_ativa(
    agencia_id: int,
    db: Session = Depends(get_db_session),
    _: str = Depends(require_dev),
):
    ag = db.query(AgenciaModel).filter(AgenciaModel.id == agencia_id).first()
    if not ag:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Agência não encontrada.")
    ag.ativa = not ag.ativa
    db.commit()
    return {"id": ag.id, "ativa": ag.ativa}


@router.post("/agencias/{agencia_id}/reset-senha")
def reset_senha_agencia(
    agencia_id: int,
    payload: dict,
    db: Session = Depends(get_db_session),
    dev_user: str = Depends(require_dev),
):
    ag = db.query(AgenciaModel).filter(AgenciaModel.id == agencia_id).first()
    if not ag:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Agência não encontrada.")
    nova_senha = payload.get("nova_senha", "")
    if len(nova_senha) < 8:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Senha deve ter pelo menos 8 caracteres.")
    ag.senha_hash = get_password_hash(nova_senha)
    db.commit()
    logging.info(f"[DEV] {dev_user} resetou senha da agência {ag.nome_fantasia} (id={agencia_id})")
    return {"ok": True, "agencia": ag.nome_fantasia}


# ── Configuração (sanitizada, sem secrets completos) ──────────────────────────

@router.get("/config")
def obter_config(
    _: str = Depends(require_dev),
):
    """Exibe a configuração ativa da plataforma (secrets truncados para segurança)."""

    def _mask(val: str, show: int = 4) -> str:
        if not val:
            return "(não configurado)"
        return val[:show] + "…" if len(val) > show else val

    return {
        "database_url":       _mask(settings.DATABASE_URL, 30),
        "base_url":           settings.BASE_URL,
        "base_url_agencia":   settings.BASE_URL_AGENCIA,
        "base_url_aprovacao": settings.BASE_URL_APROVACAO,
        "smtp_host":          settings.SMTP_HOST,
        "smtp_port":          settings.SMTP_PORT,
        "smtp_from":          settings.SMTP_FROM,
        "gas_relay_url":      settings.GAS_RELAY_URL or "(não configurado)",
        "gas_secret_ok":      bool(settings.GAS_SECRET),
        "duffel_token_ok":    bool(settings.DUFFEL_TOKEN),
        "google_places_key_ok": bool(settings.GOOGLE_PLACES_KEY),
        "ad_base_dn":         settings.AD_BASE_DN,
        "ad_group_admins":    settings.AD_GROUP_ADMINS,
        "ad_group_dev":       settings.AD_GROUP_DEV,
        "ad_group_agencias":  settings.AD_GROUP_AGENCIAS,
        "setor_email":        settings.SETOR_EMAIL,
        "agencia_tastur_email":  settings.AGENCIA_TASTUR_EMAIL or "(não configurado)",
        "agencia_kontrip_email": settings.AGENCIA_KONTRIP_EMAIL or "(não configurado)",
        "qa_aprovador_email": settings.QA_APROVADOR_EMAIL or "(desativado)",
    }


# ── Atividade recente ─────────────────────────────────────────────────────────

@router.get("/atividade")
def atividade_recente(
    limit: int = Query(30, le=100),
    db: Session = Depends(get_db_session),
    _: str = Depends(require_dev),
):
    """Últimas atualizações de solicitações para o feed de atividade."""
    itens = (
        db.query(SolicitacaoModel)
        .order_by(desc(SolicitacaoModel.data_atualizacao))
        .limit(limit)
        .all()
    )
    return [
        {
            "protocolo": s.protocolo,
            "status": s.status,
            "solicitante": s.solicitante_username,
            "viajante": s.viajante_nome or s.solicitante_username,
            "destino": f"{s.destino_cidade}/{s.destino_estado}",
            "atualizado_em": s.data_atualizacao.isoformat() if s.data_atualizacao else (
                s.data_criacao.isoformat() if s.data_criacao else None
            ),
        }
        for s in itens
    ]
