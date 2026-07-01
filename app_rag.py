"""Front-end web (Streamlit) para o Pesquisador RAG Multi-Artigos (Tema 10).

Interface separada da do Módulo 1 (``app.py``). Aqui o agente responde sobre um
conjunto FIXO de PDFs ingeridos numa base vetorial (RAG), citando a origem de
cada afirmação.

Para rodar:
    streamlit run app_rag.py
"""

from datetime import datetime
from pathlib import Path

import streamlit as st

# Reaproveita a lógica de negócio do agente RAG.
import agent_rag as core

PASTA_RESULTADOS = Path("resultados")

EXEMPLOS = {
    "Comparar metodologias": (
        "Compare as metodologias dos artigos sobre aprendizado federado. "
        "Quais datasets usam, no que divergem e quais lacunas apontam?"
    ),
    "Datasets e métricas": (
        "Quais datasets e métricas de avaliação são usados nos experimentos "
        "de aprendizado federado descritos nos artigos?"
    ),
    "Dados não-IID": (
        "O que os artigos dizem sobre dados não-IID e como isso afeta o treinamento?"
    ),
}


# --------------------------------------------------------------------------- #
# Configuração da página
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="Pesquisador RAG Multi-Artigos",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource(show_spinner="Indexando os artigos na base vetorial…")
def preparar_base_cached() -> int:
    """Ingere os PDFs uma única vez por sessão do servidor e devolve o nº de vetores."""
    core.preparar_base()
    return core.vector_db.get_count()


def executar_pesquisa(pergunta: str):
    """Roda o agente RAG e devolve (conteúdo, artigos_recuperados, falhou)."""
    resposta = core.agent.run(pergunta)
    conteudo = resposta.content or ""
    falhou = "tool_use_failed" in conteudo or conteudo.strip().startswith('{"error"')
    artigos = [] if falhou else core.fontes_recuperadas(pergunta)
    return conteudo, artigos, falhou


# --------------------------------------------------------------------------- #
# Estado
# --------------------------------------------------------------------------- #
for chave, valor in {
    "resultado": None, "pergunta_atual": "", "tema_input": "", "artigos_fonte": [],
}.items():
    st.session_state.setdefault(chave, valor)


# --------------------------------------------------------------------------- #
# Barra lateral
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.header("⚙️ Configuração")

    tem_chave = bool(core.os.getenv("GROQ_API_KEY"))
    if tem_chave:
        st.success("Chave Groq detectada", icon="✅")
    else:
        st.error("GROQ_API_KEY não encontrada. Defina-a no arquivo `.env`.", icon="⚠️")

    st.caption("**Modelo (LLM)**")
    st.code(core.agent.model.id, language=None)
    st.caption("**Embeddings (local)**")
    st.code(core.EMBED_MODEL, language=None)

    st.divider()
    st.caption("**Artigos na base**")
    pdfs = core.listar_pdfs()
    if pdfs:
        for pdf in pdfs:
            st.markdown(f"📄 `{pdf.name}`")
    else:
        st.warning("Nenhum PDF em `artigos/`. Envie arquivos abaixo.")

    novos = st.file_uploader(
        "Adicionar PDFs de artigos", type="pdf", accept_multiple_files=True
    )
    if novos:
        core.PASTA_ARTIGOS.mkdir(exist_ok=True)
        for arq in novos:
            (core.PASTA_ARTIGOS / arq.name).write_bytes(arq.getbuffer())
        st.cache_resource.clear()  # força reindexar com os novos artigos
        st.success(f"{len(novos)} arquivo(s) adicionados. Reindexando…")
        st.rerun()

    st.divider()
    st.caption("**Exemplos de pergunta**")
    for titulo, texto in EXEMPLOS.items():
        if st.button(titulo, use_container_width=True, key=f"ex_{titulo}"):
            st.session_state.tema_input = texto


# --------------------------------------------------------------------------- #
# Cabeçalho
# --------------------------------------------------------------------------- #
st.title("🧠 Pesquisador RAG Multi-Artigos")
st.markdown(
    "Agente que **lê um conjunto de artigos em PDF** e responde a perguntas "
    "**comparativas** sobre eles — citando a origem de cada afirmação. "
    "Faça perguntas de alto nível sobre metodologias, datasets, resultados e lacunas."
)

# Garante a base pronta (ingestão idempotente, cacheada).
n_vetores = preparar_base_cached() if core.listar_pdfs() else 0
if n_vetores:
    st.caption(f"Base vetorial pronta: **{n_vetores} trechos** indexados de "
               f"**{len(core.listar_pdfs())} artigo(s)**.")

pergunta = st.text_area(
    "Pergunta sobre os artigos",
    value=st.session_state.tema_input,
    height=120,
    placeholder="Ex.: Compare as metodologias dos artigos e aponte as lacunas.",
)

col_run, col_clear = st.columns([1, 1])
with col_run:
    rodar = st.button(
        "🔍 Pesquisar", type="primary", use_container_width=True,
        disabled=not tem_chave or not core.listar_pdfs(),
    )
with col_clear:
    if st.button("🧹 Limpar", use_container_width=True):
        st.session_state.resultado = None
        st.session_state.pergunta_atual = ""
        st.session_state.tema_input = ""
        st.session_state.artigos_fonte = []
        st.rerun()


# --------------------------------------------------------------------------- #
# Execução
# --------------------------------------------------------------------------- #
if rodar:
    pergunta = (pergunta or "").strip()
    if not pergunta:
        st.warning("Digite uma pergunta antes de continuar.")
    else:
        with st.status("Consultando os artigos e redigindo…", expanded=True) as status:
            st.write("🔎 Buscando trechos relevantes na base vetorial…")
            try:
                conteudo, artigos, falhou = executar_pesquisa(pergunta)
                if falhou:
                    status.update(label="O modelo falhou a chamada de ferramenta",
                                  state="error")
                    st.session_state.resultado = None
                    st.warning(
                        "O modelo produziu uma chamada de ferramenta inválida "
                        "(`tool_use_failed`) — comum em perguntas muito vagas. "
                        "Tente reformular de forma mais específica."
                    )
                else:
                    st.session_state.resultado = conteudo
                    st.session_state.pergunta_atual = pergunta
                    st.session_state.artigos_fonte = artigos
                    caminho = core.salvar_resultado(pergunta, conteudo)
                    st.write(f"💾 Resultado salvo em `{caminho}`")
                    status.update(label="Pesquisa concluída!", state="complete")
            except Exception as e:
                status.update(label="Falha na pesquisa", state="error")
                st.error(f"Ocorreu um erro:\n\n```\n{e}\n```")


# --------------------------------------------------------------------------- #
# Resultado
# --------------------------------------------------------------------------- #
if st.session_state.resultado:
    st.divider()
    if st.session_state.pergunta_atual:
        st.caption(f"**Pergunta:** {st.session_state.pergunta_atual}")
    if st.session_state.artigos_fonte:
        st.caption("**Artigos recuperados:** "
                   + ", ".join(f"`{a}`" for a in st.session_state.artigos_fonte))

    st.markdown(st.session_state.resultado)

    st.download_button(
        "⬇️ Baixar resultado (.md)",
        data=st.session_state.resultado,
        file_name=f"pesquisa-rag-{datetime.now():%Y%m%d-%H%M%S}.md",
        mime="text/markdown",
    )
