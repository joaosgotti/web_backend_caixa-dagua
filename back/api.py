# api.py
from fastapi import FastAPI, HTTPException, Depends, Path
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta, timezone as dt_timezone # Renomeado para dt_timezone
import pytz # Para conversão de fuso horário para exibição
from enum import Enum


# --- Módulos Locais ---
import config_api
from database_api import get_db_session
from models_api import Leitura
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc

# --- CONFIGURAÇÕES ---
MIN_NIVEL_VALUE = config_api.MIN_NIVEL
MAX_NIVEL_VALUE = config_api.MAX_NIVEL

# --- Enum para Unidade de Tempo ---
class TimeUnit(str, Enum):
    hours = "h"
    days = "d"

# --- Aplicação FastAPI ---
app = FastAPI(
    title="API de Leituras do Sensor de Distância (SQLAlchemy & Timezone)",
    description="API para acessar dados de distância do sensor, com tratamento de fuso horário.",
    version="1.2.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- Função Auxiliar para Calcular Nível ---
def calcular_nivel_percentual(distancia_original: float | int | None, min_val: int, max_val: int) -> int | None:
    if not isinstance(distancia_original, (int, float)): return None
    range_nivel = max_val - min_val
    if range_nivel == 0: return 0
    nivel_normalizado = 1 - ((distancia_original - min_val) / range_nivel)
    nivel_percentual = max(0.0, min(100.0, nivel_normalizado * 100.0))
    return round(nivel_percentual)

# --- Função Auxiliar para Processar Leitura ---
def processar_leitura_para_resposta(leitura_obj: Leitura, target_tz_str: str = 'America/Recife'):
    """
    Converte um objeto Leitura SQLAlchemy para um dict, ajusta timestamp para o fuso alvo e calcula nível.
    """
    if not leitura_obj:
        return None
    
    db_timestamp_aware = leitura_obj.created_on

    if db_timestamp_aware.tzinfo is None or db_timestamp_aware.tzinfo.utcoffset(db_timestamp_aware) is None:
        print(f"AVISO (ID: {leitura_obj.id}): Timestamp do DB (SQLAlchemy) veio como naive ou sem offset. Assumindo UTC e tornando aware.")
        db_timestamp_aware = db_timestamp_aware.replace(tzinfo=dt_timezone.utc)

    try:
        target_timezone = pytz.timezone(target_tz_str)
        display_timestamp = db_timestamp_aware.astimezone(target_timezone)
        created_on_iso_display = display_timestamp.isoformat()
    except pytz.exceptions.UnknownTimeZoneError:
        print(f"AVISO: Fuso horário '{target_tz_str}' desconhecido. Usando timestamp original (provavelmente UTC) para created_on.")
        created_on_iso_display = db_timestamp_aware.isoformat() 

    leitura_dict = {
        "id": leitura_obj.id,
        "distancia": leitura_obj.distancia,
        "created_on": created_on_iso_display, # Timestamp formatado para exibição
    }

    # Cálculo do Nível
    leitura_dict['nivel'] = calcular_nivel_percentual(
        leitura_obj.distancia, # Usa a distância diretamente do objeto
        config_api.MIN_NIVEL,
        config_api.MAX_NIVEL
    )
    return leitura_dict

# --- Endpoints da API com SQLAlchemy ---
@app.get("/leituras/ultima", summary="Obter a última leitura (SQLAlchemy & Timezone)")
def get_ultima_leitura_sqlalchemy(db: Session = Depends(get_db_session)):
    try:
        ultima_leitura_obj = db.query(Leitura).order_by(desc(Leitura.created_on)).first()

        if ultima_leitura_obj:
            return processar_leitura_para_resposta(ultima_leitura_obj)
        else:
            return {}
    except Exception as e:
        print(f"API Erro SQLAlchemy em /leituras/ultima: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor ao buscar última leitura")

@app.get("/leituras/{unit}/{value}", summary="Obter leituras por período flexível (horas ou dias)")
def get_leituras_por_periodo_flexivel(
    unit: TimeUnit, # Usa o Enum para validar a unidade (h ou d)
    value: int = Path(..., ge=1), # Path parameter, deve ser um inteiro >= 1
    db: Session = Depends(get_db_session)
):
    """
    Busca leituras de DISTÂNCIA dentro de um período especificado pela unidade (h para horas, d para dias)
    e um valor numérico. Retorna com o fuso horário de Recife.
    """
    delta = None
    if unit == TimeUnit.hours:
        delta = timedelta(hours=value)
    elif unit == TimeUnit.days:
        delta = timedelta(days=value)
    else:
        # Esta verificação é redundante se o Enum funcionar corretamente, mas por segurança
        raise HTTPException(status_code=400, detail="Unidade de tempo inválida. Use 'h' para horas ou 'd' para dias.")

    try:
        limite_tempo_utc = datetime.now(dt_timezone.utc) - delta

        leituras_objs = db.query(Leitura)\
                          .filter(Leitura.created_on >= limite_tempo_utc)\
                          .order_by(asc(Leitura.created_on))\
                          .all()
        
        leituras_processadas = [
            processar_leitura_para_resposta(leitura_obj) for leitura_obj in leituras_objs if leitura_obj
        ]
        
        return leituras_processadas
    except Exception as e:
        print(f"API Erro SQLAlchemy em /leituras/{unit.value}/{value}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor ao buscar histórico para {value} {unit.name}")

# --- Bloco para execução direta (teste) ---
if __name__ == "__main__":
    import uvicorn
    try:
        from database_api import engine as api_engine, Base as api_base
        print("Tentando criar tabelas da API (se não existirem)...")
        api_base.metadata.create_all(bind=api_engine)
        print("Tabelas da API verificadas/criadas.")
    except Exception as e_db_create:
        print(f"Erro ao tentar criar tabelas da API: {e_db_create}")

    print("Executando API (SQLAlchemy & Timezone) diretamente com Uvicorn (para teste)...")
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)