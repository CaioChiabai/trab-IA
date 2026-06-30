"""Front-end web (Streamlit) para o Pesquisador Bibliográfico.

Reaproveita o agente e as funções utilitárias já definidos em ``agent.py``,
expondo a mesma capacidade do terminal numa interface visual e apresentável.

Para rodar:
    streamlit run app.py
"""

import os
from datetime import datetime
from pathlib import Path

import streamlit as st

# Reaproveita a lógica de negócio já pronta (o import é seguro graças ao
# guard ``if __name__ == "__main__"`` em agent.py — main() não é executado aqui).
from agent import agent, salvar_resultado

PASTA_RESULTADOS = Path("resultados")

EXEMPLOS = {
    "Aprendizado federado": (
        "Quais são os principais artigos sobre aprendizado federado (federated "
        "learning)? Resuma as metodologias utilizadas e aponte lacunas na literatura."
    ),
    "LLMs e alucinação": (
        "Quais artigos recentes tratam de alucinação em grandes modelos de "
        "linguagem (LLMs)? Compare as abordagens de mitigação propostas."
    ),
    "Visão computacional médica": (
        "Quais são os trabalhos relevantes sobre uso de deep learning para "
        "diagnóstico por imagens médicas? Aponte datasets e lacunas."
    ),
}


# --------------------------------------------------------------------------- #
# Configuração da página
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="Pesquisador Bibliográfico",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


def executar_pesquisa(pergunta: str) -> str:
    """Roda o agente e retorna o conteúdo da resposta (string Markdown)."""
    resultado = agent.run(pergunta)
    return resultado.content or ""


# --------------------------------------------------------------------------- #
# Estado
# --------------------------------------------------------------------------- #
if "resultado" not in st.session_state:
    st.session_state.resultado = None
if "pergunta_atual" not in st.session_state:
    st.session_state.pergunta_atual = ""
if "tema_input" not in st.session_state:
    st.session_state.tema_input = ""


# --------------------------------------------------------------------------- #
# Barra lateral
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.header("⚙️ Configuração")

    tem_chave = bool(os.getenv("GROQ_API_KEY"))
    if tem_chave:
        st.success("Chave Groq detectada", icon="✅")
    else:
        st.error(
            "GROQ_API_KEY não encontrada. Defina-a no arquivo `.env`.",
            icon="⚠️",
        )

    modelo = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    st.caption("**Modelo em uso**")
    st.code(modelo, language=None)

    st.divider()
    st.caption("**Exemplos de pesquisa**")
    for titulo, texto in EXEMPLOS.items():
        if st.button(titulo, use_container_width=True, key=f"ex_{titulo}"):
            st.session_state.tema_input = texto

    st.divider()
    with st.expander("📁 Pesquisas salvas"):
        if PASTA_RESULTADOS.exists():
            arquivos = sorted(
                PASTA_RESULTADOS.glob("*.md"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            if arquivos:
                for arq in arquivos:
                    if st.button(
                        f"📄 {arq.stem}",
                        use_container_width=True,
                        key=f"hist_{arq.name}",
                    ):
                        st.session_state.resultado = arq.read_text(encoding="utf-8")
                        st.session_state.pergunta_atual = arq.stem
            else:
                st.caption("Nenhuma pesquisa salva ainda.")
        else:
            st.caption("Nenhuma pesquisa salva ainda.")


# --------------------------------------------------------------------------- #
# Cabeçalho
# --------------------------------------------------------------------------- #
st.title("📚 Pesquisador Bibliográfico")
st.markdown(
    "Agente de IA que **busca, resume e compara artigos científicos** sobre o "
    "tema informado. Digite uma pergunta de pesquisa abaixo e receba um "
    "panorama estruturado da literatura, com fontes citáveis."
)

pergunta = st.text_area(
    "Tema ou pergunta de pesquisa",
    value=st.session_state.tema_input,
    height=120,
    placeholder=(
        "Ex.: Quais são os principais artigos sobre aprendizado federado? "
        "Resuma as metodologias e aponte lacunas na literatura."
    ),
)

col_run, col_clear = st.columns([1, 1])
with col_run:
    rodar = st.button(
        "🔍 Pesquisar", type="primary", use_container_width=True, disabled=not tem_chave
    )
with col_clear:
    if st.button("🧹 Limpar", use_container_width=True):
        st.session_state.resultado = None
        st.session_state.pergunta_atual = ""
        st.session_state.tema_input = ""
        st.rerun()


# --------------------------------------------------------------------------- #
# Execução
# --------------------------------------------------------------------------- #
if rodar:
    pergunta = (pergunta or "").strip()
    if not pergunta:
        st.warning("Digite um tema ou pergunta de pesquisa antes de continuar.")
    else:
        with st.status("Pesquisando e redigindo…", expanded=True) as status:
            st.write("🔎 Consultando fontes na web e analisando resultados…")
            try:
                conteudo = executar_pesquisa(pergunta)
                st.session_state.resultado = conteudo
                st.session_state.pergunta_atual = pergunta
                caminho = salvar_resultado(pergunta, conteudo)
                st.write(f"💾 Resultado salvo em `{caminho}`")
                status.update(label="Pesquisa concluída!", state="complete")
            except Exception as e:
                status.update(label="Falha na pesquisa", state="error")
                st.error(f"Ocorreu um erro ao executar a pesquisa:\n\n```\n{e}\n```")


# --------------------------------------------------------------------------- #
# Resultado
# --------------------------------------------------------------------------- #
if st.session_state.resultado:
    st.divider()
    if st.session_state.pergunta_atual:
        st.caption(f"**Pergunta:** {st.session_state.pergunta_atual}")

    st.markdown(st.session_state.resultado)

    st.download_button(
        "⬇️ Baixar resultado (.md)",
        data=st.session_state.resultado,
        file_name=f"pesquisa-{datetime.now():%Y%m%d-%H%M%S}.md",
        mime="text/markdown",
    )
