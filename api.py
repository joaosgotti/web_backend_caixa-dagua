# api.py

# --- Bibliotecas Padrão Python ---
import os
from datetime import datetime, timedelta, timezone as dt_timezone
from typing import List, Literal, Optional

# --- Bibliotecas de Terceiros ---
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Path, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

# --- Módulos Locais do Projeto ---
from database_api import get_db_session
from models_api import Leitura as LeituraSQLAlchemy, LeituraResponse

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
templates=Jinja2Templates(directory="templates")

# --- Função Auxiliar para Calcular Nível ---
def _calcular_nivel_percentual(distancia_original: float | int | None, min_val: int, max_val: int) -> int | None:
    if not isinstance(distancia_original, (int, float)): 
        return None
    
    range_nivel = max_val - min_val
    
    if range_nivel == 0: 
        return 0
    
    nivel_normalizado = 1 - ((distancia_original - min_val) / range_nivel)
    
    nivel_percentual = max(0.0, min(100.0, nivel_normalizado * 100.0))
    
    return round(nivel_percentual)

# --- Função Auxiliar para Processar Leitura ---
def _processar_leitura(leitura_obj: LeituraSQLAlchemy) -> Optional[LeituraResponse]:
    """
    Converte um objeto Leitura SQLAlchemy para o modelo Pydantic LeituraResponse,
    calculando o nível e formatando a data.
    """
    if not leitura_obj:
        return None

    nivel_percentual = _calcular_nivel_percentual(leitura_obj.distancia, MIN_NIVEL, MAX_NIVEL)

    # Retorna um objeto Pydantic, não mais um TemplateResponse
    return LeituraResponse(
        id=leitura_obj.id,
        distancia=leitura_obj.distancia,
        nivel=nivel_percentual,
        created_on=leitura_obj.created_on 
    )

    leitura_dict['nivel'] = _calcular_nivel_percentual(leitura_obj.distancia,MIN_NIVEL,MAX_NIVEL)
    
    leituras_html = templates.TemplateResponse(
        name = "ultima_leitura.html",
        context = leitura_dict
    )

    return leituras_html

@app.get("/leituras/ultima_html",
         response_class=HTMLResponse,
         summary="Mostrar a última leitura em uma página web (HTML)")
async def get_ultima_leitura_html(request: Request, db: Session = Depends(get_db_session)):
    try:
        ultima_leitura_obj = db.query(LeituraSQLAlchemy).order_by(desc(LeituraSQLAlchemy.created_on)).first()

        if not ultima_leitura_obj:
            # Se não houver dados, retorna um HTML de erro 404
            contexto_erro = {"request": request, "mensagem": "Nenhuma leitura encontrada no banco de dados."}
            return templates.TemplateResponse("error.html", contexto_erro, status_code=404)
        
        leitura_processada = _processar_leitura(ultima_leitura_obj)
        
        contexto_jinja = {
            "request": request, 
            "leitura": leitura_processada 
        }
        
        return templates.TemplateResponse(
            name="ultima_leitura.html",
            context=contexto_jinja
        )

    except Exception as e:
        print(f"API Erro em /leituras/ultima_html: {e}") 
        contexto_erro = {"request": request, "mensagem": f"Ocorreu um erro interno no servidor: {e}"}
        return templates.TemplateResponse("error.html", contexto_erro, status_code=500)

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
        
        return [_processar_leitura(leitura) for leitura in leituras_objs]
    except Exception:
        raise HTTPException(status_code=500, detail="Erro interno do servidor ao buscar histórico")