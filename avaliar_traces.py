"""Bateria de avaliação do pesquisador RAG (agent_rag.py).

Roda um conjunto de perguntas reais contra a base de artigos, captura os
reasoning traces (chamadas de ferramenta + artigos recuperados) e gera um
relatório em ``traces/relatorio_traces.md``. Serve de base para a análise de
traces e a avaliação crítica exigidas no trabalho.

Para atingir os 10 casos pedidos no enunciado, basta acrescentar perguntas à
lista ``PERGUNTAS`` abaixo (inclua casos difíceis, ambíguos e fora do escopo).

Uso:
    python avaliar_traces.py
"""
import json
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

PAUSA_SEG = 20  # respeita o limite de tokens/min do Groq entre execuções


def _artigos_do_resultado(result_json: str) -> list[str]:
    """Extrai os arquivos (artigos) recuperados de um resultado de busca."""
    arquivos: list[str] = []
    try:
        for chunk in json.loads(result_json):
            a = (chunk.get("meta_data") or {}).get("arquivo")
            if a and a not in arquivos:
                arquivos.append(a)
    except Exception:
        pass
    return arquivos


def rodar() -> list[dict]:
    registros = []
    for i, (tag, q) in enumerate(PERGUNTAS, 1):
        print(f">>> [{i}/{len(PERGUNTAS)}] {tag}")
        tool_infos, content, erro = [], "", None
        try:
            resp = A.agent.run(q)
            content = resp.content or ""
            for t in (getattr(resp, "tools", []) or []):
                args = getattr(t, "tool_args", {}) or {}
                tool_infos.append({
                    "tool": getattr(t, "tool_name", "?"),
                    "query": args.get("query", args),
                    "artigos_recuperados": _artigos_do_resultado(getattr(t, "result", "") or ""),
                })
            if "tool_use_failed" not in content:
                A.salvar_resultado(q, content)
        except Exception as e:
            erro = f"{type(e).__name__}: {e}"
        registros.append({
            "tag": tag, "pergunta": q, "n_tool_calls": len(tool_infos),
            "tool_calls": tool_infos, "erro": erro, "resposta": content,
        })
        time.sleep(PAUSA_SEG)
    return registros


def gerar_relatorio(registros: list[dict]) -> None:
    Path("traces").mkdir(exist_ok=True)
    L = ["# Reasoning traces — pesquisador RAG multi-artigos", ""]
    for i, r in enumerate(registros, 1):
        falhou = "tool_use_failed" in (r["resposta"] or "") or r["erro"]
        L.append(f"## Caso {i} — {r['tag']}")
        L.append(f"**Pergunta:** {r['pergunta']}\n")
        for j, tc in enumerate(r["tool_calls"], 1):
            arts = ", ".join(tc["artigos_recuperados"]) or "(nenhum)"
            L.append(f"- Tool call {j}: `{tc['tool']}(query=\"{tc['query']}\")` → {arts}")
        if not r["tool_calls"]:
            L.append("- Nenhuma chamada de ferramenta registrada.")
        L.append(f"- Status: {'FALHA' if falhou else 'sucesso'} "
                 f"| {len(r['resposta'])} caracteres\n")
        if not falhou:
            L += ["<details><summary>Resposta</summary>", "", r["resposta"], "", "</details>", ""]
    Path("traces/relatorio_traces.md").write_text("\n".join(L), encoding="utf-8")
    print("Relatório salvo em traces/relatorio_traces.md")


if __name__ == "__main__":
    A.preparar_base()
    regs = rodar()
    gerar_relatorio(regs)
