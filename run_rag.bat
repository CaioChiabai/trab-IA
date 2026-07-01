@echo off

if not exist ".venv" (
    echo Criando ambiente virtual...
    python -m venv .venv
)

call .venv\Scripts\activate

echo Instalando dependencias...
pip install -r requirements.txt --quiet

echo.
echo Iniciando pesquisador RAG multi-artigos (le os PDFs da pasta artigos\)...
echo.
python agent_rag.py

pause
