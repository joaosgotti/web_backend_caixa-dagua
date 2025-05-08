# run_api_dev.py

import subprocess
import sys
import time
import os
import signal
from enum import Enum

# --- Configurações para iniciar a API ---
# Estas são configurações para o *comando* que inicia o Uvicorn.
# A própria API (api.py) buscará suas configurações de DB, MIN_NIVEL, etc., do seu .env.
API_MODULE_NAME = "api"    # Nome do arquivo Python da API (sem .py)
API_APP_VARIABLE = "app"   # Nome da variável da instância FastAPI em api.py
API_HOST_TO_BIND = "0.0.0.0" # Host em que o Uvicorn vai escutar
API_PORT_TO_LISTEN = "8000"  # Porta em que o Uvicorn vai escutar
ENABLE_UVICORN_RELOAD = True # Define se o Uvicorn deve usar --reload

# --- Determinação de Caminhos ---
# Assume que este script (run_api_dev.py), api.py e o .env da API
# estão todos no mesmo diretório.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
API_FILE_CHECK_PATH = os.path.join(SCRIPT_DIR, f"{API_MODULE_NAME}.py")
API_DOTENV_CHECK_PATH = os.path.join(SCRIPT_DIR, ".env") # Arquivo .env que a api.py irá carregar

# --- Processo da API ---
api_process_info = None # Para armazenar informações do processo Uvicorn

# --- Manipulador de Sinal de Interrupção (Ctrl+C) ---
def shutdown_api_process(sig, frame):
    global api_process_info
    print("\n" + "="*50)
    print("Sinal de interrupção recebido. Tentando parar o servidor da API...")

    if api_process_info and api_process_info.get('process'):
        process_obj = api_process_info['process']
        pid = api_process_info.get('pid', 'N/A')
        name = api_process_info.get('name', 'API Server')

        if process_obj.poll() is None: # Se o processo ainda estiver rodando
            print(f"Enviando sinal TERM para {name} (PID: {pid})...")
            process_obj.terminate() # Envia SIGTERM (mais gracioso)
            try:
                process_obj.wait(timeout=5) # Espera até 5 segundos
                print(f"{name} parado com sucesso.")
            except subprocess.TimeoutExpired:
                print(f"{name} não respondeu ao TERM, enviando KILL...")
                process_obj.kill() # Envia SIGKILL (forçado)
                print(f"{name} forçado a parar.")
            except Exception as e:
                print(f"Erro ao tentar parar {name}: {e}")
        else:
            print(f"{name} (PID: {pid}) já havia parado (código: {process_obj.poll()}).")
    else:
        print("Nenhum processo da API para parar ou informações do processo não encontradas.")

    print("=" * 50)
    print("Runner da API finalizado.")
    sys.exit(0)

# Registra o handler para SIGINT (Ctrl+C) e SIGTERM
signal.signal(signal.SIGINT, shutdown_api_process)
signal.signal(signal.SIGTERM, shutdown_api_process)

# --- Bloco Principal ---
if __name__ == "__main__":
    print("="*50)
    print("Iniciando o Runner de Desenvolvimento da API FastAPI...")
    print(f"-> API: {API_MODULE_NAME}:{API_APP_VARIABLE}")
    print(f"-> Host: {API_HOST_TO_BIND}")
    print(f"-> Porta: {API_PORT_TO_LISTEN}")
    print(f"-> Uvicorn Reload: {'Ativado' if ENABLE_UVICORN_RELOAD else 'Desativado'}")
    print("Pressione Ctrl+C para parar o servidor da API.")
    print("="*50)

    try:
        # Verificação 1: O arquivo da API (api.py) existe?
        if not os.path.isfile(API_FILE_CHECK_PATH):
            print(f"ERRO CRÍTICO: Arquivo da API '{API_FILE_CHECK_PATH}' não encontrado!")
            print("O runner não pode continuar.")
            sys.exit(1)
        print(f"[Runner] Arquivo da API '{API_FILE_CHECK_PATH}' encontrado.")

        # Verificação 2: O arquivo .env (para a API) existe? (Aviso, não erro fatal para o runner)
        # A própria api.py vai falhar ou logar erros se não conseguir carregar suas configs.
        if not os.path.isfile(API_DOTENV_CHECK_PATH):
            print(f"[Runner] AVISO: Arquivo '.env' em '{SCRIPT_DIR}' não encontrado.")
            print(f"[Runner] A API '{API_MODULE_NAME}.py' pode não carregar suas configurações corretamente.")
        else:
            print(f"[Runner] Arquivo '.env' em '{SCRIPT_DIR}' encontrado (será usado pela API).")
        
        # Monta o comando para executar o Uvicorn
        # Usamos sys.executable para garantir que estamos usando o python do venv
        uvicorn_command = [
            sys.executable,        # Ex: /caminho/para/venv/bin/python
            "-m", "uvicorn",       # Executa o módulo uvicorn
            f"{API_MODULE_NAME}:{API_APP_VARIABLE}", # Ex: api:app
            "--host", API_HOST_TO_BIND,
            "--port", API_PORT_TO_LISTEN,
        ]
        if ENABLE_UVICORN_RELOAD:
            uvicorn_command.append("--reload")

        print(f"[Runner] Executando comando: {' '.join(uvicorn_command)}")
        print("-" * 50) # Linha separadora antes dos logs do Uvicorn

        # Inicia o processo Uvicorn
        # Os logs (stdout/stderr) do Uvicorn irão para o console deste runner.
        # cwd=SCRIPT_DIR garante que Uvicorn procure api.py no diretório correto.
        process = subprocess.Popen(uvicorn_command, cwd=SCRIPT_DIR)
        api_process_info = {
            'name': 'API Server (Uvicorn)',
            'process': process,
            'pid': process.pid
        }
        
        # Mantém o runner vivo enquanto o Uvicorn estiver rodando
        # O signal_handler (Ctrl+C) cuidará do encerramento.
        # Se o Uvicorn morrer sozinho, o runner também morrerá (ou podemos adicionar lógica para reiniciar).
        process.wait() # Espera o processo Uvicorn terminar

        # Se chegarmos aqui, o Uvicorn terminou por conta própria (não por Ctrl+C)
        if api_process_info and api_process_info['process']:
            exit_code = api_process_info['process'].returncode
            print("-" * 50)
            print(f"[Runner] Processo Uvicorn (PID: {api_process_info.get('pid')}) terminou com código de saída: {exit_code}.")
            # Se o código de saída for diferente de 0, pode indicar um erro no Uvicorn/API.
            if exit_code != 0:
                 print("[Runner] Verifique os logs do Uvicorn acima para possíveis erros na API.")

    except FileNotFoundError: # Já tratado acima, mas como um catch-all
        # O sys.exit(1) acima já deve ter parado.
        pass # O erro já foi impresso
    except KeyboardInterrupt:
        # Se Ctrl+C ocorrer durante a fase de setup do runner (antes do process.wait())
        # O signal_handler pode não ter sido chamado se o processo Uvicorn não foi totalmente iniciado.
        # Chamamos explicitamente se necessário.
        if not (api_process_info and api_process_info.get('process_stopped_by_signal_handler')):
             shutdown_api_process(None, None)
    except Exception as e:
        print(f"[Runner] ERRO INESPERADO no script runner: {e}")
        # Tenta parar o processo da API se ele foi iniciado
        if api_process_info and api_process_info.get('process_stopped_by_signal_handler') is None:
            shutdown_api_process(None, None)
    finally:
        print("[Runner] Script runner finalizando.")