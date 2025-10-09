# api.py

# --- IBLIOTECAS E MÓDULOS ---

# Bibliotecas
import os
from datetime import datetime, timedelta, timezone as dt_timezone
from typing import List, Literal, Optional
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Path, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

# Módulos Locais do Projeto
from database_api import get_db_session
from models_api import Leitura as LeituraSQLAlchemy, LeituraResponse


# --- CONFIGURAÇÃO E INICIALIZAÇÃO DA APP ---

load_dotenv()

# Carrega constantes a partir das variáveis de ambiente
MIN_NIVEL = int(os.getenv("MIN_NIVEL"))
MAX_NIVEL = int(os.getenv("MAX_NIVEL"))

# Instância principal da aplicação FastAPI
app = FastAPI(
    title="API Caixa D'água",
    description="API para monitorar o nível da caixa d'água usando um sensor de distância.",
    version="1.3.0",
)

# Configuração do CORS para permitir acesso de qualquer origem
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuração do motor de templates Jinja2 para renderizar HTML
templates = Jinja2Templates(directory="templates")


def _calcular_nivel_percentual(distancia_original: float | int | None, min_val: int, max_val: int) -> int | None:
    """Calcula o nível percentual da água com base na distância medida."""
    if not isinstance(distancia_original, (int, float)):
        return None
    
    range_nivel = max_val - min_val
    if range_nivel == 0:
        return 0
    
    nivel_normalizado = 1 - ((distancia_original - min_val) / range_nivel)
    
    nivel_percentual = max(0.0, min(100.0, nivel_normalizado * 100.0))
    
    return round(nivel_percentual)

def _processar_leitura(leitura_obj: LeituraSQLAlchemy) -> Optional[LeituraResponse]:
    """Converte um objeto SQLAlchemy para o modelo Pydantic, calculando o nível."""
    if not leitura_obj:
        return None

    nivel_percentual = _calcular_nivel_percentual(leitura_obj.distancia, MIN_NIVEL, MAX_NIVEL)
    created_on_str = leitura_obj.created_on.isoformat() if leitura_obj.created_on else None

    return LeituraResponse(
        id=leitura_obj.id,
        distancia=leitura_obj.distancia,
        nivel=nivel_percentual,
        created_on=created_on_str
    )

@app.get("/favicon.ico", include_in_schema=False)
async def get_favicon():
    """Serve o arquivo de ícone para o navegador."""
    favicon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "favicon.ico")
    return FileResponse(favicon_path)

@app.get("/leituras/ultima_html", response_class=HTMLResponse, summary="Página web com a última leitura")
async def get_ultima_leitura_html(request: Request, db: Session = Depends(get_db_session)):
    """Busca a última leitura no banco de dados e a renderiza em uma página HTML."""
    try:
        ultima_leitura_obj = db.query(LeituraSQLAlchemy).order_by(desc(LeituraSQLAlchemy.created_on)).first()

        if not ultima_leitura_obj:
            contexto_erro = {"request": request, "mensagem": "Nenhuma leitura encontrada no banco de dados."}
            return templates.TemplateResponse("error.html", contexto_erro, status_code=404)
        
        leitura_processada = _processar_leitura(ultima_leitura_obj)
        
        contexto_jinja = {
            "request": request,
            "leitura": leitura_processada
        }
        
        return templates.TemplateResponse("ultima_leitura.html", context=contexto_jinja)

    except Exception as e:
        print(f"API Erro em /leituras/ultima_html: {e}")
        contexto_erro = {"request": request, "mensagem": "Ocorreu um erro interno no servidor."}
        return templates.TemplateResponse("error.html", contexto_erro, status_code=500)

@app.get("/leituras/{unit}/{value}", response_model=List[LeituraResponse], summary="Obter leituras por período")
def get_leituras_por_periodo(
    unit: Literal["h", "d"] = Path(..., title="Unidade de tempo", description="'h' para horas, 'd' para dias"),
    value: int = Path(..., ge=1, title="Valor do período", description="Deve ser um inteiro >= 1"),
    db: Session = Depends(get_db_session)
):
    """Busca um histórico de leituras com base em um período de tempo (horas ou dias)."""
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