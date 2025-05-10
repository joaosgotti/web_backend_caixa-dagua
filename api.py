# api.py
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Path
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta, timezone as dt_timezone # Renomeado para dt_timezone
import pytz # Para conversão de fuso horário para exibição
from enum import Enum
from typing import List, Literal, Optional

from models_api import Leitura as LeituraSQLAlchemy, LeituraResponse

# --- Módulos Locais ---
import config_api
from database_api import get_db_session

from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
import os

# --- CONFIGURAÇÕES ---
load_dotenv()
MIN_NIVEL = int(os.getenv("MIN_NIVEL"))
MAX_NIVEL = int(os.getenv("MAX_NIVEL"))

# --- Aplicação FastAPI ---
app = FastAPI(
    title="API de Leituras do Sensor de Distância (SQLAlchemy & Timezone)",
    description="API para acessar dados de distância do sensor, com tratamento de fuso horário.",
    version="1.2.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- Função Auxiliar para Calcular Nível ---
def _calcular_nivel_percentual(distancia_original: float | int | None, min_val: int, max_val: int) -> int | None:
    if not isinstance(distancia_original, (int, float)): return None
    range_nivel = max_val - min_val
    if range_nivel == 0: return 0
    nivel_normalizado = 1 - ((distancia_original - min_val) / range_nivel)
    nivel_percentual = max(0.0, min(100.0, nivel_normalizado * 100.0))
    return round(nivel_percentual)

# --- Função Auxiliar para Processar Leitura ---
def _converter_leitura_para_resposta(leitura_obj: LeituraSQLAlchemy) -> Optional[LeituraResponse]:
    """
    Converte um objeto Leitura SQLAlchemy para um dict, formata o timestamp UTC para ISO, e calcula o nível.
    """
    if not leitura_obj:
        return None

    leitura_dict = {
        "id": leitura_obj.id,
        "distancia": leitura_obj.distancia,
        "created_on": leitura_obj.created_on.isoformat(), # Timestamp formatado
    }

    leitura_dict['nivel'] = _calcular_nivel_percentual(leitura_obj.distancia,MIN_NIVEL,MAX_NIVEL)
    
    return leitura_dict

# --- Endpoints da API com SQLAlchemy ---    
@app.get("/leituras/ultima", 
         response_model=Optional[LeituraResponse], # Permite resposta nula se não encontrado
         summary="Obter a última leitura")
def get_ultima_leitura(db: Session = Depends(get_db_session)):
    try:
        ultima_leitura_obj = db.query(LeituraSQLAlchemy).order_by(desc(LeituraSQLAlchemy.created_on)).first()

        if not ultima_leitura_obj:
            raise HTTPException(status_code=404, detail="Nenhuma leitura encontrada")
        
        return _converter_leitura_para_resposta(ultima_leitura_obj)
    except HTTPException: # Re-raise HTTPExceptions para não mascará-las
        raise
    except Exception as e:
        print(f"API Erro em /leituras/ultima: {e}") # Logar o erro 'e' melhor em produção
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

@app.get("/leituras/{unit}/{value}",
         response_model=List[LeituraResponse],
         summary="Obter leituras por período (horas ou dias, timestamps em UTC)")
def get_leituras_por_periodo(
    unit: Literal["h", "d"] = Path(..., title="Unidade de tempo", description="'h' para horas, 'd' para dias"),
    value: int = Path(..., ge=1, title="Valor do período", description="Deve ser um inteiro >= 1"),
    db: Session = Depends(get_db_session)
):
    delta = timedelta(hours=value) if unit == "h" else timedelta(days=value)
    
    try:
        limite_tempo_utc = datetime.now(dt_timezone.utc) - delta

        leituras_objs = db.query(LeituraSQLAlchemy)\
                          .filter(LeituraSQLAlchemy.created_on >= limite_tempo_utc)\
                          .order_by(asc(LeituraSQLAlchemy.created_on))\
                          .all()
        
        return [_converter_leitura_para_resposta(leitura) for leitura in leituras_objs]
    except Exception:
        # Em produção, logue o erro 'e' com exc_info=True
        raise HTTPException(status_code=500, detail="Erro interno do servidor ao buscar histórico")