import os

from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.duckduckgo import DuckDuckGoTools

load_dotenv()

agent = Agent(
    model=Groq(id=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")),
    tools=[DuckDuckGoTools(enable_news=False)],
    instructions="""Você é um pesquisador bibliográfico especializado em artigos científicos.
Seu papel é buscar, resumir e comparar artigos acadêmicos sobre um tema dado pelo usuário.
Para cada resposta:
- Identifique os principais trabalhos relacionados ao tema
- Aponte metodologias, datasets e resultados relevantes
- Indique lacunas ou questões em aberto na literatura
- Cite as fontes encontradas
Responda sempre em português, de forma estruturada e acadêmica.""",
    debug_mode=True,
)

agent.print_response(
    "Quais são os principais artigos sobre aprendizado federado (federated learning)? "
    "Resuma as metodologias utilizadas e aponte lacunas na literatura."
)
