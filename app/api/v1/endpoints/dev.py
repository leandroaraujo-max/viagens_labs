"""
Portal do Desenvolvedor — endpoints exclusivos para G_ACCESS_VIAGENSLABS_DEV.
Acesso irrestrito a toda a plataforma: métricas, solicitações, agências, configuração.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional, List
import logging
import os

from app.api.dependencies import get_db_session, require_dev
from app.infrastructure.orm.models import (
    SolicitacaoModel, AgenciaModel, CotacaoModel, VoucherModel, TokenAprovacaoModel, UsuarioQATesteModel
)
from app.domain.models.schemas import UsuarioQATesteCreate, UsuarioQATesteResponse
from app.core.config import settings
from app.core.security import get_password_hash

router = APIRouter()

LOG_FILES = {
    "app_out": [
        r"c:\Projetos\viagens_labs\logs\viagenslabs_service.out.log",
        r"C:\Projetos\viagens_labs\logs\viagenslabs_service.out.log",
    ],
    "app_err": [
        r"c:\Projetos\viagens_labs\logs\viagenslabs_service.err.log",
        r"C:\Projetos\viagens_labs\logs\viagenslabs_service.err.log",
    ],
    "nginx_access": [
        r"C:\nginx\logs\access.log",
        r"c:\nginx\logs\access.log",
        r"C:\nginx-1.24.0\logs\access.log",
        r"c:\nginx-1.24.0\logs\access.log",
    ],
    "nginx_error": [
        r"C:\nginx\logs\error.log",
        r"c:\nginx\logs\error.log",
        r"C:\nginx-1.24.0\logs\error.log",
        r"c:\nginx-1.24.0\logs\error.log",
    ],
    "nginx_service_err": [
        r"c:\Projetos\viagens_labs\logs\viagenslabs_service.wrapper.log",
        r"C:\Projetos\viagens_labs\logs\viagenslabs_service.wrapper.log",
    ]
}

def tail_file(filepath: str, lines_count: int = 100) -> str:
    if not os.path.exists(filepath):
        return f"[LOGS] Arquivo {filepath} não existe."
    try:
        chunk_size = 4096
        with open(filepath, "rb") as f:
            f.seek(0, os.SEEK_END)
            file_size = f.tell()
            
            lines = []
            buffer = bytearray()
            seek_pos = file_size
            
            while seek_pos > 0 and len(lines) <= lines_count:
                old_seek_pos = seek_pos
                seek_pos = max(0, seek_pos - chunk_size)
                f.seek(seek_pos)
                chunk = f.read(old_seek_pos - seek_pos)
                buffer = chunk + buffer
                lines = buffer.split(b"\n")
            
            last_lines = lines[-lines_count:]
            return b"\n".join(last_lines).decode("utf-8", errors="ignore")
    except Exception:
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                return "".join(f.readlines()[-lines_count:])
        except Exception as e2:
            return f"[ERRO] Falha ao ler logs: {e2}"

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
    agencias = db.query(AgenciaModel).order_by(AgenciaModel.agencia_nome).all()
    return [
        {
            "id": a.id,
            "agencia_nome": a.agencia_nome or '',
            "razao_social": a.razao_social or '',
            "cnpj": a.cnpj or '',
            "inscricao_estadual": a.inscricao_estadual or '',
            "email": a.email or '',
            "cep": a.cep or '',
            "logradouro": a.logradouro or '',
            "numero": a.numero or '',
            "complemento": a.complemento or '',
            "bairro": a.bairro or '',
            "municipio": a.municipio or '',
            "uf": a.uf or '',
            "banco_nome": a.banco_nome or '',
            "banco_codigo": a.banco_codigo or '',
            "agencia_bancaria": a.agencia_bancaria or '',
            "conta_bancaria": a.conta_bancaria or '',
            "tipo_conta": a.tipo_conta or 'CC',
            "titularidade_cnpj": a.titularidade_cnpj or '',
            "titularidade_razao_social": a.titularidade_razao_social or '',
            "ativo": a.ativo,
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
    ag.ativo = not ag.ativo
    db.commit()
    return {"id": ag.id, "ativo": ag.ativo}



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


# ── Gestão de QA & Exclusão de Solicitações ───────────────────────────────────

@router.delete("/solicitacoes/{solicitacao_id}", status_code=204)
def excluir_solicitacao(
    solicitacao_id: int,
    db: Session = Depends(get_db_session),
    _: str = Depends(require_dev),
):
    """Exclui uma solicitação de viagem de ponta a ponta, com exclusão em cascata."""
    sol = db.query(SolicitacaoModel).filter(SolicitacaoModel.id == solicitacao_id).first()
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada.")
    
    # 1. Casamentos
    from app.infrastructure.orm.models import CasamentoModel, LogEventoModel, TokenAgenciaModel
    db.query(CasamentoModel).filter(
        (CasamentoModel.solicitacao_a_id == solicitacao_id) | 
        (CasamentoModel.solicitacao_b_id == solicitacao_id)
    ).delete(synchronize_session=False)
    
    # 2. Vouchers
    db.query(VoucherModel).filter(VoucherModel.solicitacao_id == solicitacao_id).delete(synchronize_session=False)
    
    # 3. Cotações
    db.query(CotacaoModel).filter(CotacaoModel.solicitacao_id == solicitacao_id).delete(synchronize_session=False)
    
    # 4. Tokens da Agência
    db.query(TokenAgenciaModel).filter(TokenAgenciaModel.solicitacao_id == solicitacao_id).delete(synchronize_session=False)
    
    # 5. Tokens de Aprovação
    db.query(TokenAprovacaoModel).filter(TokenAprovacaoModel.solicitacao_id == solicitacao_id).delete(synchronize_session=False)
    
    # 6. Logs de Evento
    db.query(LogEventoModel).filter(LogEventoModel.solicitacao_id == solicitacao_id).delete(synchronize_session=False)
    
    # 7. Solicitação principal
    db.delete(sol)
    db.commit()
    return None


@router.get("/usuarios-qa", response_model=List[UsuarioQATesteResponse])
def listar_usuarios_qa(
    db: Session = Depends(get_db_session),
    _: str = Depends(require_dev),
):
    """Lista todos os testadores QA cadastrados."""
    return db.query(UsuarioQATesteModel).order_by(UsuarioQATesteModel.data_criacao.desc()).all()


@router.post("/usuarios-qa", response_model=UsuarioQATesteResponse, status_code=201)
def cadastrar_usuario_qa(
    body: UsuarioQATesteCreate,
    db: Session = Depends(get_db_session),
    _: str = Depends(require_dev),
):
    """Cadastra um novo testador QA."""
    existente = db.query(UsuarioQATesteModel).filter(UsuarioQATesteModel.username == body.username).first()
    if existente:
        raise HTTPException(status_code=409, detail="Este username QA já está cadastrado.")
    
    novo = UsuarioQATesteModel(
        username=body.username.strip(),
        email=body.email.strip(),
        ativo=True,
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@router.delete("/usuarios-qa/{qa_id}", status_code=204)
def excluir_usuario_qa(
    qa_id: int,
    db: Session = Depends(get_db_session),
    _: str = Depends(require_dev),
):
    """Exclui um testador QA."""
    qa = db.query(UsuarioQATesteModel).filter(UsuarioQATesteModel.id == qa_id).first()
    if not qa:
        raise HTTPException(status_code=404, detail="Testador QA não encontrado.")
    db.delete(qa)
    db.commit()
    return None


# ── Dashboard de Monitoramento de Logs ───────────────────────────────────────

@router.get("/logs")
def ler_logs(
    servico: str = Query("app_out"),
    linhas: int = Query(100, le=500),
    _: str = Depends(require_dev),
):
    """Retorna as últimas N linhas de log do serviço selecionado."""
    paths = LOG_FILES.get(servico)
    if not paths:
        raise HTTPException(status_code=400, detail="Serviço de log inválido.")
    
    actual_path = None
    for p in paths:
        if os.path.exists(p):
            actual_path = p
            break
            
    if not actual_path:
        return {
            "caminho": paths[0],
            "conteudo": f"[LOGS] Arquivo de log para '{servico}' não encontrado nos caminhos mapeados."
        }
        
    return {
        "caminho": actual_path,
        "conteudo": tail_file(actual_path, linhas)
    }


# ── Histórico de Acessos e Auditoria ─────────────────────────────────────────

@router.get("/logs-acesso")
def listar_logs_acesso(
    db: Session = Depends(get_db_session),
    _: str = Depends(require_dev),
):
    """Lista os últimos 100 registros de auditoria da tabela log_acessos."""
    from app.infrastructure.orm.models import LogAcessoModel
    logs = db.query(LogAcessoModel).order_by(desc(LogAcessoModel.data_criacao)).limit(100).all()
    return [
        {
            "id": l.id,
            "username": l.username,
            "nome": l.nome or "",
            "perfil": l.perfil or "",
            "ip_origem": l.ip_origem or "",
            "status_acesso": l.status_acesso or "SUCESSO",
            "observacao": l.observacao or "",
            "data_criacao": l.data_criacao.isoformat() if l.data_criacao else None
        }
        for l in logs
    ]


@router.post("/consultas/executar")
def executar_consulta_predefinida(
    body: dict,
    db: Session = Depends(get_db_session),
    _: str = Depends(require_dev),
):
    """Executa uma consulta SQL predefinida de forma segura."""
    query_id = body.get("query_id")
    
    queries = {
        "custos_cc": """
            SELECT 
                cod_centro_custo AS "Código CC", 
                centro_custo AS "Nome Centro de Custo", 
                COUNT(id) AS "Total Viagens", 
                COALESCE(SUM(valor_reembolsavel_agencia), 0) AS "Total Reembolsado (R$)",
                COALESCE(SUM(taxa_cancelamento_agencia), 0) AS "Total Multas (R$)"
            FROM solicitacoes 
            GROUP BY cod_centro_custo, centro_custo 
            ORDER BY COUNT(id) DESC;
        """,
        "market_share": """
            SELECT 
                agencia_nome AS "Agência de Viagem", 
                COUNT(id) AS "Total Cotações Recebidas",
                SUM(CASE WHEN status = 'APROVADO' THEN 1 ELSE 0 END) AS "Cotações Vencidas (Aprovadas)",
                ROUND(100.0 * SUM(CASE WHEN status = 'APROVADO' THEN 1 ELSE 0 END) / NULLIF(COUNT(id), 0), 2) || '%' AS "Taxa de Conversão"
            FROM cotacoes 
            GROUP BY agencia_nome 
            ORDER BY SUM(CASE WHEN status = 'APROVADO' THEN 1 ELSE 0 END) DESC;
        """,
        "auditoria_delegacoes": """
            SELECT 
                username AS "Usuário Dev", 
                nome AS "Nome do Dev", 
                perfil AS "Perfil", 
                observacao AS "Ação Auditada", 
                data_criacao AS "Data e Hora"
            FROM log_acessos 
            WHERE observacao LIKE '%Delegação manual%' 
            ORDER BY data_criacao DESC;
        """,
        "creditos_cia": """
            SELECT 
                companhia_credito AS "Companhia Aérea", 
                COUNT(id) AS "Quantidade de Créditos",
                COALESCE(SUM(valor_credito_gerado), 0) AS "Total Créditos Acumulados (R$)"
            FROM solicitacoes 
            WHERE tipo_solicitacao_cancelamento = 'CANCELAR' 
              AND credito_utilizado = FALSE 
            GROUP BY companhia_credito 
            ORDER BY COALESCE(SUM(valor_credito_gerado), 0) DESC;
        """
    }
    
    if query_id not in queries:
        raise HTTPException(status_code=400, detail="Consulta predefinida não encontrada.")
        
    sql_text = queries[query_id]
    try:
        from sqlalchemy import text
        result = db.execute(text(sql_text))
        
        # Obter cabeçalhos de coluna
        headers = list(result.keys())
        
        # Obter linhas
        rows = [dict(zip(headers, row)) for row in result.fetchall()]
        
        return {
            "headers": headers,
            "rows": rows,
            "query_sql": sql_text.strip()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao executar consulta: {str(e)}")


@router.get("/delegacoes")
def listar_delegacoes_ad(
    db: Session = Depends(get_db_session),
    _: str = Depends(require_dev),
):
    """Retorna todas as delegações AD cadastradas."""
    from app.infrastructure.orm.models import AutorizacaoTerceiroModel
    delegacoes = db.query(AutorizacaoTerceiroModel).order_by(AutorizacaoTerceiroModel.data_criacao.desc()).all()
    return [
        {
            "id": d.id,
            "solicitante": d.solicitante_username,
            "terceiro_username": d.terceiro_username,
            "terceiro_nome": d.terceiro_nome or "",
            "terceiro_email": d.terceiro_email or "",
            "pdf_path": d.pdf_path or "",
            "status": d.status,
            "operador": d.operador_setor or "",
            "data_criacao": d.data_criacao.isoformat() if d.data_criacao else None,
        }
        for d in delegacoes
    ]


@router.post("/delegacoes", status_code=201)
def cadastrar_delegacao_ad(
    body: dict,
    db: Session = Depends(get_db_session),
    username_dev: str = Depends(require_dev),
):
    """Cadastra diretamente uma delegação AD com status APROVADA e trilha de auditoria."""
    from app.infrastructure.orm.models import AutorizacaoTerceiroModel, LogAcessoModel
    solicitante = body.get("solicitante", "").strip()
    viajante = body.get("viajante", "").strip()
    
    if not solicitante or not viajante:
        raise HTTPException(status_code=400, detail="Forneça o usuário solicitante e viajante.")
        
    # Busca dados do viajante (terceiro_username) via BigQuery para salvar nome/email corretos
    try:
        from app.infrastructure.bigquery_service import BigQueryService
        bq = BigQueryService("maga-bigdata", "maga-bigdata.kirk.assignee", "maga-bigdata.mlpap.mag_v_funcionarios_ativos")
        dados = bq.buscar_colaborador(viajante)
    except Exception:
        dados = None
        
    terceiro_nome = dados.get("nome", "") if dados else f"Viajante {viajante}"
    terceiro_email = dados.get("email", "") if dados else f"{viajante}@magazineluiza.com.br"
    
    # Cria a delegação como APROVADA
    nova = AutorizacaoTerceiroModel(
        solicitante_username=solicitante,
        terceiro_username=viajante,
        terceiro_nome=terceiro_nome,
        terceiro_email=terceiro_email,
        pdf_path="MANUAL_DEV",
        status="APROVADA",
        observacao_setor=f"Delegação manual inserida pelo Desenvolvedor {username_dev}",
        operador_setor=username_dev,
        data_decisao=func.now()
    )
    db.add(nova)
    db.commit()
    db.refresh(nova)
    
    # Registra no log de acessos/auditoria
    log = LogAcessoModel(
        username=username_dev,
        perfil="dev",
        status_acesso="SUCESSO",
        observacao=f"Delegação manual inserida pelo Desenvolvedor {username_dev} (Terceiro: {solicitante} -> Titular: {viajante})",
        data_criacao=func.now()
    )
    db.add(log)
    db.commit()
    
    return {"id": nova.id, "status": "APROVADA", "mensagem": "Delegação manual ativada com sucesso."}


@router.delete("/delegacoes/{delegacao_id}", status_code=204)
def remover_delegacao_ad(
    delegacao_id: int,
    db: Session = Depends(get_db_session),
    username_dev: str = Depends(require_dev),
):
    """Exclui diretamente uma delegação AD com trilha de auditoria."""
    from app.infrastructure.orm.models import AutorizacaoTerceiroModel, LogAcessoModel
    aut = db.query(AutorizacaoTerceiroModel).filter(AutorizacaoTerceiroModel.id == delegacao_id).first()
    if not aut:
        raise HTTPException(status_code=404, detail="Delegação não encontrada.")
        
    sol = aut.solicitante_username
    viaj = aut.terceiro_username
    
    db.delete(aut)
    db.commit()
    
    # Registra exclusão no log de acessos
    log = LogAcessoModel(
        username=username_dev,
        perfil="dev",
        status_acesso="SUCESSO",
        observacao=f"Delegação manual excluída pelo Desenvolvedor {username_dev} (Terceiro: {sol} -> Titular: {viaj})",
        data_criacao=func.now()
    )
    db.add(log)
    db.commit()
    return None

