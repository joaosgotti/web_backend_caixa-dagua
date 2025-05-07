# api.py

# --- Importação de Bibliotecas ---
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
import pytz

# --- Carregamento de Variáveis de Ambiente (Apenas para DB) ---
load_dotenv() # Ainda necessário para as variáveis do banco de dados

# --- CONFIGURAÇÕES FIXAS DE NÍVEL ---
MIN_NIVEL_VALUE = int(os.getenv("MIN_NIVEL"))
MAX_NIVEL_VALUE = int(os.getenv("MAX_NIVEL"))

# Validação simples para garantir que max > min ao iniciar
if MAX_NIVEL_VALUE <= MIN_NIVEL_VALUE:
    print(f"--- ERRO DE CONFIGURAÇÃO FIXA: MAX_NIVEL ({MAX_NIVEL_VALUE}) deve ser maior que MIN_NIVEL ({MIN_NIVEL_VALUE}) ---")
    # Em um caso real, você poderia querer parar a aplicação aqui:
    # import sys
    # sys.exit(1)

# --- Configuração da Aplicação FastAPI ---
app = FastAPI(
    title="API de Leituras do Sensor de Distância",
    description="API para acessar dados de distância do sensor salvos no banco de dados.",
    version="1.0.0",
)

# --- Configuração do Middleware CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Em produção, use domínios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Função de Conexão com o Banco de Dados ---
def connect_db():
    """
    Estabelece uma conexão com o banco de dados PostgreSQL usando credenciais de variáveis de ambiente.
    """
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT", "5432")
    required_vars = {'DB_NAME': db_name,'DB_USER': db_user,'DB_PASSWORD': db_password,'DB_HOST': db_host}
    missing_vars = [k for k, v in required_vars.items() if not v]
    if missing_vars:
        print(f"API Erro Crítico: Variáveis de ambiente do banco de dados ausentes: {', '.join(missing_vars)}")
        return None
    try:
        connection = psycopg2.connect(dbname=db_name,user=db_user,password=db_password,host=db_host,port=db_port,connect_timeout=5)
        return connection
    except psycopg2.OperationalError as e: print(f"API Erro OPERACIONAL ao conectar ao banco de dados: {e}"); return None
    except psycopg2.Error as e: print(f"API Erro psycopg2 ao conectar ao banco de dados: {e}"); return None
    except Exception as e: print(f"API Erro INESPERADO durante a conexão com o banco de dados: {e}"); return None

# --- Função Auxiliar para Calcular Nível ---
def calcular_nivel_percentual(distancia_original: float | int | None, min_val: int, max_val: int) -> int | None:
    """
    Calcula o nível como porcentagem com base na distância e nos valores min/max.
    Retorna um inteiro (0-100) ou None se a distância não for válida.
    """
    if not isinstance(distancia_original, (int, float)):
        return None

    # Calcula o tamanho total do intervalo válido
    range_nivel = max_val - min_val

    # Verifica se o intervalo é válido (evita divisão por zero)
    if range_nivel == 0:
        # print("API Aviso: MIN_NIVEL_VALUE e MAX_NIVEL_VALUE são iguais. Nível definido como 0%.") # Evitar spam no log se chamado em loop
        return 0 # Nível é 0 se o range for 0

    # Calcula onde a distância atual se encontra dentro do intervalo (valor entre 0 e 1 geralmente)
    # Lembre-se: menor distância = maior nível (reservatório mais cheio)
    nivel_normalizado = 1 - ((distancia_original - min_val) / range_nivel)
    # Converte para porcentagem e garante que fique entre 0 e 100
    nivel_percentual = max(0.0, min(100.0, nivel_normalizado * 100.0))

    return round(nivel_percentual)

# --- Endpoints da API ---

@app.get("/leituras/ultima", summary="Obter a última leitura (distância e nível calculado)")
def get_ultima_leitura():
    """
    Busca a leitura de distância mais recente, calcula o 'nivel' (como porcentagem)
    usando os valores fixos MIN_NIVEL_VALUE e MAX_NIVEL_VALUE, e retorna com fuso de Recife.
    """
    conn = None
    try:
        conn = connect_db()
        if not conn:
            raise HTTPException(status_code=503, detail="Serviço indisponível: Falha na conexão com o banco de dados")

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, distancia, created_on FROM leituras ORDER BY created_on DESC LIMIT 1;")
            result = cur.fetchone()

        if result:
            # 1. Processa o Timestamp
            original_datetime = result['created_on']
            if original_datetime.tzinfo is None:
                print(f"AVISO (ID: {result['id']}): Timestamp do DB veio como naive. Assumindo UTC.")
                original_datetime = original_datetime.replace(tzinfo=timezone.utc)
            local_timezone = pytz.timezone('America/Recife')
            local_datetime = original_datetime.astimezone(local_timezone)
            result['created_on'] = local_datetime.isoformat()

            # 2. Calcula e Adiciona o Nível
            distancia_original = result.get('distancia')
            result['nivel'] = calcular_nivel_percentual(distancia_original, MIN_NIVEL_VALUE, MAX_NIVEL_VALUE)

            # 3. Retorna o dicionário completo
            return result
        else:
            # Se nenhuma leitura for encontrada
            return {}

    except HTTPException as http_exc:
        raise http_exc
    except (Exception, psycopg2.Error) as e:
        print(f"API Erro em /leituras/ultima: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor ao buscar última leitura")
    finally:
        if conn:
            try:
                conn.close()
            except psycopg2.Error as close_err:
                print(f"API Erro ao fechar conexão DB em /leituras/ultima: {close_err}")

@app.get("/leituras", summary="Obter leituras de distância e nível em um período")
def get_leituras_por_periodo(
    periodo_horas: int = 24
):
    """
    Busca leituras de DISTÂNCIA dentro de um período, calcula o 'nivel' para cada uma,
    e as retorna com o fuso horário de Recife.
    """
    conn = None
    try:
        conn = connect_db()
        if not conn:
            raise HTTPException(status_code=503, detail="Serviço indisponível: Falha na conexão com o banco de dados")

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            limite_tempo_utc = datetime.now(timezone.utc) - timedelta(hours=periodo_horas)
            cur.execute(
                "SELECT id, distancia, created_on FROM leituras WHERE created_on >= %s ORDER BY created_on ASC;",
                (limite_tempo_utc,)
            )
            resultados = cur.fetchall()

        local_timezone = pytz.timezone('America/Recife')
        leituras_processadas = []
        for leitura in resultados:
            # Processa o Timestamp
            original_datetime = leitura['created_on']
            if original_datetime.tzinfo is None:
                 print(f"AVISO (ID: {leitura['id']}): Timestamp do DB veio como naive. Assumindo UTC.")
                 original_datetime = original_datetime.replace(tzinfo=timezone.utc)
            local_datetime = original_datetime.astimezone(local_timezone)
            leitura['created_on'] = local_datetime.isoformat()

            # Calcula e Adiciona o Nível
            distancia_original = leitura.get('distancia')
            leitura['nivel'] = calcular_nivel_percentual(distancia_original, MIN_NIVEL_VALUE, MAX_NIVEL_VALUE)

            leituras_processadas.append(leitura)

        return leituras_processadas

    except HTTPException as http_exc:
        raise http_exc
    except (Exception, psycopg2.Error) as e:
        print(f"API Erro em /leituras: {e}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor ao buscar histórico")
    finally:
        if conn:
            try:
                conn.close()
            except psycopg2.Error as close_err:
                print(f"API Erro ao fechar conexão DB em /leituras: {close_err}")

if __name__ == "__main__":
    import uvicorn
    print("Executando API diretamente com Uvicorn (para teste)...")
    print("Use 'run_backend.py' ou 'uvicorn api:app --host 0.0.0.0 --port 8000' para execução normal.")
    uvicorn.run(app, host="127.0.0.1", port=8000)