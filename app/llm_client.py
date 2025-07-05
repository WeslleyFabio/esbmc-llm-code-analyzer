import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Defina a API_URL e os headers globalmente aqui, como no seu exemplo
API_URL = "https://router.huggingface.co/together/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {os.environ.get('HUGGINGFACE_API_KEY')}",
    "Content-Type": "application/json"
}

# Use o modelo Mixtral que você está testando e que funcionou via Together AI
# Mantenha o USE_MOCK_LLM para testes locais
USE_MOCK_LLM = os.getenv("USE_MOCK_LLM", "False") == "True"

# --- Funções Auxiliares (mantidas como antes, mas aqui no contexto completo do arquivo) ---

def clean_llm_output(response_text):
    """
    Remove o eco do prompt da resposta da Hugging Face/Together AI.
    Mantém apenas o que vier depois da frase final do prompt: 'Responda em português.'
    """
    marker = "Responda em português."
    split_point = response_text.find(marker)
    if split_point != -1:
        return response_text[split_point + len(marker):].strip()
    else:
        # Se não encontrar o marcador, devolve as últimas 10 linhas como fallback
        lines = response_text.strip().splitlines()
        if len(lines) > 10:
            return "\n".join(lines[-10:])
        return response_text.strip()


def get_llm_response(user_code, parsed_output): # Adapte esta função para receber o código do usuário
    if USE_MOCK_LLM:
        # Retorno fake para testes
        return f"(MOCK) Interpretação gerada localmente para: {parsed_output}"

    # Verificação da chave de API
    if not os.environ.get("HUGGINGFACE_API_KEY"):
        return "Erro: API Key da Hugging Face/Together AI não encontrada. Verifique o arquivo .env."

    prompt_content = f"""
        Código C:
        ```c
        {user_code}
        ```

        Análise do verificador de erros:
        ```text
        {parsed_output}
        ```

        Com base no código e análise, siga estas instruções (em português, concisamente):

        Problema Identificado: Descreva o problema e tipo de vulnerabilidade.
        Código Corrigido: Forneça o código C completo ou trecho corrigido em bloco ```c.
        Explicação da Correção: Explique brevemente o que e por que foi corrigido.

        Formate sua resposta usando exatamente estas seções.
        """

    payload = {
        "messages": [
            {"role": "user", "content": prompt_content}
        ],
        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "temperature": 0.2,
        "max_tokens": 10000 
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        response.raise_for_status() 
        result = response.json()

        if "choices" in result and len(result["choices"]) > 0 and "message" in result["choices"][0]:
            result_text = result["choices"][0]["message"]["content"] # Acessa o 'content' dentro de 'message'
            clean_text = clean_llm_output(result_text)
            return clean_text
        else:
            return f"Resposta inesperada da API: {result}"

    except requests.exceptions.Timeout:
        return "Erro: A requisição para a API da Hugging Face/Together AI excedeu o tempo limite (Timeout)."
    except requests.exceptions.RequestException as e:
        return f"Erro ao consultar a API Hugging Face/Together AI: {e}"
    except Exception as e:
        return f"Ocorreu um erro inesperado na chamada da LLM: {e}"