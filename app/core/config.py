from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # String de conexão com o banco de dados PostgreSQL
    # O Pydantic irá ler essa variável de um arquivo .env ou do ambiente do sistema
    DATABASE_URL: str = "postgresql://postgres:sua_senha_aqui@localhost:5432/solicitacao_viagens"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
