"""Pesquisador Bibliográfico IA — aplicação Streamlit unificada.

Um único app com DOIS modos, escolhidos na própria tela:

  🌐 Pesquisa na Web  → busca fontes reais na internet (src/ui/web_view + src/agents/web)
  📚 Pesquisa nos PDFs → responde sobre PDFs enviados, via RAG (src/ui/rag_view + src/agents/rag)

Rode com:
    streamlit run app.py
"""

import streamlit as st

st.set_page_config(
    page_title="Pesquisador Bibliográfico IA",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS do cabeçalho, compartilhado pelos dois modos.
st.markdown(
    """
<style>
.hero-title {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    font-size: 2.6rem; font-weight: 800; line-height: 1.2; margin-bottom: 0.3rem;
}
.hero-subtitle { color: #6b7280; font-size: 1rem; margin-bottom: 1.2rem; line-height: 1.6; }
</style>
""",
    unsafe_allow_html=True,
)

MODOS = {
    "🌐 Pesquisa na Web": "web",
    "📚 Pesquisa nos PDFs (RAG)": "rag",
}

# ─── seletor de modo (topo da sidebar) ──────────────────────────────────────
with st.sidebar:
    st.markdown("## 📚 Pesquisador Bibliográfico IA")
    escolha = st.radio(
        "Modo de pesquisa",
        list(MODOS.keys()),
        key="modo_pesquisa",
        help=(
            "**Web**: busca artigos reais na internet sobre qualquer tema.\n\n"
            "**PDFs (RAG)**: responde com base nos PDFs que você enviar."
        ),
    )
    modo = MODOS[escolha]
    st.divider()

# Ao trocar de modo, limpa o estado compartilhado para não vazar resultado de um
# modo no outro (ambos usam 'resultado', 'pergunta_atual', 'tema_input').
if st.session_state.get("_modo_ativo") != modo:
    for chave in ("resultado", "pergunta_atual", "tema_input",
                  "fontes", "metricas", "artigos_fonte", "confirmar_limpar"):
        st.session_state.pop(chave, None)
    st.session_state._modo_ativo = modo

# Importação preguiçosa: o modo RAG carrega embeddings/índice (pesado), então só
# é importado quando de fato selecionado — quem usa só a Web não paga esse custo.
if modo == "web":
    from src.ui import web_view
    web_view.render()
else:
    from src.ui import rag_view
    rag_view.render()
