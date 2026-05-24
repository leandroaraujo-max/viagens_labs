from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import String, Text, Boolean
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.dependencies import get_db_session, require_setor, require_setor_username
from app.domain.models.schemas import (
    SolicitacaoSetorResponse, SetorAcaoRequest, CotacaoResponse,
    AgenciaCreate, AgenciaUpdate, AgenciaResponse,
)
from app.services.setor_service import SetorService
from app.infrastructure.orm.models import AgenciaModel

router = APIRouter()
_setor_svc = SetorService()

# Campos Optional[str] que devem permanecer None quando o banco retorna NULL
_OPTIONAL_STR_COLS = {'agencia_vencedora'}


def _build_setor_response(sol, cot_tastur, cot_kontrip, casamentos, todas_cotacoes) -> SolicitacaoSetorResponse:
    """Constrói SolicitacaoSetorResponse a partir do ORM e dados relacionados.

    Normaliza None → '' para colunas String/Text e None → False para Boolean,
    exceto campos explicitamente Optional no schema (ex: agencia_vencedora).
    """
    data = {}
    for col in sol.__table__.columns:
        val = getattr(sol, col.name)
        if val is None and col.name not in _OPTIONAL_STR_COLS:
            if isinstance(col.type, (String, Text)):
                val = ''
            elif isinstance(col.type, Boolean):
                val = False
        data[col.name] = val
    data['cotacao_tastur']  = CotacaoResponse.model_validate(cot_tastur)  if cot_tastur  else None
    data['cotacao_kontrip'] = CotacaoResponse.model_validate(cot_kontrip) if cot_kontrip else None
    data['todas_cotacoes']  = [CotacaoResponse.model_validate(c) for c in todas_cotacoes] if todas_cotacoes else []
    data['casamentos'] = casamentos
    return SolicitacaoSetorResponse.model_validate(data)


@router.get("/solicitacoes", response_model=List[SolicitacaoSetorResponse])
def listar_solicitacoes(
    status_filtro: Optional[str] = Query(None, description="Filtrar por status"),
    periodo_dias:  Optional[int] = Query(None, description="Últimos N dias"),
    agencia:       Optional[str] = Query(None, description="Filtrar por agência vencedora"),
    busca:         Optional[str] = Query(None, description="Busca livre (protocolo/viajante/destino)"),
    db: Session = Depends(get_db_session),
    _: str = Depends(require_setor),
):
    """Lista todas as solicitações visíveis no painel do setor, com filtros opcionais."""
    solicitacoes = _setor_svc.listar_solicitacoes(
        db,
        status_filtro=status_filtro,
        periodo_dias=periodo_dias,
        agencia_filtro=agencia,
        busca=busca,
    )
    return [
        _build_setor_response(*_setor_svc.get_solicitacao(db, sol.id))
        for sol in solicitacoes
    ]


@router.get("/solicitacoes/{solicitacao_id}", response_model=SolicitacaoSetorResponse)
def detalhar_solicitacao(
    solicitacao_id: int,
    db: Session = Depends(get_db_session),
    _: str = Depends(require_setor),
):
    """Detalhes completos de uma solicitação para o portal do setor."""
    sol, cot_tastur, cot_kontrip, casamentos, todas_cotacoes = _setor_svc.get_solicitacao(db, solicitacao_id)
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada.")
    return _build_setor_response(sol, cot_tastur, cot_kontrip, casamentos, todas_cotacoes)


@router.post("/solicitacoes/{solicitacao_id}/acao", status_code=status.HTTP_200_OK)
def executar_acao(
    solicitacao_id: int,
    body: SetorAcaoRequest,
    db: Session = Depends(get_db_session),
    username: str = Depends(require_setor_username),
):
    """
    Executa uma ação do setor sobre a solicitação.

    Ações disponíveis por status:
    - PENDENTE_PRE_APROVACAO_SETOR  → PRE_APROVAR | PRE_REPROVAR
    - AGUARDANDO_COTACAO            → REENVIAR_AGENCIAS
    - COTACAO_ENVIADA               → REENVIAR_AGENCIAS
    - PENDENTE_APROVACAO_SETOR_COTACAO → APROVAR_TASTUR | APROVAR_KONTRIP | REPROVAR
    """
    try:
        resultado = _setor_svc.executar_acao(
            db,
            solicitacao_id,
            body.acao,
            body.observacao,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    return resultado


# ── Casamentos ────────────────────────────────────────────────────────────────

from app.services.casamento_service import CasamentoService

_casamento_svc = CasamentoService()


@router.get("/casamentos")
def listar_casamentos(
    db: Session = Depends(get_db_session),
    _: str = Depends(require_setor),
):
    """Lista todos os pares de casamento PENDENTES para o painel do setor."""
    return _casamento_svc.listar_casamentos_pendentes(db)


@router.post("/casamentos/{casamento_id}/vincular")
def vincular_casamento(
    casamento_id: int,
    db: Session = Depends(get_db_session),
    username: str = Depends(require_setor_username),
):
    """Confirma o match — gera código de grupo e marca como VINCULADO."""
    try:
        casamento = _casamento_svc.vincular(db, casamento_id, username)
        db.commit()
        return {"id": casamento.id, "status": casamento.status, "grupo_viagem": casamento.grupo_viagem}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/casamentos/{casamento_id}/ignorar")
def ignorar_casamento(
    casamento_id: int,
    db: Session = Depends(get_db_session),
    username: str = Depends(require_setor_username),
):
    """Descarta o match — marca como IGNORADO."""
    try:
        casamento = _casamento_svc.ignorar(db, casamento_id, username)
        db.commit()
        return {"id": casamento.id, "status": casamento.status}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Agências ──────────────────────────────────────────────────────────────────

_AGENCIA_STR_FIELDS = [
    'agencia_nome','razao_social','cnpj','inscricao_estadual','email',
    'cep','logradouro','numero','complemento','bairro','municipio','uf',
    'banco_nome','banco_codigo','agencia_bancaria','conta_bancaria',
    'tipo_conta','titularidade_cnpj','titularidade_razao_social',
]

def _agencia_to_response(ag: AgenciaModel) -> AgenciaResponse:
    return AgenciaResponse(
        id=ag.id,
        agencia_nome=ag.agencia_nome or '',
        razao_social=ag.razao_social or '',
        cnpj=ag.cnpj or '',
        inscricao_estadual=ag.inscricao_estadual or '',
        email=ag.email or '',
        cep=ag.cep or '',
        logradouro=ag.logradouro or '',
        numero=ag.numero or '',
        complemento=ag.complemento or '',
        bairro=ag.bairro or '',
        municipio=ag.municipio or '',
        uf=ag.uf or '',
        banco_nome=ag.banco_nome or '',
        banco_codigo=ag.banco_codigo or '',
        agencia_bancaria=ag.agencia_bancaria or '',
        conta_bancaria=ag.conta_bancaria or '',
        tipo_conta=ag.tipo_conta or 'CC',
        titularidade_cnpj=ag.titularidade_cnpj or '',
        titularidade_razao_social=ag.titularidade_razao_social or '',
        ativo=ag.ativo,
        data_criacao=ag.data_criacao.isoformat() if ag.data_criacao else None,
    )


@router.get("/agencias", response_model=List[AgenciaResponse])
def listar_agencias(
    db: Session = Depends(get_db_session),
    _: str = Depends(require_setor),
):
    """Lista todas as agências cadastradas."""
    agencias = db.query(AgenciaModel).order_by(AgenciaModel.agencia_nome).all()
    return [_agencia_to_response(a) for a in agencias]


@router.post("/agencias", response_model=AgenciaResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_agencia(
    body: AgenciaCreate,
    db: Session = Depends(get_db_session),
    _: str = Depends(require_setor),
):
    """Cadastra nova agência de viagens."""
    cnpj_norm = (body.cnpj or '').strip().replace('.','').replace('/','').replace('-','')
    if cnpj_norm and db.query(AgenciaModel).filter(AgenciaModel.cnpj == cnpj_norm).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="CNPJ já cadastrado.")

    nova = AgenciaModel(
        agencia_nome=body.agencia_nome.strip(),
        razao_social=body.razao_social.strip(),
        cnpj=cnpj_norm,
        inscricao_estadual=body.inscricao_estadual.strip(),
        email=body.email.strip(),
        cep=body.cep.strip(),
        logradouro=body.logradouro.strip(),
        numero=body.numero.strip(),
        complemento=body.complemento.strip(),
        bairro=body.bairro.strip(),
        municipio=body.municipio.strip(),
        uf=body.uf.strip().upper(),
        banco_nome=body.banco_nome.strip(),
        banco_codigo=body.banco_codigo.strip(),
        agencia_bancaria=body.agencia_bancaria.strip(),
        conta_bancaria=body.conta_bancaria.strip(),
        tipo_conta=body.tipo_conta.strip().upper() or 'CC',
        titularidade_cnpj=(body.titularidade_cnpj or '').strip(),
        titularidade_razao_social=(body.titularidade_razao_social or '').strip(),
        ativo=True,
    )
    db.add(nova)
    db.commit()
    db.refresh(nova)
    return _agencia_to_response(nova)


@router.put("/agencias/{agencia_id}", response_model=AgenciaResponse)
def atualizar_agencia(
    agencia_id: int,
    body: AgenciaUpdate,
    db: Session = Depends(get_db_session),
    _: str = Depends(require_setor),
):
    """Atualiza dados de uma agência."""
    ag = db.query(AgenciaModel).filter(AgenciaModel.id == agencia_id).first()
    if not ag:
        raise HTTPException(status_code=404, detail="Agência não encontrada.")

    for field in _AGENCIA_STR_FIELDS:
        val = getattr(body, field, None)
        if val is not None:
            setattr(ag, field, val.strip() if isinstance(val, str) else val)
    if body.ativo is not None:
        ag.ativo = body.ativo

    db.commit()
    db.refresh(ag)
    return _agencia_to_response(ag)


@router.delete("/agencias/{agencia_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_agencia(
    agencia_id: int,
    db: Session = Depends(get_db_session),
    _: str = Depends(require_setor),
):
    """Remove permanentemente uma agência do sistema."""
    ag = db.query(AgenciaModel).filter(AgenciaModel.id == agencia_id).first()
    if not ag:
        raise HTTPException(status_code=404, detail="Agência não encontrada.")
    db.delete(ag)
    db.commit()


# ── Telemetria e Auditoria Operacional (Acessos/Onboarding) ───────────────────

@router.get("/stats")
def obter_stats_setor(
    db: Session = Depends(get_db_session),
    _: str = Depends(require_setor),
):
    """Retorna dados de telemetria adicionais para o setor (como viajantes ativos hoje)."""
    from app.infrastructure.orm.models import LogAcessoModel
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    limite_tempo = datetime.now() - timedelta(hours=24)
    
    try:
        ativos_hoje = (
            db.query(func.count(func.distinct(LogAcessoModel.username)))
            .filter(LogAcessoModel.status_acesso == "SUCESSO")
            .filter(LogAcessoModel.data_criacao >= limite_tempo)
            .scalar()
        ) or 0
    except Exception:
        ativos_hoje = 0
        
    return {"ativos_hoje": ativos_hoje}


@router.get("/alertas-acesso")
def obter_alertas_acesso(
    db: Session = Depends(get_db_session),
    _: str = Depends(require_setor),
):
    """Lista as tentativas de login bloqueadas nas últimas 48 horas."""
    from app.infrastructure.orm.models import LogAcessoModel
    from sqlalchemy import desc
    from datetime import datetime, timedelta
    
    limite_tempo = datetime.now() - timedelta(hours=48)
    
    try:
        alertas = (
            db.query(LogAcessoModel)
            .filter(LogAcessoModel.status_acesso == "BLOQUEADO")
            .filter(LogAcessoModel.data_criacao >= limite_tempo)
            .order_by(desc(LogAcessoModel.data_criacao))
            .all()
        )
    except Exception:
        alertas = []
        
    return [
        {
            "id": a.id,
            "username": a.username,
            "ip_origem": a.ip_origem or "",
            "observacao": a.observacao or "",
            "data_criacao": a.data_criacao.isoformat() if a.data_criacao else None
        }
        for a in alertas
    ]

