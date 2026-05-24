import sys
import ssl
import logging
from ldap3 import Server, Connection, SIMPLE, ALL, SUBTREE, Tls
from ldap3.core.exceptions import LDAPException

# Configuração de logs para exibição em tempo real
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

def testar_conexao_ldaps(
    servidor_uri: str,
    username: str,
    password: str,
    domain_prefix: str = "MAGAZINELUIZA",
    ad_base_dn: str = "DC=magazineluiza,DC=intranet",
    validar_cert: bool = True
):
    """
    Testa a conexão e autenticação no Active Directory via LDAPS (LDAP seguro).
    """
    logging.info("=" * 60)
    logging.info(f"INICIANDO TESTE DE LDAPS EM: {servidor_uri}")
    logging.info(f"Usuário: {username}")
    logging.info(f"Prefixo do Domínio: {domain_prefix}")
    logging.info(f"Validação de Certificado SSL/TLS: {'Ativa' if validar_cert else 'Ignorada (CERT_NONE)'}")
    logging.info("=" * 60)

    # 1. Ajustando a URI do servidor para garantir o prefixo correto
    if not servidor_uri.startswith("ldaps://"):
        logging.warning("URI não inicia com ldaps://. Corrigindo automaticamente...")
        if servidor_uri.startswith("ldap://"):
            servidor_uri = servidor_uri.replace("ldap://", "ldaps://")
        else:
            servidor_uri = f"ldaps://{servidor_uri}"
    
    # Adiciona a porta 636 se não houver porta explícita
    if ":" not in servidor_uri.split("ldaps://")[1]:
        servidor_uri = f"{servidor_uri}:636"

    logging.info(f"URI Final para Conexão: {servidor_uri}")

    # 2. Configurando SSL/TLS
    try:
        if validar_cert:
            # Conexão padrão usando as CAs de confiança do Sistema Operacional
            tls_config = Tls(validate=ssl.CERT_REQUIRED, version=ssl.PROTOCOL_TLSv1_2)
            logging.info("✓ TLS configurado (Validação exigida - CERT_REQUIRED)")
        else:
            # Ignora a verificação de certificados autoassinados ou de CAs não cadastradas
            tls_config = Tls(validate=ssl.CERT_NONE, version=ssl.PROTOCOL_TLSv1_2)
            logging.info("⚠ TLS configurado (Validação desabilitada - CERT_NONE)")
    except Exception as e_tls:
        logging.error(f"✗ Falha ao configurar contexto SSL/TLS: {e_tls}")
        return False

    # 3. Criando o objeto Server
    try:
        server = Server(servidor_uri, use_ssl=True, tls=tls_config, get_info=ALL)
        logging.info("✓ Objeto Server instanciado com sucesso.")
    except Exception as e_server:
        logging.error(f"✗ Falha ao instanciar objeto Server: {e_server}")
        return False

    # 4. Preparando as credenciais de login
    user_dn = f"{domain_prefix}\\{username}"
    logging.info(f"DN de Autenticação: {user_dn}")

    # 5. Tentando realizar o Bind de Conexão
    conn = None
    try:
        logging.info("Tentando conectar e realizar bind...")
        conn = Connection(
            server,
            user=user_dn,
            password=password,
            authentication=SIMPLE,
            raise_exceptions=True
        )
        conn.bind()
        logging.info("✓✓✓ AUTENTICAÇÃO REALIZADA COM SUCESSO VIA LDAPS! ✓✓✓")
        
        # 6. Teste de Busca (Search) para validar leitura após conexão
        logging.info(f"Testando consulta na Base DN: {ad_base_dn}...")
        conn.search(
            search_base=ad_base_dn,
            search_filter=f"(sAMAccountName={username})",
            search_scope=SUBTREE,
            attributes=["memberOf", "displayName", "mail"]
        )
        
        if conn.entries:
            entry = conn.entries[0]
            logging.info(f"✓ Consulta bem-sucedida! Usuário localizado:")
            logging.info(f"  - Nome Exibido: {entry.displayName}")
            logging.info(f"  - E-mail: {entry.mail}")
            grupos = entry.memberOf.values if entry.memberOf else []
            logging.info(f"  - Quantidade de Grupos: {len(grupos)}")
            for g in grupos[:3]:
                logging.info(f"    - {g}")
            if len(grupos) > 3:
                logging.info(f"    - ... e outros {len(grupos) - 3} grupos.")
        else:
            logging.warning(f"⚠ Conectado, mas o sAMAccountName '{username}' não foi localizado na base dn '{ad_base_dn}'.")
            
        conn.unbind()
        logging.info("Conexão encerrada de forma limpa.")
        return True

    except LDAPException as e_ldap:
        logging.error(f"✗ Erro de LDAP/Autenticação: {e_ldap}")
        if conn:
            try:
                conn.unbind()
            except:
                pass
        return False
    except Exception as e_gen:
        logging.error(f"✗ Falha geral ou de rede (Timeout/Porta 636 bloqueada): {e_gen}")
        if conn:
            try:
                conn.unbind()
            except:
                pass
        return False

if __name__ == "__main__":
    # Parametros para o teste manual (substitua com dados reais para o teste apartado)
    AD_SERVER = "ldaps://ML-ASC-AD-01.magazineluiza.intranet:636"
    USER_TEST = "lnd_araujo"
    PASS_TEST = "@Yanbento3232@"
    
    # Executa o teste de forma apartada
    if USER_TEST == "seu.usuario":
        print("\n" + "!" * 80)
        print("POR FAVOR, EDITE ESTE SCRIPT PARA INSERIR SUAS CREDENCIAIS REAIS DO AD!")
        print("Local do arquivo: <conversation_id>/scratch/test_ldaps_auth.py")
        print("!" * 80 + "\n")
    else:
        testar_conexao_ldaps(
            servidor_uri="ldaps://ML-ASC-AD-01.magazineluiza.intranet:636",
            username="lnd_araujo",
            password="@Yanbento3232@",
            validar_cert=True  # Altere para True se o seu AD tiver um certificado assinado por CA confiável
        )
