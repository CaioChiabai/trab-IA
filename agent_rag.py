"""Pesquisador Bibliográfico Multi-Artigos — Tema 10 (RAG multi-documento).

Este agente ingere um conjunto de artigos científicos em PDF numa base de
conhecimento vetorial (LanceDB, com embeddings locais via FastEmbed) e responde a
perguntas comparativas de alto nível sobre metodologias, datasets, resultados e
lacunas — citando a origem de cada afirmação (citation grounding).

Coloque os PDFs dos artigos na pasta ``artigos/`` e execute::

    python agent_rag.py

Este módulo é COMPLEMENTAR ao ``agent.py`` (pesquisador por busca na web): o
``agent.py`` busca fontes na internet; este aqui responde sobre um conjunto FIXO
de PDFs já fornecidos, como pede o Tema 10 (RAG multi-documento).
"""

import os
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.groq import Groq
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.embedder.fastembed import FastEmbedEmbedder
from agno.knowledge.reader.pdf_reader import PDFReader
from agno.vectordb.lancedb import LanceDb, SearchType
from rich.console import Console
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

load_dotenv()

console = Console()

PASTA_ARTIGOS = Path("artigos")
PASTA_VECTOR = Path("vectordb")
PASTA_RESULTADOS = Path("resultados")


# --------------------------------------------------------------------------- #
# Base de conhecimento (RAG)
# --------------------------------------------------------------------------- #
# Banco vetorial local (LanceDB) — não precisa de servidor. Os embeddings são
# gerados LOCALMENTE pelo FastEmbed (modelo ONNX), sem chave de API nem cota:
# usamos um modelo multilíngue porque as perguntas são em português e os
# artigos, em inglês (recuperação cross-lingual).
EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

vector_db = LanceDb(
    uri=str(PASTA_VECTOR),
    table_name="artigos",
    search_type=SearchType.vector,
    embedder=FastEmbedEmbedder(id=EMBED_MODEL, dimensions=384),
)

knowledge = Knowledge(
    name="Artigos científicos",
    description="Coleção de artigos científicos ingeridos para análise comparativa.",
    vector_db=vector_db,
    max_results=10,
)


def listar_pdfs() -> list[Path]:
    """Retorna os PDFs disponíveis na pasta de artigos."""
    return sorted(PASTA_ARTIGOS.glob("*.pdf"))


def preparar_base() -> list[str]:
    """Ingere na base vetorial todos os PDFs ainda não indexados.

    Usa ``skip_if_exists`` (comparação por hash de conteúdo), de modo que
    reexecuções não reprocessam nem gastam embeddings com artigos já indexados.
    Retorna a lista de nomes de artigos indexados nesta chamada.
    """
    pdfs = listar_pdfs()
    if not pdfs:
        console.print(
            f"[yellow]Nenhum PDF encontrado em '{PASTA_ARTIGOS}/'. "
            f"Adicione os artigos e rode novamente.[/yellow]"
        )
        return []

    indexados: list[str] = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        console=console,
        transient=True,
    ) as progress:
        tarefa = progress.add_task("Indexando artigos", total=len(pdfs))
        for pdf in pdfs:
            knowledge.add_content(
                name=pdf.stem,
                path=str(pdf),
                metadata={"arquivo": pdf.name, "artigo": pdf.stem},
                reader=PDFReader(),
                skip_if_exists=True,
            )
            indexados.append(pdf.stem)
            progress.advance(tarefa, 1)
    return indexados


# --------------------------------------------------------------------------- #
# Agente
# --------------------------------------------------------------------------- #
agent = Agent(
    model=Groq(id=os.getenv("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")),
    knowledge=knowledge,
    # RAG "tradicional" (retrieve-then-read): o Agno recupera os trechos relevantes
    # e os injeta no contexto ANTES de chamar o modelo. NÃO usamos tool calling
    # porque o Llama no Groq falha de forma intermitente ('tool_use_failed') ao
    # emitir a chamada de função; injetar o contexto direto é 100% confiável.
    add_knowledge_to_context=True,
    search_knowledge=False,
    markdown=True,
    instructions="""Você é um pesquisador bibliográfico especializado em análise
COMPARATIVA de artigos científicos. Sua base de conhecimento contém um conjunto
FIXO de artigos previamente ingeridos (em PDF). Seu papel é responder perguntas
de alto nível comparando esses artigos entre si.

CONTEXTO FORNECIDO:
- Você recebe, no contexto desta conversa, trechos recuperados automaticamente dos
  artigos ingeridos. Cada trecho indica o arquivo de origem.
- Baseie-se APENAS nesses trechos. Escreva a resposta COMPLETA de uma só vez.
- Na tabela comparativa, procure incluir artigos distintos (evite repetir a mesma fonte).

REGRA FUNDAMENTAL — CITATION GROUNDING (integridade das citações):
- Para CADA afirmação relevante, indique de qual artigo (arquivo/fonte) ela veio.
- NUNCA misture informações de artigos diferentes sem deixar claro a origem de cada uma.
- NUNCA invente autores, anos, datasets, métricas ou resultados. Se a informação
  não estiver nos artigos recuperados, escreva explicitamente
  "não encontrado nos artigos ingeridos".
- Se a pergunta não puder ser respondida com os artigos disponíveis, diga isso
  claramente em vez de fabricar uma resposta.

FORMATO OBRIGATÓRIO DA RESPOSTA (use exatamente estas seções, em Markdown):

# Pesquisa: <pergunta>

## 1. Resumo comparativo
Um ou dois parágrafos sintetizando o que os artigos, em conjunto, dizem sobre o tema.

## 2. Tabela comparativa
Tabela em Markdown com as colunas:
| Artigo (fonte) | Metodologia/abordagem | Dataset(s) | Principais resultados |
Inclua uma linha por artigo relevante à pergunta.

## 3. Metodologias e abordagens
Descreva, em tópicos, as metodologias de cada artigo, sempre citando a fonte.

## 4. Convergências e divergências
Aponte, em tópicos, onde os artigos concordam e onde divergem entre si.

## 5. Lacunas e questões em aberto
Liste as lacunas e questões de pesquisa em aberto mencionadas nos artigos.

## 6. Fontes citadas
Lista dos artigos (arquivos) efetivamente usados para responder.

Responda sempre em português, de forma estruturada e acadêmica.""",
    debug_mode=False,
)


# --------------------------------------------------------------------------- #
# Utilitários de saída
# --------------------------------------------------------------------------- #
def _nome_arquivo(pergunta: str) -> str:
    """Gera um nome de arquivo seguro (sem acentos) a partir da pergunta."""
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
    caminho = PASTA_RESULTADOS / f"{_nome_arquivo(pergunta)}.md"
    cabecalho = f"> **Pergunta de pesquisa:** {pergunta}\n\n---\n\n"
    caminho.write_text(cabecalho + conteudo + "\n", encoding="utf-8")
    return str(caminho)


def fontes_recuperadas(pergunta: str, max_results: int = 10) -> list[str]:
    """Retorna os artigos (arquivos) distintos que a busca vetorial recupera para
    a pergunta — os mesmos trechos que são injetados no contexto do agente."""
    fontes: list[str] = []
    try:
        for doc in knowledge.search(pergunta, max_results=max_results):
            arq = (getattr(doc, "meta_data", None) or {}).get("arquivo")
            if arq and arq not in fontes:
                fontes.append(arq)
    except Exception:
        pass
    return fontes


def executar_pesquisa(pergunta: str):
    """Roda o agente em segundo plano com barra de progresso.

    Retorna uma tupla ``(conteudo, fontes)`` — ``fontes`` é a lista de artigos
    efetivamente recuperados da base vetorial para responder à pergunta."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        futuro = executor.submit(agent.run, pergunta)
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[cyan]consultando os artigos…[/cyan]"),
            console=console,
            transient=True,
        ) as progress:
            tarefa = progress.add_task("Pesquisando e redigindo", total=None)
            while not futuro.done():
                progress.advance(tarefa, 1)
                time.sleep(0.1)
        resposta = futuro.result()

    return (resposta.content or ""), fontes_recuperadas(pergunta)


def _mostrar_fontes(fontes) -> None:
    """Imprime os artigos recuperados da base para a resposta."""
    if not fontes:
        console.print("[dim](nenhum artigo recuperado)[/dim]")
        return
    console.print(f"[bold]Artigos recuperados:[/bold] {len(fontes)}")
    for i, f in enumerate(fontes, 1):
        console.print(f"  [cyan]{i}.[/cyan] {f}")


def main():
    pergunta_padrao = (
        "Compare as metodologias dos artigos sobre aprendizado federado. "
        "Quais datasets usam, no que divergem e quais lacunas apontam?"
    )

    console.rule("[bold]Pesquisador Bibliográfico Multi-Artigos (RAG)[/bold]")

    # 1) Prepara a base vetorial (ingestão idempotente).
    pdfs = listar_pdfs()
    console.print(
        f"[dim]{len(pdfs)} artigo(s) na pasta '{PASTA_ARTIGOS}/'.[/dim]"
    )
    preparar_base()

    if not pdfs:
        return

    # 2) Recebe a pergunta.
    console.print("\nDigite uma pergunta comparativa sobre os artigos.")
    console.print(
        "[dim](Enter para usar a pergunta de exemplo sobre aprendizado federado.)[/dim]\n"
    )
    pergunta = input("Pergunta> ").strip()
    if not pergunta:
        pergunta = pergunta_padrao
        console.print(f"\n[dim]Usando pergunta de exemplo:[/dim]\n{pergunta}\n")

    # 3) Executa.
    console.print()
    conteudo, fontes = executar_pesquisa(pergunta)

    console.rule("[bold green]Resultado[/bold green]")
    console.print(Markdown(conteudo))
    console.rule("[bold]Fontes[/bold]")
    _mostrar_fontes(fontes)
    console.rule()

    caminho = salvar_resultado(pergunta, conteudo)
    console.print(f"[green]✓ Resultado salvo em:[/green] {caminho}")


if __name__ == "__main__":
    main()
