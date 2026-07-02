@echo off

if not exist ".venv" (
    echo Criando ambiente virtual...
    python -m venv .venv
)

call .venv\Scripts\activate

echo Instalando dependencias...
pip install -r requirements.txt --quiet

echo.
echo Iniciando pesquisador RAG multi-artigos (le os PDFs da pasta data\artigos\)...
echo.
python -m src.agents.rag

pause
