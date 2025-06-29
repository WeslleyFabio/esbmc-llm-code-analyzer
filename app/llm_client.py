import os
import requests
from dotenv import load_dotenv

load_dotenv()

HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
USE_MOCK_LLM = os.getenv("USE_MOCK_LLM", "False") == "True"


def get_llm_response(parsed_output):
    if USE_MOCK_LLM:
        # Retorno fake para testes
        return f"(MOCK) Interpretação gerada localmente para: {parsed_output}"


def clean_llm_output(response_text):
    """
    Remove o eco do prompt da resposta da Hugging Face.
    Mantém apenas o que vier depois da frase final do prompt: 'Responda em português.'
    """
    marker = "Responda em português."
    split_point = response_text.find(marker)
    if split_point != -1:
        return response_text[split_point + len(marker):].strip()
    else:
        # Se não encontrar o marcador, devolve só as últimas 10 linhas como fallback
        lines = response_text.strip().splitlines()
        if len(lines) > 10:
            return "\n".join(lines[-10:])
        return response_text.strip()


def get_llm_response(parsed_output):
    if USE_MOCK_LLM:
        # Retorno fake para testes
        return f"(MOCK) Interpretação gerada localmente para: {parsed_output}"

    if not HUGGINGFACE_API_KEY:
        return "Erro: API Key da Hugging Face não encontrada. Verifique o arquivo .env."

    api_url = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"

    prompt = f"""
        Resumo da análise de código C feita pelo ESBMC:

        {parsed_output}

        Explique de forma breve (máximo 300 caracteres) qual o problema encontrado, o tipo de vulnerabilidade. Forneça o código corrigido. Responda em português.
        """

    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_KEY}"
    }

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 1000,
            "temperature": 0.2
        }
    }

    try:
        response = requests.post(
            api_url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()

        if isinstance(result, list) and "generated_text" in result[0]:
            result_text = result[0]["generated_text"]
            clean_text = clean_llm_output(result_text)
            return clean_text
        else:
            return str(result)

    except Exception as e:
        return f"Erro ao consultar a API Hugging Face: {str(e)}"
