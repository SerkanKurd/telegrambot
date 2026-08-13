import ollama
from dotenv import load_dotenv
import os
import logging
import requests

load_dotenv()
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma2:2b")


def generate(prompt: str) -> str:
    try:
        client = ollama.Client(OLLAMA_HOST)
        response = client.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": "Cevaplarını en fazla 2 cümleyle sınırla."},
                {"role": "user", "content": prompt}
            ],
            options={
                "num_predict": 64,       # max token sayısı
                "temperature": 0.2,      # daha kısa ve odaklı
                "top_p": 0.8,            # sampling daraltma
                "top_k": 20,             # sampling daraltma
                # "stop": ["\n\n"]         # ilk boş satırda kes
            }
        )
        return response["message"]["content"]
    except Exception as e:
        logging.error(f"Error connecting to Ollama server: {e}")
        return "Sunucuya bağlanılamıyor, lütfen daha sonra tekrar deneyin."


def api_test() -> bool:
    # OLLAMA_HOST
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=1)
        response.raise_for_status()
        return True
    except Exception:
        return False


if __name__ == "__main__":
    generate("Yamaç paraşütü nedir?")
    # api_test()
