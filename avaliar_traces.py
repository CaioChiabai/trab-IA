"""Bateria de avaliação do pesquisador RAG (agent_rag.py).

Roda um conjunto de perguntas reais contra a base de artigos, captura o *trace de
recuperação* (quais artigos a busca vetorial recupera e injeta no contexto) e o
resultado de cada resposta, gerando ``traces/relatorio_traces.md``. Serve de base
para a análise de traces e a avaliação crítica exigidas no trabalho.

O agente usa RAG "tradicional" (retrieve-then-read): o Agno recupera os trechos
relevantes e os injeta no contexto antes de chamar o modelo — por isso o trace
relevante é o conjunto de artigos recuperados, e não uma chamada de ferramenta.

Para atingir os 10 casos pedidos no enunciado, acrescente perguntas à lista
``PERGUNTAS`` (inclua casos difíceis, ambíguos e fora do escopo).

Uso:
    python avaliar_traces.py
"""
import time
from pathlib import Path

import agent_rag as A

# (rótulo, pergunta). Casos "fora-escopo" e "ambigua" testam anti-alucinação.
PERGUNTAS = [
    ("comparativa",
     "Compare as metodologias dos artigos sobre aprendizado federado. Quais datasets usam, no que divergem e quais lacunas apontam?"),
    ("datasets",
     "Quais datasets e métricas de avaliação são usados nos experimentos de aprendizado federado descritos nos artigos?"),
    ("nao-iid",
     "O que os artigos dizem sobre dados não-IID (não independentes e identicamente distribuídos) e como isso afeta o treinamento?"),
    ("fedavg",
     "Qual artigo propõe o algoritmo FedAvg (Federated Averaging) e como ele reduz o custo de comunicação?"),
    ("fora-escopo",
     "Qual é a acurácia do GPT-4 no exame ENEM segundo estes artigos?"),
    ("ambigua",
     "Fale sobre segurança."),
]

PAUSA_SEG = 15  # respeita o limite de tokens/min do Groq entre execuções


def rodar() -> list[dict]:
    registros = []
    for i, (tag, q) in enumerate(PERGUNTAS, 1):
        print(f">>> [{i}/{len(PERGUNTAS)}] {tag}")
        content, erro = "", None
        fontes = A.montar_contexto(q)[1]  # trace de recuperação (local, barato)
        try:
            content, fontes = A.rodar_agente(q)
            if "tool_use_failed" not in content:
                A.salvar_resultado(q, content)
        except Exception as e:
            erro = f"{type(e).__name__}: {e}"
        registros.append({
            "tag": tag, "pergunta": q, "fontes": fontes,
            "erro": erro, "resposta": content,
        })
        print(f"   artigos_recuperados={len(fontes)} len={len(content)} erro={erro}")
        time.sleep(PAUSA_SEG)
    return registros


def gerar_relatorio(registros: list[dict]) -> None:
    Path("traces").mkdir(exist_ok=True)
    L = ["# Reasoning traces — pesquisador RAG multi-artigos", "",
         "Cada caso registra os artigos recuperados da base vetorial (injetados no "
         "contexto do modelo) e o resultado da resposta.", ""]
    for i, r in enumerate(registros, 1):
        falhou = "tool_use_failed" in (r["resposta"] or "") or r["erro"]
        L.append(f"## Caso {i} — {r['tag']}")
        L.append(f"**Pergunta:** {r['pergunta']}\n")
        fontes = ", ".join(r["fontes"]) or "(nenhum)"
        L.append(f"- Artigos recuperados (RAG): {fontes}")
        L.append(f"- Status: {'FALHA' if falhou else 'sucesso'} "
                 f"| {len(r['resposta'])} caracteres\n")
        if not falhou:
            L += ["<details><summary>Resposta</summary>", "", r["resposta"], "", "</details>", ""]
    Path("traces/relatorio_traces.md").write_text("\n".join(L), encoding="utf-8")
    print("Relatório salvo em traces/relatorio_traces.md")


if __name__ == "__main__":
    A.preparar_base()
    gerar_relatorio(rodar())
