# database_api.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sys
import config_api

SQLALCHEMY_DATABASE_URL = config_api.DATABASE_URL

# echo=True é útil para debug, loga as queries SQL. Remova em produção.
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Função para obter uma sessão do banco de dados (usada como dependência no FastAPI)
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Tente conectar para verificar se o engine foi criado corretamente (opcional, falha cedo)
try:
    with engine.connect() as connection:
        print("[DatabaseAPI] Conexão com o SQLAlchemy Engine (API) bem-sucedida.")
except Exception as e:
    print(f"[DatabaseAPI] ERRO CRÍTICO ao criar SQLAlchemy Engine (API) ou conectar: {e}")
    sys.exit(1)