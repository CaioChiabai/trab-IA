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
- **Banco Vetorial (RAG)**: Solução local para indexação de PDFs (através da pasta `data/artigos/`)

## Pré-requisitos e Configuração

1. **Chave de API do Groq**: O projeto utiliza a API do Groq para inferência do modelo de linguagem. 
   - Crie um arquivo chamado `.env` na raiz do projeto.
   - Adicione a sua chave no arquivo:
     ```env
     GROQ_API_KEY=sua_chave_aqui
     GROQ_MODEL=llama-3.3-70b-versatile
     ```

2. **Artigos em PDF (Para o modo RAG)**:
   - Caso deseje utilizar o modo RAG, coloque os artigos em formato `.pdf` dentro da pasta `data/artigos/` antes de iniciar. (Você também pode fazer o upload pela interface web do RAG).

## Como Executar e Testar

O projeto possui scripts automatizados (`.bat`) para facilitar a execução no Windows. Eles automaticamente criam o ambiente virtual, instalam as dependências listadas em `requirements.txt` e iniciam a aplicação.

### Interface Web (Recomendado) — um único app com os dois modos

- Execute o arquivo **`run_web.bat`**.
- O navegador abrirá com a interface Streamlit. Na **barra lateral**, escolha o modo de pesquisa:
  - **🌐 Pesquisa na Web**: o agente busca fontes reais na internet sobre qualquer tema.
    - *Teste*: "Quais são os principais artigos sobre aprendizado federado?"
  - **📚 Pesquisa nos PDFs (RAG)**: responde **com base nos PDFs** da pasta `data/artigos/`, com citações. Você pode adicionar ou remover PDFs pela própria interface.
    - *Teste*: com artigos na base, pergunte "Quais metodologias são comparadas nestes artigos?"

### Linha de Comando (CLI)

- `run.bat` — pesquisa na web pelo terminal.
- `run_rag.bat` — pesquisa RAG (base de PDFs locais) pelo terminal.

## Estrutura do Projeto

```
├── app.py                     # Entry Streamlit — despacha entre os dois modos escolhidos na tela
├── run_web.bat / run.bat / run_rag.bat
├── src/                       # Código-fonte da aplicação
│   ├── config.py              # Configuração central: caminhos (absolutos) e modelos
│   ├── utils.py               # Utilitários compartilhados (slug de arquivo, gravação dos resultados)
│   ├── agents/
│   │   ├── web.py             # Agente de pesquisa na web (DuckDuckGo)
│   │   └── rag.py             # Agente RAG sobre base vetorial local de PDFs
│   └── ui/
│       ├── web_view.py        # Interface do modo de pesquisa na web
│       └── rag_view.py        # Interface do modo de pesquisa RAG (PDFs)
├── scripts/
│   └── avaliar_traces.py      # Bateria de avaliação de traces do RAG
├── data/                      # Dados (não versionados, exceto os PDFs de exemplo)
│   ├── artigos/               # PDFs de entrada do modo RAG
│   ├── vectordb/              # Base vetorial LanceDB (gerada)
│   └── resultados/            # Relatórios .md gerados
└── docs/                      # Documentação e artefatos de análise
    ├── perguntas-exemplo.md
    ├── dificuldades-implementacao.md
    └── traces/
```

**Como rodar pela CLI** (a partir da raiz): `python -m src.agents.web` ou `python -m src.agents.rag`
(os arquivos `.bat` já fazem isso automaticamente).
