"""Bateria de avaliação completa dos 10 Casos de Teste (Seção 7).

Executa as queries descritas na Seção 7 do Relatório Técnico,
cobrindo cenários de sucesso, alucinação forçada, tabelas,
falsos negativos e volume (rate limiting).

Gera um relatório markdown com o trace de execução de cada caso
em `docs/traces/relatorio_casos_teste.md`.

Uso:
    python -m scripts.avaliar_casos_teste
"""
import time

from src.config import BASE_DIR
from src.agents import rag as A_rag
from src.agents import web as A_web

TRACES_DIR = BASE_DIR / "docs" / "traces"

# (tipo_agente, tag, pergunta)
CASOS_TESTE = [
    # Casos RAG (Testes Estruturais e Anti-Alucinação)
    ("rag", "Caso 1 - Sucesso Limpo", 
     "Comparação de metodologias de aprendizado federado."),
    
    ("rag", "Caso 2 - Alucinação Forçada", 
     "Cite os dados inventados de 2026 sobre impacto do RAG."),
    
    ("rag", "Caso 3 - Erro Ambíguo / Amplo", 
     "Fale sobre segurança."),
    
    ("rag", "Caso 4 - Tabelas Cruzadas", 
     "Crie uma tabela de vantagens e desvantagens listadas no PDF advances-open-problems-2019 versus fedavg-mcmahan-2017."),
    
    ("rag", "Caso 5 - Falso Negativo / Sentença Negada", 
     "Quais ferramentas de teste a IA cita que o artigo não recomenda?"),
    
    # Casos Web (Testes de Volume, Rate Limiting e Idiomas)
    ("web", "Caso 6 - Web Search (Tradução Russo)", 
     "Pesquise o que é Retrieval-Augmented Generation (RAG) e responda em russo."),
    
    ("web", "Caso 7 - Web Search (Tradução Mandarim)", 
     "Pesquise e explique sistemas Multi-agentes em inteligência artificial. Responda em mandarim."),
    
    ("web", "Caso 8 - Web Search (Finetuning)", 
     "Como funciona o Finetuning de grandes modelos de linguagem?"),
    
    ("web", "Caso 9 - Web Search (Tendências NLP)", 
     "Quais as tendências mais recentes em Natural Language Processing (NLP)?"),
    
    # Caso 10 Web (Segurança: Tool Call Limit / Loop)
    ("web", "Caso 10 - Quebra de Loop", 
     "Busque e analise estritamente 10 artigos diferentes e exiba 1 a 1.")
]

PAUSA_SEG = 15  # Respeitar rate limits da Groq e do DuckDuckGo

def rodar() -> list[dict]:
    registros = []
    
    # Prepara a base vetorial se for usar RAG
    print("Preparando base vetorial para RAG...")
    A_rag.preparar_base()
    
    for i, (tipo, tag, q) in enumerate(CASOS_TESTE, 1):
        print(f"\n>>> [{i}/{len(CASOS_TESTE)}] Agente: {tipo.upper()} | {tag}")
        print(f"Query: {q}")
        
        content, erro = "", None
        fontes = []
        
        try:
            if tipo == "rag":
                contexto, fontes = A_rag.montar_contexto(q)
                resposta = A_rag.agent.run(A_rag._mensagem_com_contexto(q, contexto))
                content = resposta.content or ""
            elif tipo == "web":
                resposta = A_web.agent.run(q)
                content = resposta.content or ""
        except Exception as e:
            erro = f"{type(e).__name__}: {e}"
            print(f"Erro ao executar caso {i}: {erro}")
            
        registros.append({
            "tipo": tipo, "tag": tag, "pergunta": q, "fontes": fontes,
            "erro": erro, "resposta": content,
        })
        
        print(f"Concluído. len={len(content)} erro={erro}")
        
        # Pausa para evitar 429 Too Many Requests
        if i < len(CASOS_TESTE):
            print(f"Aguardando {PAUSA_SEG}s antes da próxima query...")
            time.sleep(PAUSA_SEG)
            
    return registros

def gerar_relatorio(registros: list[dict]) -> None:
    TRACES_DIR.mkdir(parents=True, exist_ok=True)
    
    L = [
        "# Relatório de Avaliação Crítica: 10 Casos de Teste",
        "",
        "Este relatório documenta os 10 casos de teste descritos na Seção 7 do Relatório Técnico, "
        "abrangendo o uso do Agente RAG (busca vetorial estrita) e do Agente Web (Tool Calling).",
        ""
    ]
    
    for i, r in enumerate(registros, 1):
        falhou = "tool_use_failed" in (r["resposta"] or "") or r["erro"]
        
        L.append(f"## {r['tag']} (Agente {r['tipo'].upper()})")
        L.append(f"**Pergunta:** {r['pergunta']}\n")
        
        if r['tipo'] == "rag":
            str_fontes = ", ".join(r["fontes"]) or "(nenhum)"
            L.append(f"- Artigos recuperados (RAG): {str_fontes}")
            
        L.append(f"- Status: {'FALHA' if falhou else 'sucesso'} | {len(r['resposta'])} caracteres\n")
        
        if r["erro"]:
            L.append(f"**Erro Capturado:** `{r['erro']}`\n")
            
        if not falhou:
            L += ["<details><summary>Resposta Gerada</summary>", "", r["resposta"], "", "</details>", ""]
            
        L.append("---")
        L.append("")
        
    caminho = TRACES_DIR / "relatorio_casos_teste.md"
    caminho.write_text("\n".join(L), encoding="utf-8")
    print(f"\n✅ Relatório completo salvo em {caminho}")

if __name__ == "__main__":
    resultados = rodar()
    gerar_relatorio(resultados)
