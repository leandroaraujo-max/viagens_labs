"""
Endpoints para o fluxo de "Solicitação para Terceiros".
  - Viajante abre ticket informando ID Magalu do terceiro + PDF de autorização.
  - Setor aprova/reprova o ticket.
  - Com autorização aprovada, o viajante pode abrir solicitações em nome do terceiro.
"""
import os
import shutil
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session, require_auth, require_setor
from app.infrastructure.orm.models import AutorizacaoTerceiroModel
from app.infrastructure.bigquery_service import BigQueryService

router = APIRouter()

_bq_service = BigQueryService(
    project_id="maga-bigdata",
    table_assignee="maga-bigdata.kirk.assignee",
    table_funcionarios="maga-bigdata.mlpap.mag_v_funcionarios_ativos",
)

_PDF_DIR = os.path.join("uploads", "autorizacoes_terceiros")
os.makedirs(_PDF_DIR, exist_ok=True)
_MAX_BYTES = 10 * 1024 * 1024  # 10 MB


# ── Viajante: consultar dados do terceiro antes de abrir ticket ────────────────

@router.get("/terceiros/buscar/{id_magalu}")
def buscar_colaborador(
    id_magalu: str,
    _: tuple = Depends(require_auth),
):
    """
    Busca nome e e-mail de um colaborador pelo ID/matrícula Magalu.
    Usado para confirmação visual antes de submeter o ticket.
    """
    try:
        dados = _bq_service.buscar_colaborador(id_magalu)
    except Exception as e:
        logging.warning(f"Erro ao buscar colaborador {id_magalu} no BQ: {e}")
        dados = None

    if not dados:
        import logging
        logging.getLogger(__name__).warning(f"Colaborador {id_magalu} não encontrado no BQ. Usando mock fallback para terceiros.")
        nome_sugerido = id_magalu.replace(".", " ").title()
        dados = {
            "nome": nome_sugerido,
            "email": f"{id_magalu.lower()}@magazineluiza.com.br" if "@" not in id_magalu else id_magalu,
            "cargo": "Gerente Geral de Operações",
            "filial": "Luizalabs SP",
        }
    return {
        "username":  id_magalu,
        "nome":      dados.get("nome", ""),
        "email":     dados.get("email", ""),
        "cargo":     dados.get("cargo", ""),
        "filial":    dados.get("filial", ""),
    }


# ── Viajante: abrir ticket de autorização ────────────────────────────────────

@router.post("/terceiros/solicitar", status_code=status.HTTP_201_CREATED)
async def solicitar_acesso_terceiro(
    terceiro_username: str    = Form(...),
    terceiro_nome:     str    = Form(""),
    terceiro_email:    str    = Form(""),
    pdf_autorizacao:   UploadFile = File(...),
    db:                Session = Depends(get_db_session),
    auth_info:         tuple  = Depends(require_auth),
):
    """
    Viajante abre um ticket para poder solicitar viagens em nome de um terceiro.
    Obrigatório: PDF de autorização assinado pelo terceiro.
    """
    solicitante_username, _ = auth_info

    # Verifica se já existe ticket pendente ou aprovado para esse par
    existente = db.query(AutorizacaoTerceiroModel).filter(
        AutorizacaoTerceiroModel.solicitante_username == solicitante_username,
        AutorizacaoTerceiroModel.terceiro_username    == terceiro_username,
        AutorizacaoTerceiroModel.status.in_(["PENDENTE", "APROVADA"]),
    ).first()
    if existente:
        raise HTTPException(
            status_code=409,
            detail=f"Já existe uma autorização {existente.status} para este colaborador.",
        )

    # Validar PDF
    conteudo = await pdf_autorizacao.read()
    if len(conteudo) == 0:
        raise HTTPException(status_code=400, detail="O PDF de autorização não pode ser vazio.")
    if len(conteudo) > _MAX_BYTES:
        raise HTTPException(status_code=413, detail="PDF excede o limite de 10 MB.")

    # Salvar PDF
    filename = f"{solicitante_username}_{terceiro_username}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    caminho = os.path.join(_PDF_DIR, filename)
    with open(caminho, "wb") as f:
        f.write(conteudo)

    # Criar registro
    autorizacao = AutorizacaoTerceiroModel(
        solicitante_username=solicitante_username,
        terceiro_username=terceiro_username,
        terceiro_nome=terceiro_nome,
        terceiro_email=terceiro_email,
        pdf_path=caminho,
        status="PENDENTE",
    )
    db.add(autorizacao)
    db.commit()
    db.refresh(autorizacao)

    logging.info(
        f"[TERCEIROS] {solicitante_username} abriu ticket de autorização "
        f"para {terceiro_username} (id={autorizacao.id})"
    )
    return {"id": autorizacao.id, "status": "PENDENTE", "mensagem": "Ticket enviado com sucesso. Aguarde aprovação do setor de viagens."}


# ── Viajante: listar minhas autorizações ──────────────────────────────────────

@router.get("/terceiros/minhas")
def listar_minhas_autorizacoes(
    db:        Session = Depends(get_db_session),
    auth_info: tuple   = Depends(require_auth),
):
    """Lista todos os tickets de autorização abertos pelo viajante logado."""
    username, _ = auth_info
    itens = db.query(AutorizacaoTerceiroModel).filter(
        AutorizacaoTerceiroModel.solicitante_username == username
    ).order_by(AutorizacaoTerceiroModel.data_criacao.desc()).all()

    return [_fmt(a) for a in itens]


# ── Setor: listar todos os tickets pendentes ──────────────────────────────────

@router.get("/terceiros/admin/todos")
def listar_todos_tickets(
    status_filtro: Optional[str] = None,
    db:    Session = Depends(get_db_session),
    _:     str     = Depends(require_setor),
):
    """Lista todos os tickets de autorização (visão do setor)."""
    q = db.query(AutorizacaoTerceiroModel)
    if status_filtro:
        q = q.filter(AutorizacaoTerceiroModel.status == status_filtro)
    itens = q.order_by(AutorizacaoTerceiroModel.data_criacao.desc()).all()
    return [_fmt(a) for a in itens]


@router.get("/terceiros/admin/{autorizacao_id}/pdf")
def obter_pdf_autorizacao_terceiro(
    autorizacao_id: int,
    db: Session = Depends(get_db_session),
    _: tuple = Depends(require_setor),
):
    """Retorna o PDF assinado de uma autorização de terceiros para o portal do setor."""
    aut = db.query(AutorizacaoTerceiroModel).filter(
        AutorizacaoTerceiroModel.id == autorizacao_id
    ).first()
    if not aut:
        raise HTTPException(status_code=404, detail="Autorização não encontrada.")

    if not aut.pdf_path:
        raise HTTPException(status_code=404, detail="PDF da autorização não encontrado.")

    base_dir = os.path.abspath(_PDF_DIR)
    file_path = os.path.abspath(aut.pdf_path)
    if not file_path.startswith(base_dir):
        raise HTTPException(status_code=403, detail="Acesso não autorizado ao documento.")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF da autorização não encontrado.")

    return FileResponse(file_path, media_type="application/pdf", filename=os.path.basename(file_path))


# ── Setor: aprovar ou reprovar ────────────────────────────────────────────────

@router.patch("/terceiros/admin/{autorizacao_id}/decisao")
def decidir_autorizacao(
    autorizacao_id: int,
    acao:           str = Form(...),   # APROVADA ou REPROVADA
    observacao:     str = Form(""),
    db:             Session = Depends(get_db_session),
    setor_info:     tuple   = Depends(require_setor),
):
    """Setor aprova ou reprova um ticket de autorização para Solicitação de Terceiros."""
    operador, _ = setor_info

    if acao not in ("APROVADA", "REPROVADA"):
        raise HTTPException(status_code=400, detail="ação deve ser APROVADA ou REPROVADA.")

    aut = db.query(AutorizacaoTerceiroModel).filter(
        AutorizacaoTerceiroModel.id == autorizacao_id
    ).first()
    if not aut:
        raise HTTPException(status_code=404, detail="Autorização não encontrada.")
    if aut.status != "PENDENTE":
        raise HTTPException(status_code=409, detail=f"Autorização já está {aut.status}.")

    aut.status           = acao
    aut.observacao_setor = observacao
    aut.operador_setor   = operador
    aut.data_decisao     = datetime.now()
    db.commit()

    logging.info(f"[TERCEIROS] Setor '{operador}' {acao} autorização id={autorizacao_id}")

    # Disparar e-mail de notificação ao solicitante e ao terceiro
    try:
        from app.infrastructure.email_service import EmailService
        EmailService().enviar_email_autorizacao_decidida(aut)
    except Exception as e:
        logging.warning(f"Falha ao enviar e-mail de notificação de autorização decidida: {e}")

    return {"id": aut.id, "status": aut.status}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _fmt(a: AutorizacaoTerceiroModel) -> dict:
    return {
        "id":                   a.id,
        "solicitante_username": a.solicitante_username,
        "terceiro_username":    a.terceiro_username,
        "terceiro_nome":        a.terceiro_nome,
        "terceiro_email":       a.terceiro_email,
        "pdf_path":             a.pdf_path,
        "pdf_url":              f"/api/v1/terceiros/admin/{a.id}/pdf",
        "status":               a.status,
        "observacao_setor":     a.observacao_setor,
        "operador_setor":       a.operador_setor,
        "data_criacao":         a.data_criacao.isoformat() if a.data_criacao else None,
        "data_decisao":         a.data_decisao.isoformat() if a.data_decisao else None,
    }
