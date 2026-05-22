from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Forçando o driver a usar codificação cliente UTF8, apontando para a porta 5433 e com a senha encodada
    DATABASE_URL: str = "postgresql://postgres:Magazine%40123@127.0.0.1:5433/solicitacao_viagens?client_encoding=utf8"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
