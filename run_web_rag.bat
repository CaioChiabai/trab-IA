@echo off

if not exist ".venv" (
    echo Criando ambiente virtual...
    python -m venv .venv
)

call .venv\Scripts\activate

echo Instalando dependencias...
pip install -r requirements.txt --quiet

echo.
echo Iniciando interface web do pesquisador RAG multi-artigos...
echo (le os PDFs da pasta artigos\)
echo.
streamlit run app_rag.py

pause
