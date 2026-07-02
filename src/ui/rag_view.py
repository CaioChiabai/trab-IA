"""Interface (Streamlit) do modo de PESQUISA NOS PDFs (RAG).

Exposto como ``render()`` e despachado por ``app.py``. Reutiliza a lógica de
``src/agents/rag.py``: responde sobre um conjunto de PDFs ingeridos numa base
vetorial, citando a origem de cada afirmação.
"""

from datetime import datetime

import streamlit as st

from src.config import tem_chave_groq
# Reaproveita a lógica de negócio do agente RAG.
from src.agents import rag as core

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

# Chaves de estado deste modo (limpas ao trocar de modo, em app.py).
DEFAULTS = {"resultado": None, "pergunta_atual": "", "tema_input": "", "artigos_fonte": []}


@st.cache_resource(show_spinner="Indexando os artigos na base vetorial…")
def preparar_base_cached() -> int:
    """Ingere os PDFs uma única vez por sessão do servidor e devolve o nº de vetores."""
    core.preparar_base()
    return core.vector_db.get_count()


def executar_pesquisa(pergunta: str):
    """Roda o agente RAG (recuperação balanceada por artigo) e devolve
    (conteúdo, artigos_recuperados, falhou)."""
    conteudo, artigos = core.rodar_agente(pergunta)
    falhou = "tool_use_failed" in conteudo or conteudo.strip().startswith('{"error"')
    return conteudo, ([] if falhou else artigos), falhou


def render():
    for chave, valor in DEFAULTS.items():
        st.session_state.setdefault(chave, valor)

    # ─── sidebar ────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### ⚙️ Configuração")
        tem_chave = tem_chave_groq()
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
                c1, c2 = st.columns([0.85, 0.15], vertical_alignment="center")
                with c1:
                    st.markdown(f"📄 `{pdf.name}`")
                with c2:
                    if st.button("−", key=f"del_{pdf.name}",
                                 type="tertiary", help=f"Remover {pdf.name} da base"):
                        core.remover_artigo(pdf.name)
                        st.cache_resource.clear()  # força reindexar sem o artigo
                        st.session_state.resultado = None
                        st.toast(f"{pdf.name} removido da base.", icon="🗑️")
                        st.rerun()

            if st.button("🧹 Limpar toda a base", use_container_width=True,
                         help="Remove todos os artigos e seus vetores"):
                st.session_state.confirmar_limpar = True

            if st.session_state.get("confirmar_limpar"):
                st.warning("Remover **todos** os artigos? Esta ação não pode ser desfeita.")
                cc1, cc2 = st.columns(2)
                with cc1:
                    if st.button("✅ Confirmar", use_container_width=True):
                        n = core.limpar_base()
                        st.cache_resource.clear()
                        st.session_state.confirmar_limpar = False
                        st.session_state.resultado = None
                        st.toast(f"{n} artigo(s) removidos.", icon="🧹")
                        st.rerun()
                with cc2:
                    if st.button("Cancelar", use_container_width=True):
                        st.session_state.confirmar_limpar = False
                        st.rerun()
        else:
            st.warning("Nenhum PDF em `artigos/`. Envie arquivos abaixo.")

        novos = st.file_uploader("Adicionar PDFs de artigos", type="pdf", accept_multiple_files=True)
        if novos:
            core.PASTA_ARTIGOS.mkdir(parents=True, exist_ok=True)
            for arq in novos:
                (core.PASTA_ARTIGOS / arq.name).write_bytes(arq.getbuffer())
            st.cache_resource.clear()  # força reindexar com os novos artigos
            st.success(f"{len(novos)} arquivo(s) adicionados. Reindexando…")
            st.rerun()

        st.divider()
        st.caption("**Exemplos de pergunta**")
        for titulo, texto in EXEMPLOS.items():
            if st.button(titulo, use_container_width=True, key=f"rag_ex_{titulo}"):
                st.session_state.tema_input = texto
                st.rerun()

    # ─── cabeçalho ──────────────────────────────────────────────────────────
    st.markdown(
        """
<div class="hero-title">📚 Pesquisa nos PDFs (RAG)</div>
<div class="hero-subtitle">
  Agente que <strong>lê seus artigos em PDF</strong> e responde a perguntas
  comparativas sobre eles — citando a origem de cada afirmação.
</div>
""",
        unsafe_allow_html=True,
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
        if st.button("🧹 Limpar", use_container_width=True, key="rag_limpar"):
            for k, v in DEFAULTS.items():
                st.session_state[k] = v
            st.rerun()

    # ─── execução ───────────────────────────────────────────────────────────
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
                        status.update(label="O modelo falhou a chamada de ferramenta", state="error")
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
                    msg = str(e).lower()
                    if any(t in msg for t in ("rate_limit", "tokens per minute", "too large", "413")):
                        st.warning(
                            "**Limite de tokens por minuto do Groq atingido** "
                            "(free-tier).\n\n"
                            "O que fazer:\n"
                            "- Aguarde cerca de 1 minuto e tente de novo;\n"
                            "- Reduza o número de artigos na base (remova os que não "
                            "forem relevantes à pergunta);\n"
                            "- Ou use um modelo com limite maior definindo `GROQ_MODEL_RAG` "
                            "no arquivo `.env`."
                        )
                    else:
                        st.error(f"Ocorreu um erro:\n\n```\n{e}\n```")

    # ─── resultado ──────────────────────────────────────────────────────────
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
