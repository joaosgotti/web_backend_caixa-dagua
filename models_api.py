# models_api.py
from sqlalchemy import Column, Integer, Float, DateTime
from datetime import datetime, timezone
from database_api import Base 

class Leitura(Base):
    __tablename__ = "leituras" 

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    distancia = Column(Float, nullable=False)
    created_on = Column(DateTime(timezone=True), nullable=False)

    def __repr__(self):
        return f"<Leitura(id={self.id}, distancia={self.distancia}, created_on='{self.created_on}')>"

