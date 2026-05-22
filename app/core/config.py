from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Banco de dados
    DATABASE_URL: str = "postgresql://postgres:Magazine%40123@127.0.0.1:5433/solicitacao_viagens?client_encoding=utf8"

    # SMTP — relay interno (sem autenticação)
    SMTP_HOST: str = "smtpml.magazineluiza.intranet"
    SMTP_PORT: int = 25
    SMTP_FROM: str = "viagenslabs@luizalabs.com"       # endereço sem caixa postal
    SMTP_FROM_NAME: str = "ViagensLabs | Luizalabs"
    SMTP_REPLY_TO: str = "rubia.paim@luizalabs.com"  # respostas redirecionadas aqui

    # URL pública do sistema (para links nos e-mails — painel setor, portal aprovação)
    BASE_URL: str = "http://viagenslabs.magazineluiza.intranet"

    # URL usada nos links enviados às AGÊNCIAS EXTERNAS (Tastur / Kontrip).
    # Pode ser diferente de BASE_URL: quando o sistema for exposto à internet ou VPN
    # disponível, basta trocar este valor no .env sem mexer no código.
    BASE_URL_AGENCIA: str = "http://viagenslabs.magazineluiza.intranet"

    # Duffel API — busca consultiva de voos (token via .env, nunca hardcoded)
    DUFFEL_TOKEN: str = ""
    DUFFEL_BASE_URL: str = "https://api.duffel.com"
    DUFFEL_VERSION: str = "v2"

    # Active Directory — grupos de acesso
    AD_BASE_DN: str = "DC=magazineluiza,DC=intranet"
    AD_GROUP_ADMINS:   str = "G_ACCESS_VIAGENSLABS_ADMINS"    # acesso ao Portal do Setor
    AD_GROUP_USERS:    str = "G_ACCESS_VIAGENSLABS_USERS"     # acesso ao Portal do Viajante
    AD_GROUP_AGENCIAS: str = "G_ACCESS_VIAGENSLABS_AGENCIAS"  # acesso futuro das agências (VPN + AD)

    # Setor de Viagens — endereço que recebe notificações de pré-aprovação
    SETOR_EMAIL: str = "viagenslabs@luizalabs.com"

    # Agências — endereços para envio de solicitações de cotação
    AGENCIA_TASTUR_EMAIL: str = ""
    AGENCIA_KONTRIP_EMAIL: str = ""

    # QA — quando definido, todos os e-mails de aprovação são redirecionados para este endereço.
    # Deixe vazio (ou remova) para desativar. Para remoção total: apagar esta linha + 3 linhas em _criar_token.
    QA_APROVADOR_EMAIL: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
