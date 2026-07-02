@echo off

if not exist ".venv" (
    echo Criando ambiente virtual...
    python -m venv .venv
)

call .venv\Scripts\activate

echo Instalando dependencias...
pip install -r requirements.txt --quiet

echo.
echo Iniciando agente (busca na web)...
echo.
python -m src.agents.web

pause
