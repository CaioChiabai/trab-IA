# Pesquisador Bibliográfico IA

Este projeto é um agente autônomo baseado em Inteligência Artificial que pesquisa, resume e compara artigos científicos a partir de perguntas em linguagem natural. Ele foi desenvolvido utilizando **Python**, **Agno**, **Groq LLM** e **Streamlit**, oferecendo tanto uma interface de linha de comando (CLI) quanto uma interface web interativa.

O projeto possui dois modos principais de funcionamento:
1. **Pesquisa na Web**: Busca ativamente por fontes reais na web (usando DuckDuckGo), analisa o conteúdo e gera um relatório acadêmico estruturado com as fontes.
2. **Pesquisa Local (RAG - Retrieval-Augmented Generation)**: Lê um conjunto de artigos em PDF previamente inseridos, indexa-os em uma base vetorial e responde a perguntas comparativas sobre eles, citando os trechos exatos de origem.

## Tecnologias Utilizadas

- **Linguagem**: Python
- **Framework Web**: Streamlit
- **Agentes e IA**: Agno, Groq LLM (ex: llama-3.3-70b-versatile)
- **Busca**: DuckDuckGo
- **Banco Vetorial (RAG)**: Solução local para indexação de PDFs (através da pasta `artigos/`)

## Pré-requisitos e Configuração

1. **Chave de API do Groq**: O projeto utiliza a API do Groq para inferência do modelo de linguagem. 
   - Crie um arquivo chamado `.env` na raiz do projeto.
   - Adicione a sua chave no arquivo:
     ```env
     GROQ_API_KEY=sua_chave_aqui
     GROQ_MODEL=llama-3.3-70b-versatile
     ```

2. **Artigos em PDF (Para o modo RAG)**:
   - Caso deseje utilizar o modo RAG, coloque os artigos em formato `.pdf` dentro da pasta `artigos/` antes de iniciar. (Você também pode fazer o upload pela interface web do RAG).

## Como Executar e Testar

O projeto possui scripts automatizados (`.bat`) para facilitar a execução no Windows. Eles automaticamente criam o ambiente virtual, instalam as dependências listadas em `requirements.txt` e iniciam a aplicação desejada.

### Modo 1: Pesquisa na Web

Neste modo, o agente fará buscas na internet para responder à sua pergunta de pesquisa.

- **Interface Web (Recomendado)**:
  - Execute o arquivo `run_web.bat`.
  - O navegador abrirá automaticamente com a interface Streamlit.
  - *Teste*: Tente fazer uma pergunta como: "Quais são os principais artigos sobre aprendizado federado?"

- **Linha de Comando (CLI)**:
  - Execute o arquivo `run.bat`.
  - Acompanhe o processo diretamente pelo terminal.

### Modo 2: Pesquisador RAG (Base de Artigos Locais)

Neste modo, o agente responderá perguntas **exclusivamente com base nos PDFs** presentes na pasta `artigos/`.

- **Interface Web (Recomendado)**:
  - Execute o arquivo `run_web_rag.bat`.
  - Na interface, você verá os PDFs indexados e poderá enviar perguntas cujas respostas serão baseadas neles, com as devidas citações.
  - *Teste*: Se você tiver artigos sobre LLMs na pasta, pergunte: "Quais metodologias são comparadas nestes artigos?"

- **Linha de Comando (CLI)**:
  - Execute o arquivo `run_rag.bat`.
  - A pesquisa ocorrerá no terminal lendo sua base vetorial.

## Estrutura do Projeto

- `app.py`: Front-end web (Streamlit) para a pesquisa na web.
- `app_rag.py`: Front-end web (Streamlit) para a pesquisa RAG com PDFs.
- `agent.py`: Lógica principal do agente de pesquisa na web.
- `agent_rag.py`: Lógica principal do agente de pesquisa em base vetorial local.
- `avaliar_traces.py`: Script para avaliação dos rastros de execução.
- `artigos/`: Pasta onde os PDFs devem ser inseridos para o modo RAG.
- `resultados/`: Pasta onde as pesquisas geradas são salvas em formato `.md`.
- `traces/`: Logs e rastros de execução.
- `*.bat`: Scripts facilitadores para iniciar cada uma das aplicações no Windows.
