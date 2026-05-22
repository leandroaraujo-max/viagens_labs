from app.infrastructure.database import SessionLocal

def get_db_session():
    """Cria e fornece uma sess?o do banco de dados por requisi??o."""
    db = None
    try:
        db = SessionLocal()
        yield db
    finally:
        if db:
            db.close()
