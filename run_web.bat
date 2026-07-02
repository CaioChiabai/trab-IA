@echo off

if not exist ".venv" (
    echo Criando ambiente virtual...
    python -m venv .venv
)

call .venv\Scripts\activate

echo Instalando dependencias...
pip install -r requirements.txt --quiet

echo.
echo Iniciando interface web (escolha o modo na tela: Web ou PDFs/RAG)...
echo.
streamlit run app.py

pause
