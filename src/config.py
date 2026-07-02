"""Configuração central do projeto: caminhos e modelos.

Centraliza tudo o que os dois agentes precisam saber sobre o ambiente, num só
lugar. Os caminhos são ABSOLUTOS (derivados da raiz do repositório), de modo que
a aplicação funciona independentemente do diretório de onde é executada — antes
os caminhos eram relativos ao CWD e quebravam se rodados de outra pasta.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Carrega o .env uma única vez, aqui, para todo o projeto.
load_dotenv()

# Raiz do repositório: este arquivo é <raiz>/src/config.py.
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

PASTA_ARTIGOS = DATA_DIR / "artigos"        # PDFs de entrada do modo RAG
PASTA_VECTOR = DATA_DIR / "vectordb"        # base vetorial LanceDB (gerada)
PASTA_RESULTADOS = DATA_DIR / "resultados"  # relatórios .md gerados

# Modelos do Groq. O agente web precisa de um modelo com tool calling; o RAG usa
# um modelo próprio (contexto grande) com limite de tokens/min mais alto.
GROQ_MODEL_WEB = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_MODEL_RAG = os.getenv("GROQ_MODEL_RAG", "meta-llama/llama-4-scout-17b-16e-instruct")

# Embeddings locais (FastEmbed/ONNX), multilíngue para recuperação cross-lingual
# (perguntas em português, artigos em inglês). Sem chave de API nem cota.
EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def tem_chave_groq() -> bool:
    """Indica se a GROQ_API_KEY está configurada no ambiente."""
    return bool(os.getenv("GROQ_API_KEY"))
