from google.cloud import bigquery
import logging
from typing import Optional, Dict
import re

class BigQueryService:
    TABLE_CAD_FUNCIONARIO = "maga-bigdata.balboa.cad_funcionario"

    def __init__(self, project_id: str, table_assignee: str, table_funcionarios: str):
        self.project_id = project_id
        self.table_assignee = table_assignee
        self.table_funcionarios = table_funcionarios

        try:
            self.client = bigquery.Client(project=project_id)
            logging.info(f"BigQueryService inicializado no projeto {project_id}.")
        except Exception as e:
            logging.error(f"Falha ao conectar no BigQuery: {e}")
            self.client = None

    def buscar_colaborador(self, cpf_ou_matricula: str) -> Optional[Dict]:
        """
        Consulta os dados do colaborador fazendo o JOIN entre assignee e funcionarios.
        Trata CPFs com zeros suprimidos.
        """
        if not self.client:
            raise RuntimeError("Cliente BQ nao ativo. Configure o gcloud ADC.")

        chave_limpa = str(cpf_ou_matricula).strip()

        if chave_limpa.isdigit():
            chave_numerica = re.sub(r"\D", "", chave_limpa)
            if len(chave_numerica) == 11:
                cpf_sem_zero = chave_numerica.lstrip("0")
                filtro = f"(t1.custom2 = '{chave_numerica}' OR t1.custom2 = '{cpf_sem_zero}' OR LPAD(t1.custom2,11,'0') = '{chave_numerica}')"
            else:
                filtro = f"t1.CUSTOM1 = '{chave_numerica}'"
        else:
            chave_lower = chave_limpa.lower()
            filtro = (
                f"(LOWER(t1.user_name) = '{chave_lower}' "
                f"OR LOWER(t1.user_name) = '{chave_lower}@magazineluiza.com.br' "
                f"OR LOWER(SPLIT(t1.user_name, '@')[SAFE_OFFSET(0)]) = '{chave_lower}')"
            )

        query = f"""
            SELECT DISTINCT
              CAST(t2.ID AS STRING)                          AS matricula,
              t1.custom2                                     AS cpf,
              t2.NOME                                        AS nome,
              t2.CARGO                                       AS cargo,
              t2.FILIAL                                      AS filial,
              t2.CENTRO_CUSTO                                AS centro_custo,
              t2.COD_CENTRO_CUSTO                            AS cod_centro_custo,
              t2.DATA_ADMISSAO                               AS data_admissao,
              t2.SITUACAO                                    AS situacao,
              t1.email                                       AS email,
              t1.user_name                                   AS user_name,
              CONCAT(g1.first_name, ' ', g1.last_name)       AS aprovador_n1_nome,
              g1.email                                       AS aprovador_n1_email,
              CONCAT(g2.first_name, ' ', g2.last_name)       AS aprovador_n2_nome,
              g2.email                                       AS aprovador_n2_email,
              -- cad_funcionario: telefone e dados complementares
              cf.FONERES                                     AS foneres,
              cf.CODCHAPA                                    AS codchapa,
              cf.CODFUNCAO                                   AS codfuncao,
              cf.CODFIL                                      AS codfil
            FROM `{self.table_assignee}` AS t1
            INNER JOIN `{self.table_funcionarios}` AS t2
              ON t1.CUSTOM1 = CAST(t2.ID AS STRING)
            LEFT JOIN `{self.TABLE_CAD_FUNCIONARIO}` AS cf
              ON LPAD(CAST(cf.CGCCPF AS STRING), 11, '0') = LPAD(t1.custom2, 11, '0')
              AND cf.FLATIVO = 'S'
            LEFT JOIN `{self.table_assignee}` AS g1
              ON t1.superior = g1.id AND g1.active = TRUE
            LEFT JOIN `{self.table_assignee}` AS g2
              ON g1.superior = g2.id AND g2.active = TRUE
            WHERE {filtro}
              AND t2.SITUACAO NOT IN ('Desligado', 'Demitido', 'Afastado', 'Aposentado', 'Inativo')
              AND t1.active = TRUE
            LIMIT 1
        """

        try:
            query_job = self.client.query(query)
            resultados = list(query_job.result())

            if resultados:
                linha = resultados[0]

                def _fmt_date(val) -> str:
                    """Converte date/datetime do BQ para DD/MM/YYYY."""
                    if val is None:
                        return ''
                    if hasattr(val, 'strftime'):
                        return val.strftime('%d/%m/%Y')
                    return str(val)

                return {
                    "matricula":          getattr(linha, "matricula",          ""),
                    "cpf":                getattr(linha, "cpf",                ""),
                    "nome":               getattr(linha, "nome",               ""),
                    "cargo":              getattr(linha, "cargo",              ""),
                    "filial":             str(getattr(linha, "filial",         "") or ""),
                    "centro_custo":       getattr(linha, "centro_custo",       ""),
                    "cod_centro_custo":   str(getattr(linha, "cod_centro_custo", "") or ""),
                    "data_admissao":      _fmt_date(getattr(linha, "data_admissao",   None)),
                    "situacao":           getattr(linha, "situacao",           ""),
                    "email":              getattr(linha, "email",              ""),
                    "user_name":          getattr(linha, "user_name",          ""),
                    "aprovador_n1_nome":  getattr(linha, "aprovador_n1_nome",  "N\u00e3o Definido"),
                    "aprovador_n1_email": getattr(linha, "aprovador_n1_email", ""),
                    "aprovador_n2_nome":  getattr(linha, "aprovador_n2_nome",  ""),
                    "aprovador_n2_email": getattr(linha, "aprovador_n2_email", ""),
                    # cad_funcionario
                    "foneres":            str(getattr(linha, "foneres",   "") or ""),
                    "codchapa":           str(getattr(linha, "codchapa",  "") or ""),
                    "codfuncao":          str(getattr(linha, "codfuncao", "") or ""),
                    "codfil":             str(getattr(linha, "codfil",    "") or ""),
                }

            return None

        except Exception as e:
            logging.error(f"Falha na consulta BQ: {e}")
            raise e

    def buscar_situacao_por_email(self, email: str) -> Optional[str]:
        """
        Retorna a coluna SITUACAO de mag_v_funcionarios_ativos para o e-mail informado.
        Usado para verificar se o aprovador N1 esta de Ferias antes de iniciar o fluxo.
        Retorna None se o colaborador nao for encontrado ou se o BQ estiver indisponivel.
        """
        if not self.client or not email:
            return None

        email_safe = email.strip().lower().replace("'", "").replace("\\", "")

        query = f"""
            SELECT t2.SITUACAO AS situacao
            FROM `{self.table_assignee}` AS t1
            INNER JOIN `{self.table_funcionarios}` AS t2
              ON t1.CUSTOM1 = CAST(t2.ID AS STRING)
            WHERE LOWER(t1.email) = '{email_safe}'
              AND t1.active = TRUE
            LIMIT 1
        """

        try:
            resultado = list(self.client.query(query).result())
            if resultado:
                return getattr(resultado[0], "situacao", None)
            return None
        except Exception as e:
            logging.error(f"Falha ao buscar situacao para {email}: {e}")
            return None