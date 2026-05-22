from ldap3 import Server, Connection, SIMPLE, ALL, SUBTREE
from ldap3.core.exceptions import LDAPException
import logging

from app.core.config import settings


class ActiveDirectoryService:
    def __init__(self):
        self.servidores_ad = [
            "ldap://ML-ASC-AD-01.magazineluiza.intranet",
            "ldap://ML-ASC-AD2.magazineluiza.intranet",
            "ldap://ML-HB-AD01.magazineluiza.intranet"
        ]
        self.domain_prefix = "MAGAZINELUIZA"

    def autenticar_e_obter_perfil(self, username: str, password: str) -> dict:
        """
        Autentica via AD e verifica grupo de acesso para determinar o perfil.

        Retorna:
            { "autenticado": True,  "perfil": "setor" }    — membro de G_ACCESS_VIAGENSLABS_ADMINS
            { "autenticado": True,  "perfil": "agencia" }  — membro de G_ACCESS_VIAGENSLABS_AGENCIAS (futuro)
            { "autenticado": True,  "perfil": "viajante" } — membro de G_ACCESS_VIAGENSLABS_USERS ou usuário AD comum
            { "autenticado": False, "perfil": None }       — credenciais inválidas
        """
        if not username or not password:
            return {"autenticado": False, "perfil": None}

        if "\\" in username:
            username = username.split("\\")[1]

        user_dn = f"{self.domain_prefix}\\{username}"

        for server_uri in self.servidores_ad:
            try:
                server = Server(server_uri, get_info=ALL)
                conn = Connection(
                    server,
                    user=user_dn,
                    password=password,
                    authentication=SIMPLE,
                    raise_exceptions=True
                )
                conn.bind()

                # Após autenticar, consultar os grupos (memberOf) do usuário
                perfil = "viajante"
                try:
                    conn.search(
                        search_base=settings.AD_BASE_DN,
                        search_filter=f"(sAMAccountName={username})",
                        search_scope=SUBTREE,
                        attributes=["memberOf"]
                    )
                    if conn.entries:
                        raw_grupos = conn.entries[0].memberOf.values if conn.entries[0].memberOf else []
                        grupos = [str(g).upper() for g in raw_grupos]
                        if any(settings.AD_GROUP_ADMINS.upper() in g for g in grupos):
                            perfil = "setor"
                            logging.info(
                                f"[LDAP] '{username}' autenticado como SETOR "
                                f"(membro de {settings.AD_GROUP_ADMINS})"
                            )
                        elif any(settings.AD_GROUP_AGENCIAS.upper() in g for g in grupos):
                            # Perfil reservado — fluxo completo via VPN+AD implementado futuramente
                            perfil = "agencia_ad"
                            logging.info(
                                f"[LDAP] '{username}' identificado como AGÊNCIA via AD "
                                f"(membro de {settings.AD_GROUP_AGENCIAS})"
                            )
                except Exception as e_search:
                    # Falha na busca de grupos não bloqueia o login — usa perfil padrão
                    logging.warning(
                        f"[LDAP] Não foi possível verificar grupos de '{username}': {e_search}. "
                        "Perfil padrão: viajante."
                    )

                conn.unbind()
                return {"autenticado": True, "perfil": perfil}

            except LDAPException as e:
                logging.warning(f"[LDAP] Servidor {server_uri} recusou as credenciais: {e}")
                return {"autenticado": False, "perfil": None}

            except Exception as e:
                logging.warning(f"[LDAP] Falha de comunicação com {server_uri}: {e}")
                continue

        logging.error("[LDAP] Falha geral: nenhum servidor AD disponível.")
        return {"autenticado": False, "perfil": None}

    # -------------------------------------------------------------------------
    # Compat. retroativa (mantido para não quebrar chamadas antigas)
    # -------------------------------------------------------------------------
    def autenticar_usuario(self, username: str, password: str) -> bool:
        return self.autenticar_e_obter_perfil(username, password)["autenticado"]
