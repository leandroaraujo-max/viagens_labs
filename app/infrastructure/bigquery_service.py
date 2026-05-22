from google.cloud import bigquery
import logging
from typing import Optional, Dict
import re

class BigQueryService:
    def __init__(self, project_id: str, table_assignee: str, table_funcionarios: str):
        self.project_id = project_id
        self.table_assignee = table_assignee
        self.table_funcionarios = table_funcionarios
        
        try:
            # Inicializa usando ADC (Application Default Credentials) que voc? configurou no gcloud
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
            raise RuntimeError("Cliente BQ n?o ativo. Configure o gcloud ADC.")

        # Limpa formata??o mantendo apenas n?meros ou o nome de usu?rio (ex: lnd_araujo)
        chave_limpa = str(cpf_ou_matricula).strip()
        
        # L?gica de filtro id?ntica ao GAS (aceita CPF ou Matr?cula/Username)
        if chave_limpa.isdigit():
            # Se s? tem n?meros, trata como CPF ou Matr?cula
            chave_numerica = re.sub(r"\D", "", chave_limpa)
            if len(chave_numerica) == 11:
                cpf_sem_zero = chave_numerica.lstrip("0")
                filtro = f"(t1.custom2 = '{chave_numerica}' OR t1.custom2 = '{cpf_sem_zero}' OR LPAD(t1.custom2,11,'0') = '{chave_numerica}')"
            else:
                # ? matr?cula num?rica
                filtro = f"t1.CUSTOM1 = '{chave_numerica}'"
        else:
            # ? username de rede (ex: lnd_araujo)
            filtro = f"t1.user_name = '{chave_limpa}'"

        # A sua Query Real de Produ??o, mantendo a busca da cadeia de aprova??o (N1/N2)
        query = f"""
            SELECT DISTINCT
              CAST(t2.ID AS STRING)                          AS matricula,
              t1.custom2                                     AS cpf,
              t2.NOME                                        AS nome,
              t2.CARGO                                       AS cargo,
              t2.FILIAL                                      AS filial,
              t2.CENTRO_CUSTO                                AS centro_custo,
              t2.SITUACAO                                    AS situacao,
              t1.email                                       AS email,
              t1.user_name                                   AS user_name,
              CONCAT(g1.first_name, ' ', g1.last_name)       AS aprovador_n1_nome,
              g1.email                                       AS aprovador_n1_email
            FROM `{self.table_assignee}` AS t1
            INNER JOIN `{self.table_funcionarios}` AS t2
              ON t1.CUSTOM1 = CAST(t2.ID AS STRING)
            LEFT JOIN `{self.table_assignee}` AS g1
              ON t1.superior = g1.id AND g1.active = TRUE
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
                # Converte o Row do BQ para Dicion?rio de forma segura
                return {
                    "matricula": getattr(linha, "matricula", ""),
                    "cpf": getattr(linha, "cpf", ""),
                    "nome": getattr(linha, "nome", ""),
                    "cargo": getattr(linha, "cargo", ""),
                    "filial": getattr(linha, "filial", ""),
                    "centro_custo": getattr(linha, "centro_custo", ""),
                    "situacao": getattr(linha, "situacao", ""),
                    "email": getattr(linha, "email", ""),
                    "user_name": getattr(linha, "user_name", ""),
                    "aprovador_n1_nome": getattr(linha, "aprovador_n1_nome", "N?o Definido"),
                    "aprovador_n1_email": getattr(linha, "aprovador_n1_email", "")
                }
                
            return None 
            
        except Exception as e:
            logging.error(f"Falha na consulta BQ: {e}")
            raise e
