import os
import requests
import json
from typing import Dict, Any

def score_with_llm(text: str) -> Dict[str, Any]:
    """
    Gera uma análise completa do texto usando um LLM (Modelo de Linguagem Grande).
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "error": "Chave de API do Gemini não configurada. Defina a variável de ambiente GEMINI_API_KEY."
        }

    # Prompt para o LLM
    prompt_text = f"""
    Você é um assistente de revisão de pares especializado em artigos acadêmicos brasileiros.
    Analise o seguinte texto e forneça uma resposta em formato JSON com as seguintes chaves:
    1. 'scores': Um objeto com notas de 1 a 100 para 'Relevância e Originalidade', 'Rigor Metodológico', 'Qualidade da Escrita', 'Fundamentação Teórica' e 'Resultados e Discussão'.
    2. 'explainability': Um objeto com uma breve explicação para cada nota.
    3. 'recommendations': Uma lista de três a cinco recomendações específicas e acionáveis para melhorar o texto.

    O texto para análise é:
    "{text}"
    """

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }
    
    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_text}
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        llm_output = response.json()
        
        # A API retorna um JSON dentro de uma string de texto. Precisamos parsear
        # para garantir que o formato é o esperado
        
        return llm_output

    except requests.exceptions.HTTPError as errh:
        return {"error": f"Erro HTTP: {errh}"}
    except requests.exceptions.ConnectionError as errc:
        return {"error": f"Erro de Conexão: {errc}"}
    except requests.exceptions.Timeout as errt:
        return {"error": f"Tempo de espera excedido: {errt}"}
    except requests.exceptions.RequestException as err:
        return {"error": f"Erro geral na requisição: {err}"}
    except Exception as e:
        return {"error": f"Erro inesperado no processamento: {e}"}
