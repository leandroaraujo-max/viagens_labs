from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List, Tuple
import logging

from app.infrastructure.orm.models import SolicitacaoModel, CasamentoModel


# Janela de dias para considerar datas próximas
JANELA_TOTAL_DIAS = 2
JANELA_PARCIAL_B_DIAS = 7


def _servicos(sol: SolicitacaoModel) -> set:
    return set(s.strip() for s in (sol.tipo_servico or "").split(",") if s.strip())


def _calcular_match(a: SolicitacaoModel, b: SolicitacaoModel) -> str:
    """
    Regras de casamento:
      TOTAL    — mesmo destino, data_ida próxima (±2 dias) E mesmos serviços
      PARCIAL_A — mesmo destino, data_ida próxima (±2 dias), serviços diferentes mas com intersecção
      PARCIAL_B — mesmo destino, data_ida próxima (±7 dias), mesmos serviços
      NENHUM   — demais casos
    """
    if a.destino_cidade.strip().lower() != b.destino_cidade.strip().lower():
        return "NENHUM"

    diff_dias = abs((a.data_ida - b.data_ida).days)
    servicos_a = _servicos(a)
    servicos_b = _servicos(b)
    comuns = servicos_a & servicos_b

    if diff_dias <= JANELA_TOTAL_DIAS:
        if servicos_a == servicos_b:
            return "TOTAL"
        if comuns:
            return "PARCIAL_A"
    elif diff_dias <= JANELA_PARCIAL_B_DIAS:
        if servicos_a == servicos_b:
            return "PARCIAL_B"

    return "NENHUM"


class CasamentoService:

    def processar_casamentos(self, db: Session, nova_solicitacao: SolicitacaoModel) -> List[CasamentoModel]:
        """
        Chamado quando uma solicitação entra em AGUARDANDO_COTACAO.
        Compara com todas as outras no mesmo status e registra pares de casamento.
        """
        candidatas = db.query(SolicitacaoModel).filter(
            SolicitacaoModel.status == "AGUARDANDO_COTACAO",
            SolicitacaoModel.id != nova_solicitacao.id,
        ).all()

        casamentos_criados = []

        for candidata in candidatas:
            tipo = _calcular_match(nova_solicitacao, candidata)
            if tipo == "NENHUM":
                continue

            # Evita duplicata
            ja_existe = db.query(CasamentoModel).filter(
                (
                    (CasamentoModel.solicitacao_a_id == nova_solicitacao.id) &
                    (CasamentoModel.solicitacao_b_id == candidata.id)
                ) | (
                    (CasamentoModel.solicitacao_a_id == candidata.id) &
                    (CasamentoModel.solicitacao_b_id == nova_solicitacao.id)
                )
            ).first()

            if ja_existe:
                continue

            comuns = ",".join(sorted(_servicos(nova_solicitacao) & _servicos(candidata)))
            casamento = CasamentoModel(
                solicitacao_a_id=nova_solicitacao.id,
                solicitacao_b_id=candidata.id,
                tipo_match=tipo,
                destino=nova_solicitacao.destino_cidade,
                servicos_comuns=comuns,
            )
            db.add(casamento)
            casamentos_criados.append(casamento)
            logging.info(
                f"Casamento {tipo}: solicitações {nova_solicitacao.id} ↔ {candidata.id} "
                f"(destino: {nova_solicitacao.destino_cidade}, serviços: {comuns})"
            )

        if casamentos_criados:
            db.commit()

        return casamentos_criados

    def listar_casamentos_da_solicitacao(self, db: Session, solicitacao_id: int) -> List[dict]:
        """Retorna todos os pares de casamento envolvendo uma solicitação."""
        registros = db.query(CasamentoModel).filter(
            (CasamentoModel.solicitacao_a_id == solicitacao_id) |
            (CasamentoModel.solicitacao_b_id == solicitacao_id)
        ).all()

        resultado = []
        for r in registros:
            par_id = r.solicitacao_b_id if r.solicitacao_a_id == solicitacao_id else r.solicitacao_a_id
            resultado.append({
                "par_id": par_id,
                "tipo_match": r.tipo_match,
                "destino": r.destino,
                "servicos_comuns": r.servicos_comuns,
            })
        return resultado
