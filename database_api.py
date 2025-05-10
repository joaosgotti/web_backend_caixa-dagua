# database_api.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sys
import os
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

SQLALCHEMY_DATABASE_URL = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

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