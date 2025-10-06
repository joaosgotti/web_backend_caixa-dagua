# models_api.py
from typing import Optional, Union
from sqlalchemy import Column, Integer, Float, DateTime
from database_api import Base 
from pydantic import BaseModel

class Leitura(Base): # Modelo SQLAlchemy
    __tablename__ = "leituras" 

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    distancia = Column(Float, nullable=False)
    created_on = Column(DateTime(timezone=True), nullable=False)
    #nivel = Column(Float, nullable=False) # No banco, é Float e não nulo

    def __repr__(self):
        return f"<Leitura(id={self.id}, distancia={self.distancia}, created_on='{self.created_on}', nivel={self.nivel})>"

class LeituraResponse(BaseModel):
    id: int
    distancia: float 
    created_on: str  
    #nivel: Optional[Union[int, float]]