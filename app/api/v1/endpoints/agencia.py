from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

from app.api.dependencies import get_db_session, require_agencia
from app.domain.models import schemas
from app.infrastructure.orm.models import CotacaoModel, SolicitacaoModel, TokenAgenciaModel
from app.services.cotacao_service import CotacaoService
from app.services.casamento_service import CasamentoService
from app.services.voucher_service import VoucherService

router = APIRouter()
_cotacao_svc = CotacaoService()
_casamento_svc = CasamentoService()
_voucher_svc = VoucherService()

_MAX_BYTES = 20 * 1024 * 1024  # 20 MB


# ── Helpers ───────────────────────────────────────────────────────────────────

def _validar_token_agencia(
    token_uuid: str, finalidade: str, db: Session
) -> TokenAgenciaModel:
    """
    Valida o token de acesso da agência.
    Levanta 404 se não encontrado/usado, 410 se expirado.
    """
    tok = (
        db.query(TokenAgenciaModel)
        .filter(
            TokenAgenciaModel.uuid == token_uuid,
            TokenAgenciaModel.finalidade == finalidade,
            TokenAgenciaModel.status == "PENDENTE",
        )
        .first()
    )
    if not tok:
        raise HTTPException(status_code=404, detail="Link inválido ou já utilizado.")
    if datetime.now() > tok.data_expiracao:
        tok.status = "EXPIRADO"
        db.commit()
        raise HTTPException(
            status_code=410,
            detail="Este link expirou. Solicite ao setor de viagens um novo link.",
        )
    return tok


def _build_agencia_response(sol, cotacao, casamentos) -> schemas.SolicitacaoAgenciaResponse:
    return schemas.SolicitacaoAgenciaResponse(
        id=sol.id,
        protocolo=sol.protocolo,
        solicitante_username=sol.solicitante_username,
        destino_cidade=sol.destino_cidade,
        destino_estado=sol.destino_estado,
        origem_cidade=sol.origem_cidade,
        data_ida=sol.data_ida,
        data_volta=sol.data_volta,
        tipo_servico=sol.tipo_servico,
        classificacao=sol.classificacao,
        status=sol.status,
        motivo_viagem=sol.motivo_viagem,
        aereo_periodo_preferido=sol.aereo_periodo_preferido,
        aereo_tipo_trecho=sol.aereo_tipo_trecho,
        bagagem_extra=sol.bagagem_extra,
        assento_especial=sol.assento_especial,
        rodov_periodo_preferido=sol.rodov_periodo_preferido,
        rodov_tipo_onibus=sol.rodov_tipo_onibus,
        preferencia_hotel_nome=sol.preferencia_hotel_nome,
        carro_cidade_retirada=sol.carro_cidade_retirada,
        carro_hora_retirada=sol.carro_hora_retirada,
        carro_cidade_devolucao=sol.carro_cidade_devolucao,
        carro_hora_devolucao=sol.carro_hora_devolucao,
        observacoes_viajante=sol.observacoes_viajante,
        viajante_nome=getattr(sol, 'viajante_nome', '') or '',
        viajante_matricula=getattr(sol, 'viajante_matricula', '') or '',
        viajante_cargo=getattr(sol, 'viajante_cargo', '') or '',
        viajante_filial=getattr(sol, 'viajante_filial', '') or '',
        viajante_cpf=getattr(sol, 'viajante_cpf', '') or '',
        viajante_email=getattr(sol, 'viajante_email', '') or '',
        viajante_centro_custo=getattr(sol, 'viajante_centro_custo', '') or '',
        viajante_cod_centro_custo=getattr(sol, 'viajante_cod_centro_custo', '') or '',
        viajante_celular=getattr(sol, 'viajante_celular', '') or '',
        viajante_data_nascimento=getattr(sol, 'viajante_data_nascimento', '') or '',
        preferencia_voo=getattr(sol, 'preferencia_voo', '') or '',
        preferencia_voo_volta=getattr(sol, 'preferencia_voo_volta', '') or '',
        cotacao=schemas.CotacaoResponse.model_validate(cotacao) if cotacao else None,
        casamentos=casamentos,
    )


@router.get("/solicitacoes", response_model=List[schemas.SolicitacaoAgenciaResponse])
def listar_solicitacoes(
    status_filtro: Optional[str] = None,
    db: Session = Depends(get_db_session),
    agencia_info: tuple = Depends(require_agencia),
):
    """
    Lista as solicitações disponíveis para cotação.
    Filtro opcional: ?status_filtro=AGUARDANDO_COTACAO
    """
    solicitacoes = _cotacao_svc.listar_solicitacoes_agencia(db, status_filtro)
    resultado = []
    for sol in solicitacoes:
        cotacao = db.query(CotacaoModel).filter_by(solicitacao_id=sol.id).first()
        casamentos = _casamento_svc.listar_casamentos_da_solicitacao(db, sol.id)
        resultado.append(_build_agencia_response(sol, cotacao, casamentos))
    return resultado


@router.get("/solicitacoes/{solicitacao_id}", response_model=schemas.SolicitacaoAgenciaResponse)
def detalhar_solicitacao(
    solicitacao_id: int,
    db: Session = Depends(get_db_session),
    agencia_info: tuple = Depends(require_agencia),
):
    """Detalhes de uma solicitação específica para a agência."""
    sol, cotacao = _cotacao_svc.get_solicitacao_com_cotacao(db, solicitacao_id)
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada.")

    statuses_visiveis = {"AGUARDANDO_COTACAO", "COTACAO_ENVIADA", "PENDENTE_APROVACAO_SETOR_COTACAO", "APROVADA_AGUARDANDO_VOUCHER", "CONCLUIDA"}
    if sol.status not in statuses_visiveis:
        raise HTTPException(
            status_code=403,
            detail="Solicitação não disponível no portal da agência.",
        )

    casamentos = _casamento_svc.listar_casamentos_da_solicitacao(db, solicitacao_id)
    return _build_agencia_response(sol, cotacao, casamentos)


@router.post(
    "/solicitacoes/{solicitacao_id}/cotacao",
    response_model=schemas.CotacaoResponse,
    status_code=status.HTTP_201_CREATED,
)
def registrar_cotacao(
    solicitacao_id: int,
    dados: schemas.CotacaoCreate,
    db: Session = Depends(get_db_session),
    agencia_info: tuple = Depends(require_agencia),
):
    """Registra ou atualiza a cotação de uma solicitação."""
    agencia_usuario, agencia_nome = agencia_info
    try:
        cotacao = _cotacao_svc.registrar_cotacao(
            db=db,
            solicitacao_id=solicitacao_id,
            dados=dados,
            agencia_usuario=agencia_usuario,
            agencia_nome=agencia_nome,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return schemas.CotacaoResponse.model_validate(cotacao)


# ══════════════════════════════════════════════════════════════════════════════
# Rotas de acesso por TOKEN (sem autenticação — agências externas via link e-mail)
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/token/{token_uuid}")
def consultar_por_token(token_uuid: str, db: Session = Depends(get_db_session)):
    """
    Retorna os dados da solicitação para a agência via link token (sem login).
    Responde com: { agencia_nome, finalidade_token, solicitacao: {...} }
    Usado por agencia.html quando ?token= está na URL.
    """
    # Busca o token (qualquer finalidade)
    tok = (
        db.query(TokenAgenciaModel)
        .filter(
            TokenAgenciaModel.uuid == token_uuid,
            TokenAgenciaModel.status == "PENDENTE",
        )
        .first()
    )
    if not tok:
        raise HTTPException(status_code=404, detail="Link inválido ou já utilizado.")
    if datetime.now() > tok.data_expiracao:
        tok.status = "EXPIRADO"
        db.commit()
        raise HTTPException(
            status_code=410,
            detail="Este link expirou. Solicite ao setor de viagens um novo link.",
        )

    sol = db.query(SolicitacaoModel).filter_by(id=tok.solicitacao_id).first()
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada.")
    cotacao = db.query(CotacaoModel).filter_by(
        solicitacao_id=sol.id, agencia_nome=tok.agencia_nome
    ).first()
    casamentos = _casamento_svc.listar_casamentos_da_solicitacao(db, sol.id)
    return {
        "agencia_nome":     tok.agencia_nome,
        "finalidade_token": tok.finalidade,   # COTACAO / VOUCHER
        "solicitacao":      _build_agencia_response(sol, cotacao, casamentos),
    }


@router.post(
    "/token/{token_uuid}/cotacao",
    response_model=schemas.CotacaoResponse,
    status_code=status.HTTP_201_CREATED,
)
def registrar_cotacao_por_token(
    token_uuid: str,
    dados: schemas.CotacaoCreate,
    db: Session = Depends(get_db_session),
):
    """Registra a cotação usando token de link (sem login). Token fica USADO após submissão."""
    tok = _validar_token_agencia(token_uuid, "COTACAO", db)
    try:
        cotacao = _cotacao_svc.registrar_cotacao(
            db=db,
            solicitacao_id=tok.solicitacao_id,
            dados=dados,
            agencia_usuario="link_token",
            agencia_nome=tok.agencia_nome,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    tok.status = "USADO"
    db.commit()
    return schemas.CotacaoResponse.model_validate(cotacao)


@router.post("/token/{token_uuid}/voucher")
async def upload_voucher_por_token(
    token_uuid:   str,
    tipo_voucher: str        = Form(...),
    arquivo:      UploadFile = File(...),
    db            = Depends(get_db_session),
):
    """Upload de voucher usando token de link (sem login). Não invalida o token — agência pode enviar 1 por tipo."""
    tok = _validar_token_agencia(token_uuid, "VOUCHER", db)

    sol: SolicitacaoModel = db.query(SolicitacaoModel).filter_by(id=tok.solicitacao_id).first()
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada.")
    if sol.status != "APROVADA_AGUARDANDO_VOUCHER":
        raise HTTPException(
            status_code=409,
            detail=f"Voucher não é esperado neste momento (status: {sol.status}).",
        )
    if sol.agencia_vencedora != tok.agencia_nome:
        raise HTTPException(status_code=403, detail="Token pertence a outra agência.")

    conteudo = await arquivo.read()
    if len(conteudo) > _MAX_BYTES:
        raise HTTPException(status_code=413, detail="Arquivo excede 20 MB.")
    if len(conteudo) == 0:
        raise HTTPException(status_code=400, detail="Arquivo vazio.")

    try:
        voucher = _voucher_svc.registrar_voucher(
            db=db,
            solicitacao=sol,
            tipo_voucher=tipo_voucher,
            arquivo_bytes=conteudo,
            filename=arquivo.filename or "voucher.pdf",
        )
        db.commit()
        db.refresh(voucher)
        db.refresh(sol)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {
        "id":                 voucher.id,
        "solicitacao_id":     voucher.solicitacao_id,
        "tipo_voucher":       voucher.tipo_voucher,
        "caminho_arquivo":    voucher.caminho_arquivo,
        "status_solicitacao": sol.status,
    }


@router.post("/token/{token_uuid}/liquidar-cancelamento")
async def liquidar_cancelamento_por_token(
    token_uuid: str,
    taxa_cancelamento_agencia: float = Form(0.0),
    valor_reembolsavel_agencia: float = Form(0.0),
    valor_credito_gerado: float = Form(0.0),
    companhia_credito: str = Form(""),
    arquivo: Optional[UploadFile] = File(None),
    db = Depends(get_db_session),
):
    """Permite à agência liquidar taxas e créditos de cancelamento/remarcação via link seguro."""
    # O token de cancelamento pode ser reusado, mas idealmente é do tipo VOUCHER ou similar.
    # Vamos validar contra qualquer token pendente daquela solicitação.
    tok = (
        db.query(TokenAgenciaModel)
        .filter(
            TokenAgenciaModel.uuid == token_uuid,
            TokenAgenciaModel.status == "PENDENTE",
        )
        .first()
    )
    if not tok:
        raise HTTPException(status_code=404, detail="Link inválido ou já utilizado.")
        
    sol: SolicitacaoModel = db.query(SolicitacaoModel).filter_by(id=tok.solicitacao_id).first()
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada.")
        
    if sol.status not in ["PENDENTE_CANCELAMENTO", "PENDENTE_REMARCACAO"]:
        raise HTTPException(
            status_code=409,
            detail=f"Esta solicitação não está aguardando liquidação da agência (status atual: {sol.status}).",
        )
        
    import os
    doc_path = None
    if arquivo:
        conteudo = await arquivo.read()
        if len(conteudo) > _MAX_BYTES:
            raise HTTPException(status_code=413, detail="Arquivo excede 20 MB.")
        if len(conteudo) > 0:
            os.makedirs(os.path.join("uploads", "cancelamentos"), exist_ok=True)
            filename = f"cancelamento_{sol.id}_{int(datetime.now().timestamp())}.pdf"
            doc_path = os.path.join("uploads", "cancelamentos", filename)
            with open(doc_path, "wb") as f:
                f.write(conteudo)
                
    sol.taxa_cancelamento_agencia = taxa_cancelamento_agencia
    sol.valor_reembolsavel_agencia = valor_reembolsavel_agencia
    sol.valor_credito_gerado = valor_credito_gerado
    sol.companhia_credito = companhia_credito
    if doc_path:
        sol.documento_cancelamento_caminho = doc_path
        
    if sol.tipo_solicitacao_cancelamento == "REMARCAR":
        sol.status = "PENDENTE_APROVACAO_REMARCACAO"
    else:
        sol.status = "PENDENTE_APROVACAO_CANCELAMENTO"
        
    # Invalida o token após liquidar
    tok.status = "USADO"
    
    db.commit()
    return {"protocolo": sol.protocolo, "status": sol.status, "mensagem": "Liquidação enviada ao setor de viagens para aprovação final."}


@router.post("/solicitacoes/{solicitacao_id}/liquidar-cancelamento")
async def liquidar_cancelamento_autenticado(
    solicitacao_id: int,
    taxa_cancelamento_agencia: float = Form(0.0),
    valor_reembolsavel_agencia: float = Form(0.0),
    valor_credito_gerado: float = Form(0.0),
    companhia_credito: str = Form(""),
    arquivo: Optional[UploadFile] = File(None),
    db = Depends(get_db_session),
    agencia_info: tuple = Depends(require_agencia),
):
    """Permite à agência autenticada liquidar taxas e créditos de cancelamento/remarcação."""
    agencia_usuario, agencia_nome = agencia_info
    sol: SolicitacaoModel = db.query(SolicitacaoModel).filter_by(id=solicitacao_id).first()
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada.")
        
    if sol.status not in ["PENDENTE_CANCELAMENTO", "PENDENTE_REMARCACAO"]:
        raise HTTPException(
            status_code=409,
            detail=f"Esta solicitação não está aguardando liquidação da agência (status atual: {sol.status}).",
        )
        
    import os
    doc_path = None
    if arquivo:
        conteudo = await arquivo.read()
        if len(conteudo) > _MAX_BYTES:
            raise HTTPException(status_code=413, detail="Arquivo excede 20 MB.")
        if len(conteudo) > 0:
            os.makedirs(os.path.join("uploads", "cancelamentos"), exist_ok=True)
            filename = f"cancelamento_{sol.id}_{int(datetime.now().timestamp())}.pdf"
            doc_path = os.path.join("uploads", "cancelamentos", filename)
            with open(doc_path, "wb") as f:
                f.write(conteudo)
                
    sol.taxa_cancelamento_agencia = taxa_cancelamento_agencia
    sol.valor_reembolsavel_agencia = valor_reembolsavel_agencia
    sol.valor_credito_gerado = valor_credito_gerado
    sol.companhia_credito = companhia_credito
    if doc_path:
        sol.documento_cancelamento_caminho = doc_path
        
    if sol.tipo_solicitacao_cancelamento == "REMARCAR":
        sol.status = "PENDENTE_APROVACAO_REMARCACAO"
    else:
        sol.status = "PENDENTE_APROVACAO_CANCELAMENTO"
        
    db.commit()
    return {"protocolo": sol.protocolo, "status": sol.status, "mensagem": "Liquidação enviada ao setor de viagens para aprovação final."}

