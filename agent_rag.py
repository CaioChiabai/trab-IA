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


def remover_artigo(nome_pdf: str) -> bool:
    """Remove um artigo da base de conhecimento.

    Apaga tanto os vetores indexados no LanceDB (pelo nome do artigo, que é o
    ``stem`` usado na ingestão) quanto o próprio arquivo PDF em ``artigos/``.
    Sem isso, deletar apenas o PDF deixaria os vetores órfãos na base, e o
    agente continuaria recuperando trechos do artigo "removido".

    ``nome_pdf`` é o nome do arquivo (ex.: ``fedavg-mcmahan-2017.pdf``).
    Retorna ``True`` se o arquivo foi de fato apagado do disco.
    """
    stem = Path(nome_pdf).stem
    # Remove os vetores. Tenta por nome (usado na ingestão) e, por garantia,
    # também por metadata do arquivo — assim cobrimos ambos os esquemas.
    for tentativa in (
        lambda: knowledge.remove_vectors_by_name(stem),
        lambda: vector_db.delete_by_metadata({"arquivo": nome_pdf}),
    ):
        try:
            tentativa()
        except Exception:
            pass

    caminho = PASTA_ARTIGOS / nome_pdf
    if caminho.exists():
        caminho.unlink()
        return True
    return False


def limpar_base() -> int:
    """Remove TODOS os artigos: apaga os vetores e os PDFs da pasta.

    Útil quando o usuário quer descartar os artigos de exemplo e montar uma
    base sobre outro assunto do zero. Retorna quantos artigos foram removidos.
    """
    pdfs = listar_pdfs()
    for pdf in pdfs:
        remover_artigo(pdf.name)
    return len(pdfs)


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
    # RAG "retrieve-then-read" com recuperação BALANCEADA por artigo: montamos o
    # contexto manualmente (ver montar_contexto), garantindo trechos de TODOS os
    # artigos. Não usamos tool calling (o Llama no Groq falha com 'tool_use_failed')
    # nem a injeção automática do Agno (que concentra o top-k em poucos artigos).
    add_knowledge_to_context=False,
    search_knowledge=False,
    markdown=True,
    instructions="""Você é um pesquisador bibliográfico especializado em análise
COMPARATIVA de artigos científicos. Sua base de conhecimento contém um conjunto
FIXO de artigos previamente ingeridos (em PDF). Seu papel é responder perguntas
de alto nível comparando esses artigos entre si.

CONTEXTO FORNECIDO:
- Você recebe, na própria mensagem, trechos recuperados de CADA artigo da base,
  agrupados por arquivo de origem (linhas "### Artigo: <arquivo>").
- Baseie-se APENAS nesses trechos. Escreva a resposta COMPLETA de uma só vez.
- Na tabela comparativa, inclua UMA LINHA POR ARTIGO fornecido, quando houver
  informação relevante — o objetivo é comparar todos os artigos, não apenas um.

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


def montar_contexto(pergunta: str, por_artigo: int = 3, pool: int = 150):
    """Recuperação BALANCEADA: em vez de pegar apenas o top-k global (que tende a
    concentrar-se num único artigo), recupera os ``por_artigo`` trechos mais
    relevantes de CADA artigo. Assim, todos os artigos entram no contexto.

    Retorna ``(contexto, fontes)``: o texto agrupado por artigo e a lista dos
    arquivos incluídos."""
    selecionados: dict[str, list[str]] = {}
    try:
        for doc in knowledge.search(pergunta, max_results=pool):
            arq = (getattr(doc, "meta_data", None) or {}).get("arquivo")
            if not arq:
                continue
            trechos = selecionados.setdefault(arq, [])
            if len(trechos) < por_artigo:
                trechos.append(doc.content or "")
    except Exception:
        pass

    blocos = []
    for arq, trechos in selecionados.items():
        corpo = "\n\n".join(t.strip() for t in trechos if t.strip())
        blocos.append(f"### Artigo: {arq}\n{corpo}")
    return "\n\n".join(blocos), list(selecionados.keys())


def _mensagem_com_contexto(pergunta: str, contexto: str) -> str:
    return (
        f"{pergunta}\n\n"
        "=== TRECHOS RECUPERADOS DOS ARTIGOS (baseie-se APENAS nestes) ===\n\n"
        f"{contexto}"
    )


def rodar_agente(pergunta: str):
    """Monta o contexto balanceado, roda o agente e retorna ``(conteudo, fontes)``."""
    contexto, fontes = montar_contexto(pergunta)
    resposta = agent.run(_mensagem_com_contexto(pergunta, contexto))
    return (resposta.content or ""), fontes


def executar_pesquisa(pergunta: str):
    """Versão para a CLI: roda o agente em segundo plano com barra de progresso.
    Retorna ``(conteudo, fontes)``."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        futuro = executor.submit(rodar_agente, pergunta)
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
        conteudo, fontes = futuro.result()

    return conteudo, fontes


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
