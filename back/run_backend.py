# --- Importação de Bibliotecas Essenciais ---
# Importa módulos necessários para interação com o sistema operacional,
# gerenciamento de processos e tratamento de sinais de interrupção.
import subprocess # Para iniciar e controlar processos externos (o Listener, API, Frontend)
import sys        # Para acessar variáveis do sistema e sair do script
import time       # Para usar pausas (sleep)
import os         # Para interagir com o sistema de arquivos (caminhos)
import signal     # Para capturar sinais do sistema (como Ctrl+C)

# --- Configuração dos Processos ---
# Define os nomes dos scripts, módulos, pastas e comandos para cada parte da aplicação.
# Isso centraliza as definições e facilita a modificação futura.

# Configurações do Backend (Python)
LISTENER_SCRIPT = "mqtt_listener.py" # Nome do arquivo do script do Listener MQTT
# API_SCRIPT = "api.py" # Comentado, pois uvicorn usa nome_do_modulo:variavel_app
API_MODULE = "api"         # Nome do módulo Python da API (se o arquivo é api.py, o módulo é api)
API_VARIABLE = "app"       # Nome da variável da instância FastAPI/Flask dentro do módulo (geralmente 'app')
API_HOST = "0.0.0.0"       # Host onde a API vai rodar (0.0.0.0 significa todas as interfaces, acessível externamente)
API_PORT = "8000"          # Porta onde a API vai escutar requisições

# Configurações do Frontend (Node.js/Yarn/NPM)
FRONTEND_DIR = "front"     # Nome da pasta que contém o código do Frontend
FRONTEND_MANAGER = "yarn"  # Gerenciador de pacotes usado pelo Frontend (yarn ou npm)
FRONTEND_COMMAND = "dev"   # Comando a ser executado pelo gerenciador de pacotes (ex: 'dev', 'start')

# --- Determinação de Caminhos ---
# Calcula os caminhos completos para os scripts e pastas com base na localização deste script.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) # Diretório onde este script 'runner' está
LISTENER_PATH = os.path.join(SCRIPT_DIR, LISTENER_SCRIPT) # Caminho completo para o script do Listener
# API_PATH = os.path.join(SCRIPT_DIR, API_SCRIPT) # Não precisamos mais do caminho direto
# Caminho completo para a pasta do Frontend. Assume que 'front' está um nível acima
# do diretório onde este script 'runner' está. Ex: project/runner.py, project/front/...
FRONTEND_DIR_PATH = os.path.join(SCRIPT_DIR, '..', FRONTEND_DIR)

# --- Lista de Processos Ativos ---
# Lista para armazenar informações sobre os processos que foram iniciados.
# Usado para monitorar e encerrar os processos posteriormente.
processes = [] # Cada item será um dicionário como {'name': ..., 'process': ..., 'pid': ...}

# --- Manipulador de Sinal de Interrupção ---
# Função chamada quando o script recebe um sinal para terminar (como Ctrl+C).
def signal_handler(sig, frame):
    """
    Handler para sinais SIGINT (Ctrl+C) e SIGTERM.
    Tenta parar todos os processos iniciados de forma graciosa, e força o encerramento se necessário.
    """
    print("\n" + "-"*50) # Imprime uma linha separadora para destacar a mensagem
    print("Recebido sinal de interrupção. Parando todos os processos...")

    # Itera sobre a lista de processos em ordem inversa. Isso pode ser útil
    # se houver dependências na ordem de desligamento (ex: Frontend -> API -> Listener).
    for p_info in reversed(processes):
        pid = p_info.get('pid')         # PID do processo
        name = p_info.get('name')       # Nome descritivo do processo
        process_obj = p_info.get('process') # O objeto Popen do subprocess

        # Verifica se o objeto do processo existe e se o processo ainda está rodando (poll() é None)
        if process_obj and process_obj.poll() is None:
            print(f"Parando {name} (PID: {pid})...")
            try:
                # Tenta terminar o processo de forma graciosa (envia SIGTERM)
                process_obj.terminate()
                try:
                    # Espera um tempo limitado (3 segundos) pelo processo terminar sozinho
                    process_obj.wait(timeout=3)
                    print(f"{name} parado com sucesso.")
                except subprocess.TimeoutExpired:
                    # Se o processo não terminar no tempo, força o encerramento (envia SIGKILL)
                    print(f"{name} não terminou dentro do tempo limite, forçando kill...")
                    process_obj.kill()
                    print(f"{name} forçado a parar.")
            except Exception as e:
                # Captura qualquer erro que ocorra durante a tentativa de parar o processo
                print(f"Erro ao tentar parar {name} (PID: {pid}): {e}")
        # Se o processo já havia parado antes do sinal ser recebido
        elif pid:
            print(f"{name} (PID: {pid}) já havia parado ou não foi iniciado corretamente.")

    print("-" * 50)
    print("Processos parados. Saindo do script runner.")
    sys.exit(0) # Sai do script runner com código de sucesso

# --- Registro dos Manipuladores de Sinal ---
# Associa a função signal_handler aos sinais SIGINT (geralmente por Ctrl+C) e SIGTERM.
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# --- Mensagens Iniciais ---
print("Iniciando Backend (MQTT Listener, API) e Frontend (Servidor de Desenvolvimento)...")
print("Os logs de todos os processos aparecerão abaixo.")
print("Pressione Ctrl+C para parar TODOS os processos de forma coordenada.")
print("-" * 50)

# --- Bloco Principal de Inicialização e Monitoramento ---
# Tenta iniciar todos os processos e monitorá-los.
try:
    # --- Verificação de Arquivos/Pastas Essenciais ---
    # Verifica se os arquivos/diretórios necessários existem antes de tentar iniciar os processos.
    if not os.path.isfile(LISTENER_PATH):
        raise FileNotFoundError(f"Erro de Configuração: Script MQTT Listener '{LISTENER_PATH}' não encontrado!")
    # Verifica se o arquivo da API existe (assume que o módulo 'api' corresponde ao arquivo 'api.py' no SCRIPT_DIR)
    if not os.path.isfile(os.path.join(SCRIPT_DIR, f"{API_MODULE}.py")):
        raise FileNotFoundError(f"Erro de Configuração: Arquivo API '{API_MODULE}.py' não encontrado em '{SCRIPT_DIR}'!")
    # Verifica se a pasta do Frontend existe
    if not os.path.isdir(FRONTEND_DIR_PATH):
        raise FileNotFoundError(f"Erro de Configuração: Pasta do Frontend '{FRONTEND_DIR_PATH}' não encontrada!")
    # Verifica se o package.json existe na pasta do Frontend (aviso, não um erro fatal)
    if not os.path.isfile(os.path.join(FRONTEND_DIR_PATH, 'package.json')):
        print(f"Aviso: 'package.json' não encontrado em '{FRONTEND_DIR_PATH}'. O comando '{FRONTEND_MANAGER} run {FRONTEND_COMMAND}' pode falhar se as dependências do Frontend não estiverem instaladas.")

    # --- Inicia MQTT Listener ---
    print("\n" + "-"*20 + " Iniciando MQTT Listener " + "-"*20)
    # Comando para executar o script Python do Listener.
    # sys.executable garante que seja usado o mesmo interpretador Python que roda este script runner.
    listener_cmd_list = [sys.executable, LISTENER_PATH]
    # Inicia o processo em um novo grupo (principalmente para Windows) para melhor controle de sinais.
    listener_process = subprocess.Popen(listener_cmd_list,
                                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0)
    # Adiciona as informações do processo à lista de monitoramento.
    processes.append({'name': 'MQTT Listener', 'process': listener_process, 'pid': listener_process.pid})
    print(f"-> [Runner] MQTT Listener iniciado com PID: {listener_process.pid}")
    time.sleep(0.5) # Pequena pausa para dar tempo ao processo iniciar

    # --- Inicia API com Uvicorn ---
    print("\n" + "-"*20 + " Iniciando API com Uvicorn " + "-"*20)
    # Comando para rodar o Uvicorn como um módulo Python.
    # Isso garante que o uvicorn seja executado a partir do ambiente Python ativo (ex: ambiente virtual).
    api_cmd_list = [
        sys.executable, # Usa o mesmo interpretador Python
        "-m", "uvicorn", # Executa o módulo 'uvicorn'
        f"{API_MODULE}:{API_VARIABLE}", # Especifica o módulo da API e o nome da instância da aplicação (ex: api:app)
        "--host", API_HOST,           # Define o host configurado
        "--port", API_PORT,           # Define a porta configurada
        # "--reload" # Descomente esta linha durante o desenvolvimento se quiser auto-reload da API ao mudar arquivos
    ]
    # Inicia o processo da API. É importante definir 'cwd' (Current Working Directory)
    # para o diretório do script runner (onde api.py reside) para que o uvicorn
    # encontre o módulo da sua API corretamente.
    api_process = subprocess.Popen(api_cmd_list,
                                   cwd=SCRIPT_DIR, # Define o diretório de execução do processo
                                   creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0)
    processes.append({'name': 'API Server (Uvicorn)', 'process': api_process, 'pid': api_process.pid})
    print(f"-> [Runner] API (Uvicorn) iniciada com PID: {api_process.pid}")
    time.sleep(1) # Pausa um pouco maior para a API carregar

    # --- Inicia Frontend Development Server ---
    print("\n" + "-"*20 + " Iniciando Frontend Dev Server " + "-"*20)
    # Comando para executar o gerenciador de pacotes do Frontend.
    # No Windows, o executável pode precisar do '.cmd' (yarn.cmd, npm.cmd).
    # shell=True é usado no Windows porque comandos como 'yarn' podem ser aliases ou scripts.
    if sys.platform == "win32":
        frontend_cmd = f"{FRONTEND_MANAGER}.cmd"
    else:
        frontend_cmd = FRONTEND_MANAGER # Em Linux/macOS, geralmente não precisa do .cmd
    frontend_cmd_list = [frontend_cmd, 'run', FRONTEND_COMMAND] # Ex: ['yarn', 'run', 'dev']

    # Inicia o processo do Frontend. É crucial definir 'cwd'
    # para o diretório raiz do Frontend (onde está o package.json).
    frontend_process = subprocess.Popen(
        frontend_cmd_list,
        cwd=FRONTEND_DIR_PATH,      # Define o diretório de execução para a pasta do Frontend
        shell=True if sys.platform == "win32" else False, # Usa shell=True apenas no Windows
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    )
    processes.append({'name': 'Frontend Dev Server', 'process': frontend_process, 'pid': frontend_process.pid})
    print(f"-> [Runner] Servidor Frontend iniciado com PID: {frontend_process.pid} (Comando: '{FRONTEND_MANAGER} run {FRONTEND_COMMAND}')")

    # --- Loop Principal de Monitoramento ---
    print("\n" + "-" * 50)
    print("Todos os processos iniciados.")
    print("-> Pressione Ctrl+C no terminal para parar TODOS os processos de forma segura.")
    print("-> Observe os logs dos processos sendo exibidos abaixo.")

    # Este loop mantém o script runner rodando e monitora os processos filhos.
    # Se qualquer processo filho terminar inesperadamente, o runner detecta e tenta parar os outros.
    while True:
        # Itera sobre os processos monitorados
        for p_info in processes:
            process_obj = p_info.get('process')
            name = p_info.get('name')

            # Verifica se o processo existe e se ele TERMINOU (poll() retorna o código de saída se terminou, None se ainda rodando)
            if process_obj and process_obj.poll() is not None:
                # Se um processo terminou inesperadamente...
                print(f"\n[AVISO] Processo '{name}' (PID: {p_info.get('pid')}) terminou inesperadamente com código de saída {process_obj.returncode}.")
                print("Iniciando procedimento de desligamento para os outros processos...")
                # Chama o manipulador de sinal para tentar parar os demais processos
                signal_handler(None, None) # Passa None para sig e frame, apenas para chamar a lógica de desligamento
        # Pausa curta para não consumir 100% da CPU neste loop de monitoramento
        time.sleep(2)

# --- Tratamento de Exceções na Inicialização ---
# Captura erros que podem ocorrer ANTES dos processos entrarem no loop de monitoramento
except FileNotFoundError as e:
    # Erro específico se algum arquivo/pasta configurado não for encontrado
    print(f"\nErro de Configuração: {e}")
    print("Por favor, verifique se os nomes dos arquivos/scripts e os caminhos das pastas na seção de CONFIGURAÇÃO estão corretos.")
except Exception as e:
    # Captura qualquer outro erro geral durante a fase de inicialização
    print(f"\nErro geral inesperado durante a inicialização dos scripts: {e}")
    # Tenta limpar (parar) quaisquer processos que possam ter sido iniciados antes do erro fatal.
    print("Tentando parar processos iniciados antes do erro...")
    signal_handler(None, None) # Chama o handler para tentar desligar o que foi iniciado

# O script termina aqui (ou pelo sys.exit(0) dentro do signal_handler)