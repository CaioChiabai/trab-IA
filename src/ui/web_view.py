"""Interface (Streamlit) do modo de PESQUISA NA WEB.

Exposto como ``render()`` e despachado por ``app.py``. Reutiliza a lógica de
``src/agents/web.py`` (busca real na web via DuckDuckGo) com feedback
progressivo, cards de fontes clicáveis e exibição de métricas.
"""

import html
from datetime import datetime

import streamlit as st

from src.config import PASTA_RESULTADOS, GROQ_MODEL_WEB, tem_chave_groq
from src.agents import web as agent_module
from src.agents.web import agent
from src.utils import salvar_resultado

_CSS = """
<style>
.hero-title {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 2.6rem; font-weight: 800; line-height: 1.2; margin-bottom: 0.3rem;
}
.hero-subtitle { color: #6b7280; font-size: 1rem; margin-bottom: 1.2rem; line-height: 1.6; }
.query-badge {
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: #ede9fe; color: #5b21b6; border-radius: 999px;
    padding: 0.3rem 0.8rem; font-size: 0.82rem; font-weight: 600; margin-bottom: 0.8rem;
}
.fonte-card {
    background: #ffffff; border: 1px solid #e5e7eb; border-left: 4px solid #7c3aed;
    border-radius: 10px; padding: 1rem 1.1rem; margin-bottom: 0.75rem;
    transition: box-shadow 0.2s ease;
}
.fonte-card:hover { box-shadow: 0 4px 14px rgba(124, 58, 237, 0.13); border-left-color: #5b21b6; }
.fonte-titulo { font-weight: 700; font-size: 0.92rem; color: #111827; margin-bottom: 0.3rem; }
.fonte-trecho {
    color: #6b7280; font-size: 0.82rem; line-height: 1.55; margin-bottom: 0.5rem;
    display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.fonte-link a { color: #7c3aed; font-size: 0.8rem; font-weight: 600; text-decoration: none; }
.fonte-link a:hover { text-decoration: underline; }
.fonte-num {
    display: inline-block; background: #7c3aed; color: #fff; border-radius: 50%;
    width: 1.4rem; height: 1.4rem; line-height: 1.4rem; text-align: center;
    font-size: 0.72rem; font-weight: 700; margin-right: 0.4rem; flex-shrink: 0;
}
</style>
"""

EXEMPLOS = {
    "Aprendizado Federado": (
        "Quais são os principais artigos sobre aprendizado federado (federated "
        "learning)? Resuma as metodologias utilizadas e aponte lacunas na literatura."
    ),
    "LLMs e Alucinação": (
        "Quais artigos recentes tratam de alucinação em grandes modelos de "
        "linguagem (LLMs)? Compare as abordagens de mitigação propostas."
    ),
    "Deep Learning Médico": (
        "Quais são os trabalhos relevantes sobre uso de deep learning para "
        "diagnóstico por imagens médicas? Aponte datasets e lacunas."
    ),
    "Transformers em NLP": (
        "Quais os artigos seminais sobre a arquitetura Transformer e suas "
        "variações em NLP? Resuma as principais contribuições."
    ),
    "Reinforcement Learning": (
        "Quais os principais avanços em reinforcement learning aplicado a jogos "
        "e robótica? Cite trabalhos e compare abordagens."
    ),
}

# Chaves de estado deste modo (limpas ao trocar de modo, em app.py).
DEFAULTS = {
    "resultado": None,
    "pergunta_atual": "",
    "tema_input": "",
    "fontes": [],
    "metricas": {},
}


def _executar(pergunta: str, write_fn):
    """Roda o agente injetando callback de progresso no módulo agent."""
    agent_module._sources_collected = []
    agent_module._progress_callback = lambda msg: write_fn(msg)
    try:
        resultado = agent.run(pergunta)
        conteudo = resultado.content or ""
    finally:
        agent_module._progress_callback = None

    fontes = list({f["url"]: f for f in agent_module._sources_collected if f.get("url")}.values())
    agent_module._sources_collected = []
    return conteudo, fontes


def render():
    st.markdown(_CSS, unsafe_allow_html=True)

    for k, v in DEFAULTS.items():
        st.session_state.setdefault(k, v)

    # ─── sidebar ────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### ⚙️ Configuração")
        tem_chave = tem_chave_groq()
        modelo = GROQ_MODEL_WEB
        if tem_chave:
            st.success("API Groq conectada", icon="✅")
        else:
            st.error("**GROQ_API_KEY** não encontrada.\n\nConfigure no arquivo `.env`.", icon="⚠️")
        st.caption("**Modelo ativo**")
        st.code(modelo, language=None)

        st.divider()
        st.caption("**Exemplos de pesquisa**")
        for titulo, texto in EXEMPLOS.items():
            if st.button(f"📖 {titulo}", use_container_width=True, key=f"web_ex_{titulo}"):
                st.session_state.tema_input = texto
                st.rerun()

        st.divider()
        with st.expander("🕐 Pesquisas salvas"):
            arquivos = sorted(
                PASTA_RESULTADOS.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True,
            ) if PASTA_RESULTADOS.exists() else []
            if arquivos:
                for arq in arquivos[:12]:
                    mtime = datetime.fromtimestamp(arq.stat().st_mtime).strftime("%d/%m %H:%M")
                    label = arq.stem[:28] + ("…" if len(arq.stem) > 28 else "")
                    c1, c2 = st.columns([5, 2])
                    with c1:
                        if st.button(f"📄 {label}", use_container_width=True, key=f"web_hist_{arq.name}"):
                            st.session_state.resultado = arq.read_text(encoding="utf-8")
                            st.session_state.pergunta_atual = arq.stem
                            st.session_state.fontes = []
                            st.session_state.metricas = {}
                    with c2:
                        st.caption(mtime)
            else:
                st.caption("Nenhuma pesquisa salva ainda.")

    # ─── cabeçalho ──────────────────────────────────────────────────────────
    st.markdown(
        """
<div class="hero-title">🌐 Pesquisa na Web</div>
<div class="hero-subtitle">
  Agente de IA que <strong>busca, resume e compara</strong> artigos científicos
  na internet — fontes reais, citáveis e clicáveis.
</div>
""",
        unsafe_allow_html=True,
    )

    pergunta = st.text_area(
        "Tema ou pergunta de pesquisa",
        value=st.session_state.tema_input,
        height=110,
        placeholder=(
            "Ex.: Quais são os principais artigos sobre aprendizado federado? "
            "Resuma as metodologias e aponte lacunas na literatura."
        ),
        help=(
            "Escreva uma pergunta de pesquisa clara. "
            "O agente fará até 4 buscas específicas e estruturará os resultados."
        ),
    )

    col_run, col_clear, _ = st.columns([2, 1, 3])
    with col_run:
        rodar = st.button("🔍 Pesquisar", type="primary", use_container_width=True, disabled=not tem_chave)
    with col_clear:
        if st.button("🧹 Limpar", use_container_width=True, key="web_limpar"):
            for k, v in DEFAULTS.items():
                st.session_state[k] = v
            st.rerun()

    # ─── execução ───────────────────────────────────────────────────────────
    if rodar:
        pergunta_limpa = (pergunta or "").strip()
        if not pergunta_limpa:
            st.warning("✏️ Digite um tema ou pergunta de pesquisa antes de continuar.")
        else:
            with st.status("🔄 Iniciando pesquisa…", expanded=True) as status:
                st.write("🧠 Analisando a pergunta de pesquisa…")
                try:
                    conteudo, fontes = _executar(pergunta_limpa, st.write)
                    st.write("📝 Organizando e redigindo o relatório final…")
                    caminho = salvar_resultado(pergunta_limpa, conteudo)
                    st.write(f"💾 Salvo em `{caminho}`")
                    status.update(label="✅ Pesquisa concluída!", state="complete")

                    st.session_state.resultado = conteudo
                    st.session_state.pergunta_atual = pergunta_limpa
                    st.session_state.fontes = fontes
                    st.session_state.metricas = {
                        "palavras": len(conteudo.split()),
                        "fontes": len(fontes),
                    }
                except Exception as exc:
                    status.update(label="❌ Falha na pesquisa", state="error")
                    st.error(f"Erro ao executar a pesquisa:\n\n```\n{exc}\n```")

    # ─── resultado ──────────────────────────────────────────────────────────
    if st.session_state.resultado:
        st.divider()
        if st.session_state.pergunta_atual:
            st.markdown(
                f'<div class="query-badge">📋 {html.escape(st.session_state.pergunta_atual)}</div>',
                unsafe_allow_html=True,
            )

        m = st.session_state.metricas
        if m:
            c1, c2, c3 = st.columns(3)
            c1.metric("📄 Palavras no relatório", f"{m.get('palavras', 0):,}".replace(",", "."))
            c2.metric("🌐 Fontes únicas coletadas", m.get("fontes", 0))
            c3.metric("🤖 Motor de busca", "DuckDuckGo")

        st.divider()
        st.markdown(st.session_state.resultado)

        fontes = st.session_state.fontes
        if fontes:
            st.divider()
            st.markdown("### 🔗 Fontes encontradas")
            st.caption(
                f"{len(fontes)} página(s) coletada(s) durante a pesquisa — "
                "clique nos links para acessar as fontes originais."
            )
            cols = st.columns(2)
            for i, fonte in enumerate(fontes):
                titulo = fonte.get("titulo") or "Sem título"
                url = fonte.get("url") or "#"
                trecho = fonte.get("trecho") or ""
                trecho_curto = trecho[:180] + ("…" if len(trecho) > 180 else "")
                # Escapa dados vindos da web antes de injetar no HTML.
                titulo_s = html.escape(titulo)
                trecho_s = html.escape(trecho_curto)
                url_s = html.escape(url, quote=True)
                with cols[i % 2]:
                    st.markdown(
                        f"""
<div class="fonte-card">
  <div style="display:flex;align-items:flex-start;gap:0.5rem;">
    <span class="fonte-num">{i + 1}</span>
    <div>
      <div class="fonte-titulo">{titulo_s}</div>
      <div class="fonte-trecho">{trecho_s}</div>
      <div class="fonte-link"><a href="{url_s}" target="_blank" rel="noopener">🔗 Acessar fonte →</a></div>
    </div>
  </div>
</div>
""",
                        unsafe_allow_html=True,
                    )

        st.divider()
        col_dl, _ = st.columns([1, 3])
        with col_dl:
            st.download_button(
                "⬇️ Baixar relatório (.md)",
                data=st.session_state.resultado,
                file_name=f"pesquisa-{datetime.now():%Y%m%d-%H%M%S}.md",
                mime="text/markdown",
                use_container_width=True,
            )
