# run_backend.py

import os
import sys
import uvicorn 
from dotenv import load_dotenv

load_dotenv()

API_MODULE_NAME = os.getenv("API_MODULE_NAME") 
API_APP_VARIABLE = os.getenv("API_APP_VARIABLE")
API_HOST_TO_BIND = os.getenv("API_HOST_TO_BIND")
API_PORT_TO_LISTEN = os.getenv("API_PORT_TO_LISTEN")

if not all([API_MODULE_NAME, API_APP_VARIABLE, API_HOST_TO_BIND, API_PORT_TO_LISTEN]):
        print("ERRO: Alguma variável de ambiente não foi definida")
        sys.exit(1)

ENABLE_UVICORN_RELOAD = False

APP_STRING = F"{API_MODULE_NAME}:{API_APP_VARIABLE}"

print(f"--- Iniciando API: {APP_STRING} em http://{API_HOST_TO_BIND}:{API_HOST_TO_BIND} ---")

if ENABLE_UVICORN_RELOAD:
    print("--- Reload ativado. Ctrl+C para parar. ---")
else:
    print("--- Ctrl+C para parar. ---")

try:
    uvicorn.run(
        APP_STRING,
        host=API_HOST_TO_BIND,
        port=int(API_PORT_TO_LISTEN),
        reload=ENABLE_UVICORN_RELOAD,
        log_level="info"
    )

except ValueError:
    print(f"ERRO: O valor da porta '{API_PORT_TO_LISTEN}' não é um número válido.")
    sys.exit(1)
except ImportError:
    print(f"ERRO: Não foi possível importar a aplicação '{APP_STRING}'. Verifique o nome do módulo e da variável.")
    sys.exit(1)
except KeyboardInterrupt:
    print("\n--- Servidor encerrado pelo usuário. ---")
except Exception as e:
    print(f"ERRO inesperado ao iniciar o servidor: {e}")
    sys.exit(1)















SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
API_FILE_PATH = os.path.join(SCRIPT_DIR, f"{API_MODULE_NAME}.py")


api_process = None 


def shutdown_handler(sig, frame):
    global api_process
    print("\n--- Encerrando servidor API... ---")
    if api_process and api_process.poll() is None:
        api_process.terminate()
        try:
            api_process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            api_process.kill() 
            api_process.wait() 
    print("--- Servidor API encerrado. ---")
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown_handler) 
signal.signal(signal.SIGTERM, shutdown_handler) 

# --- Bloco Principal ---
if __name__ == "__main__":
    print(f"--- Iniciando API: {API_MODULE_NAME}:{API_APP_VARIABLE} em {API_HOST_TO_BIND}:{API_PORT_TO_LISTEN} ---")
    if ENABLE_UVICORN_RELOAD:
        print("--- Reload ativado. Ctrl+C para parar. ---")
    else:
        print("--- Ctrl+C para parar. ---")

    if not os.path.isfile(API_FILE_PATH):
        print(f"ERRO: Arquivo API '{API_FILE_PATH}' não encontrado. Saindo.")
        sys.exit(1)

    uvicorn_cmd = [
        sys.executable, 
        "-m", "uvicorn",
        f"{API_MODULE_NAME}:{API_APP_VARIABLE}",
        "--host", API_HOST_TO_BIND,
        "--port", API_PORT_TO_LISTEN,
    ]
    if ENABLE_UVICORN_RELOAD:
        uvicorn_cmd.append("--reload")

    try:
        api_process = subprocess.Popen(uvicorn_cmd, cwd=SCRIPT_DIR)
        api_process.wait() 

        if api_process.returncode is not None and api_process.returncode != 0:
            print(f"--- Servidor API terminou com erro (código: {api_process.returncode}). ---")

    except FileNotFoundError:
        print("ERRO: Não foi possível iniciar o Uvicorn. Verifique Python/Uvicorn no PATH.")
        sys.exit(1)
    except Exception as e:
        print(f"[Runner] Erro inesperado: {e}")
        if api_process and api_process.poll() is None:
            api_process.kill() 
        sys.exit(1)
