"""Utilitários compartilhados pelos dois agentes (web e RAG).

Centraliza a geração de nome de arquivo e a gravação dos resultados, evitando
código duplicado entre ``agent.py`` e ``agent_rag.py`` (antes cada um tinha sua
própria cópia idêntica dessas funções).
"""

import unicodedata
from pathlib import Path

PASTA_RESULTADOS = Path("resultados")


def slug_arquivo(pergunta: str) -> str:
    """Gera um nome de arquivo seguro (sem acentos) a partir do tema pesquisado.

    Remove acentos para um slug 100% portável entre sistemas de arquivos.
    """
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFKD", pergunta)
        if not unicodedata.combining(c)
    )
    base = "".join(c if c.isalnum() or c in " -_" else "" for c in sem_acento)
    base = "-".join(base.lower().split())[:60].strip("-")
    return base or "pesquisa"


def salvar_resultado(pergunta: str, conteudo: str) -> str:
    """Grava o resultado em um arquivo Markdown dentro da pasta 'resultados'."""
    PASTA_RESULTADOS.mkdir(exist_ok=True)
    caminho = PASTA_RESULTADOS / f"{slug_arquivo(pergunta)}.md"
    cabecalho = f"> **Pergunta de pesquisa:** {pergunta}\n\n---\n\n"
    caminho.write_text(cabecalho + conteudo + "\n", encoding="utf-8")
    return str(caminho)
