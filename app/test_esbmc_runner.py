import os
import requests
from dotenv import load_dotenv # Importe load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv() 

API_URL = "https://router.huggingface.co/together/v1/chat/completions"

# Use a variável de ambiente correta, que é HUGGINGFACE_API_KEY
headers = {
    "Authorization": f"Bearer {os.environ.get('HUGGINGFACE_API_KEY')}", # Use .get() para evitar KeyError se a variável não estiver definida
    "Content-Type": "application/json" # Adicione este cabeçalho, é boa prática para requisições JSON
}

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    response.raise_for_status() # Lança uma exceção para erros HTTP (como 404, 500)
    return response.json()

try:
    response = query({
        "messages": [
            {
                "role": "user",
                "content": "What is the capital of France?"
            }
        ],
        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1"
    })

    # Verifica se 'choices' e 'message' existem antes de tentar acessá-los
    if "choices" in response and len(response["choices"]) > 0 and "message" in response["choices"][0]:
        print(response["choices"][0]["message"])
    else:
        print("Resposta inesperada da API:", response)

except requests.exceptions.RequestException as e:
    print(f"Erro ao fazer a requisição à API: {e}")
except Exception as e:
    print(f"Ocorreu um erro inesperado: {e}")