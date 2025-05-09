# config_api.py
import os
import sys
from dotenv import load_dotenv

# --- Carregamento do .env ---
DOTENV_PATH = os.path.join(os.path.dirname(__file__), '.env_api')

if not load_dotenv(dotenv_path=DOTENV_PATH, override=True):
    print(f"[ConfigAPI] AVISO: Arquivo de configuração '{DOTENV_PATH}' não encontrado ou não pôde ser lido.")
    print(f"[ConfigAPI] As configurações serão buscadas diretamente do ambiente do processo.")
else:
    print(f"[ConfigAPI] Arquivo '{DOTENV_PATH}' carregado com sucesso (ou tentado carregar).")

# --- Função Auxiliar para Variáveis Obrigatórias e Conversão ---
def get_env_var(var_name, default=None, required=True, var_type=str):
    value = os.getenv(var_name, default)
    if required and value is None:
        print(f"[ConfigAPI] ERRO CRÍTICO: Variável de ambiente obrigatória '{var_name}' não definida.")
        sys.exit(1) # Ou levante uma exceção específica

    if value is not None and var_type is not str:
        try:
            if var_type is int:
                return int(value)
            if var_type is float:
                return float(value)
            if var_type is bool:
                # Considera 'true', '1', 'yes', 'on' (case-insensitive) como True
                return value.lower() in ['true', '1', 'yes', 'on']
            # Adicionar outros tipos se necessário
        except ValueError:
            print(f"[ConfigAPI] ERRO CRÍTICO: Variável '{var_name}' ('{value}') não pôde ser convertida para {var_type}.")
            sys.exit(1) # Ou levante uma exceção
    return value

# --- Configurações do Banco de Dados ---
DB_NAME = get_env_var("DB_NAME", required=True)
DB_USER = get_env_var("DB_USER", required=True)
DB_PASSWORD = get_env_var("DB_PASSWORD", required=True)
DB_HOST = get_env_var("DB_HOST", required=True)
DB_PORT = get_env_var("DB_PORT", required=True, var_type=int) 

# --- Configurações de Nível (para a API) ---
MIN_NIVEL = get_env_var("MIN_NIVEL", required=True, var_type=int)
MAX_NIVEL = get_env_var("MAX_NIVEL", required=True, var_type=int)

# --- URL de Conexão para SQLAlchemy ---
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Para verificar se tudo foi carregado
print(f"[ConfigAPI] Configurações da API carregadas: "
      f"DB_NAME={DB_NAME}, "
      f"DB_USER={DB_USER}, "
      f"DB_PASSWORD={DB_PASSWORD}, "
      f"DB_HOST={DB_HOST},"
      f"DB_PORT={DB_PORT},"
      f"MIN_NIVEL={MIN_NIVEL},"
      f"MAX_NIVEL={MAX_NIVEL},"
      f"DATABASE_URL={DATABASE_URL}"
    )