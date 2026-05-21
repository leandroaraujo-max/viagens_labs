from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Cria a engine de conexão com o banco de dados usando a URL do arquivo de config
engine = create_engine(settings.DATABASE_URL)

# Cria uma fábrica de sessões (SessionLocal) que será usada para criar sessões com o banco
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para os modelos ORM (nossas futuras tabelas)
Base = declarative_base()
