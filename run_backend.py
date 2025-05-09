# run_api_dev.py (versão ultra-concisa)

import subprocess
import sys
import os
import signal
from dotenv import load_dotenv
load_dotenv()

# --- Configurações Essenciais ---
API_MODULE_NAME = os.getenv("API_MODULE_NAME")  # Nome do módulo da API
API_APP_VARIABLE = os.getenv("API_APP_VARIABLE")  # Nome da variável do app FastAPI
API_HOST_TO_BIND = os.getenv("API_HOST_TO_BIND")
API_PORT_TO_LISTEN = os.getenv("API_PORT_TO_LISTEN")  # Porta para escutar
ENABLE_UVICORN_RELOAD = os.getenv("ENABLE_UVICORN_RELOAD") # Habilitar reload do Uvicorn

# --- Caminhos ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
API_FILE_PATH = os.path.join(SCRIPT_DIR, f"{API_MODULE_NAME}.py")

# --- Processo Global ---
api_process = None # Referência global para o processo Uvicorn

# --- Manipulador de Sinal (Ctrl+C e TERM) ---
def shutdown_handler(sig, frame):
    global api_process
    print("\n--- Encerrando servidor API... ---")
    if api_process and api_process.poll() is None:  # Se o processo existe e está rodando
        api_process.terminate()  # Tenta terminar graciosamente
        try:
            api_process.wait(timeout=2)  # Espera um pouco (timeout curto)
        except subprocess.TimeoutExpired:
            api_process.kill()  # Força o encerramento se não responder
            api_process.wait()  # Garante que o processo "kill" seja coletado
    print("--- Servidor API encerrado. ---")
    sys.exit(0)

# Registra os manipuladores de sinal
signal.signal(signal.SIGINT, shutdown_handler) # Para Ctrl+C
signal.signal(signal.SIGTERM, shutdown_handler) # Para outros sinais de término

# --- Bloco Principal ---
if __name__ == "__main__":
    print(f"--- Iniciando API: {API_MODULE_NAME}:{API_APP_VARIABLE} em {API_HOST_TO_BIND}:{API_PORT_TO_LISTEN} ---")
    if ENABLE_UVICORN_RELOAD:
        print("--- Reload ativado. Ctrl+C para parar. ---")
    else:
        print("--- Ctrl+C para parar. ---")

    # Verificação crítica mínima: o arquivo da API existe?
    if not os.path.isfile(API_FILE_PATH):
        print(f"ERRO: Arquivo API '{API_FILE_PATH}' não encontrado. Saindo.")
        sys.exit(1)

    # Monta o comando Uvicorn
    uvicorn_cmd = [
        sys.executable,  # Usa o interpretador Python atual (bom para venvs)
        "-m", "uvicorn",
        f"{API_MODULE_NAME}:{API_APP_VARIABLE}",
        "--host", API_HOST_TO_BIND,
        "--port", API_PORT_TO_LISTEN,
    ]
    if ENABLE_UVICORN_RELOAD:
        uvicorn_cmd.append("--reload")

    try:
        # Inicia o Uvicorn. Logs do Uvicorn irão para o console.
        # cwd garante que Uvicorn procure api.py no diretório correto.
        api_process = subprocess.Popen(uvicorn_cmd, cwd=SCRIPT_DIR)
        api_process.wait()  # Espera o processo Uvicorn terminar

        # Se chegarmos aqui, Uvicorn terminou por conta própria (não por Ctrl+C)
        # Informa apenas se houve um código de saída de erro.
        if api_process.returncode is not None and api_process.returncode != 0:
            print(f"--- Servidor API terminou com erro (código: {api_process.returncode}). ---")
        # Se Uvicorn sair com código 0, o script simplesmente termina sem mensagens adicionais.

    except FileNotFoundError:
        # Erro se o comando `python` ou `uvicorn` não for encontrado.
        print("ERRO: Não foi possível iniciar o Uvicorn. Verifique Python/Uvicorn no PATH.")
        sys.exit(1)
    except Exception as e:
        # Tratamento de erro genérico e muito básico para o runner
        print(f"[Runner] Erro inesperado: {e}")
        if api_process and api_process.poll() is None:
            api_process.kill() # Tenta parar o Uvicorn se o runner falhar
        sys.exit(1)
    # Nenhuma mensagem "finalizando runner" para manter a concisão.
    # Se o servidor terminar normalmente (código 0), o script apenas sai.