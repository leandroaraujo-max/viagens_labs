from ldap3 import Server, Connection, SIMPLE, ALL
from ldap3.core.exceptions import LDAPException
import logging

class ActiveDirectoryService:
    def __init__(self):
        self.servidores_ad = [
            "ldap://ML-ASC-AD-01.magazineluiza.intranet",
            "ldap://ML-ASC-AD2.magazineluiza.intranet",
            "ldap://ML-HB-AD01.magazineluiza.intranet"
        ]
        self.domain_prefix = "MAGAZINELUIZA"

    def autenticar_usuario(self, username: str, password: str) -> bool:
        """
        Tenta fazer um Simple Bind no AD usando o formato de maior compatibilidade do Windows:
        DOMINIO\\usuario
        """
        if not username or not password:
            return False

        if "\\" in username:
            username = username.split("\\")[1]
            
        user_dn = f"{self.domain_prefix}\\{username}"
        
        for server_uri in self.servidores_ad:
            try:
                logging.info(f"[LDAP] Tentando autentica??o via servidor {server_uri}...")
                server = Server(server_uri, get_info=ALL)
                
                conn = Connection(
                    server,
                    user=user_dn,
                    password=password,
                    authentication=SIMPLE,
                    raise_exceptions=True
                )
                
                conn.bind()
                
                logging.info(f"[LDAP] SUCESSO: Usu?rio '{user_dn}' validado com sucesso!")
                conn.unbind()
                return True
                
            except LDAPException as e:
                logging.warning(f"[LDAP] Servidor {server_uri} recusou as credenciais: {e}")
                return False
                
            except Exception as e:
                logging.warning(f"[LDAP] Falha de comunica??o com {server_uri}: {e}")
                continue
                
        logging.error("[LDAP] Falha geral: Nenhum dos servidores de AD p?de validar o login.")
        return False
