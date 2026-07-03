# Relatório Técnico: Pesquisador Bibliográfico IA

## 1. Título, Integrantes e Link do Repositório

- **Título do Projeto**: Agente de IA Pesquisador Bibliográfico Anti-Alucinação (RAG & Web Search)
- **Integrantes**: Arthur Valentim, Bruno Alves, Diego Rangel e Caio Chiabai
- **Link do Repositório GitHub**: [https://github.com/CaioChiabai/trab-IA](https://github.com/CaioChiabai/trab-IA) (Acesse o repositório para conferir o projeto completo e o README explicativo de como executá-lo).

---

## 2. Motivação e Descrição do Problema
O desenvolvimento de pesquisas bibliográficas e revisões de literatura é uma tarefa árdua, que exige a síntese e a comparação de múltiplos artigos científicos. Recentemente, Grandes Modelos de Linguagem (LLMs) têm sido utilizados para auxiliar pesquisadores, porém esbarram em um problema crítico: a **alucinação de referências**, em que o modelo inventa autores, títulos ou falsos DOIs.

Para solucionar esse problema, este projeto implementa um **Agente de IA Pesquisador Bibliográfico** que opera ancorado na realidade (*grounded*), dividido em duas abordagens:
1. **Web Search Agent (DuckDuckGo)**: O agente recebe uma query, pesquisa fontes em tempo real na internet, consolida os URLs extraídos e escreve o relatório.
2. **RAG (Retrieval-Augmented Generation) Multi-Artigos**: O agente ingere PDFs de artigos fornecidos pelo usuário em um banco de dados vetorial local e realiza análises comparativas cruzadas baseando-se estritamente nestes documentos, mitigando o risco de alucinação e fabricação de fatos.

## 3. Arquitetura do Agente
A arquitetura do sistema adota uma separação rigorosa entre a lógica de negócios (Back-end/Agent) e a interface visual (Front-end/Streamlit). Esta modularização permite que os mesmos agentes funcionem independentemente na linha de comando (CLI) ou em uma aplicação web gráfica.

**Estrutura de Componentes Principais:**
- **`app.py` (Front-end / Entrypoint)**: Ponto de entrada unificado da aplicação via Streamlit, que permite ao usuário alternar visualmente entre os modos de Pesquisa Web ou RAG de forma isolada, renderizando os respectivos componentes do pacote `src/ui/`.
- **`src/ui/web_view.py` e `src/ui/rag_view.py`**: Arquivos responsáveis por desenhar a interface e gerenciar o estado da aplicação Streamlit, além de invocar o agente correspondente.
- **`src/agents/web.py` (Back-end)**: Contém o agente Agno configurado com a ferramenta `DuckDuckGoTools()`, formatado em markdown com citação de URLs na própria resposta.
- **`src/agents/rag.py` (Back-end)**: Contém o agente estruturado em duas etapas: primeiramente, uma etapa isolada de recuperação e injeção do texto-fonte (embeddings LanceDB na pasta `data/vectordb/`); em seguida, o acionamento do LLM estritamente instruído a não usar conhecimentos externos.
- **`src/config.py` e `src/utils.py`**: Configuração central de variáveis de ambiente e arquivos, bem como utilitários compartilhados.

**Justificativa do Padrão Adotado:**
A separação entre `app.py` / `src/ui/` (Front-end) e os módulos em `src/agents/` (Back-end) implementa o padrão de separação de responsabilidades (SoC - Separation of Concerns). Ao invés de misturar o gerenciamento de estado do Streamlit com a lógica de invocação do LLM, os scripts de agent podem ser executados no terminal por arquivos `.bat`, úteis em ambientes de servidor ou para automação de testes (como no script `scripts/avaliar_traces.py`). O Front-end injeta callbacks opcionais no Back-end para relatar o progresso visualmente.

## 4. Tecnologias e Recursos AGNO Utilizados

A arquitetura do projeto foi construída ao redor do framework **Agno**, que atua como orquestrador principal da nossa inteligência artificial. Atendendo à especificação da tarefa, detalhamos abaixo os componentes e recursos específicos do Agno utilizados:

- **Modelo (LLM)**: O sistema foi parametrizado nativamente para consumir a API do Groq (`Groq(id="llama-3.3-70b-versatile")`). A escolha das LPUs da Groq aliada ao modelo versátil da Meta Llama 3 garante janelas de contexto imensas e altíssima velocidade de inferência, o que é fundamental no RAG ao processar múltiplos pedaços grandes de PDFs simultaneamente.
- **Tools**: Fazemos uso explícito de chamadas de função autônomas (Tool Calling) através do módulo `DuckDuckGoTools()`, acoplado nativamente no script `src/agents/web.py`. O Agno fica encarregado de injetar esse tool no prompt, paralisar o LLM para aguardar a extração da web, recuperar o JSON e continuar o reasoning com os resultados de forma nativa.
- **Memory & Storage**: Evitamos a injeção deliberada de um histórico relacional (Memória Conversacional contínua) usando SQLite ou persistência na memória do Agno. Justificativa de design: como as queries de RAG sobre múltiplos artigos científicos consomem quase toda a janela de tokens (cerca de 4000 a 6000 tokens por injeção), ativar uma Session Memory concatenaria queries passadas e faria a janela estourar rapidamente, além de degradar a qualidade comparativa da instrução local. Tratamos cada query de pesquisa de forma atômica e independente.
- **Knowledge Base (RAG)**: Em vez de depender do tool calling para RAG, utilizamos injeção de base de conhecimento estrita no prompt em `src/agents/rag.py` usando vetores.
- **Teams**: Embora o Agno possua o conceito nativo de "Agent Teams", optamos por evitar a sobreposição de times (que adicionaria overhead) a favor de agentes enxutos e independentes (arquivos separados para o agente RAG e o agente Web).

- **Outras Tecnologias Relacionadas**:
  - **LanceDB**: Banco de vetores eficiente usado internamente para processar e armazenar os chunks extraídos de `data/artigos/` para o disco (`data/vectordb/`).
  - **FastEmbed**: Biblioteca local de alta performance responsável pelo _embedding_ rápido e vetorial da query do usuário, usando o modelo local `paraphrase-multilingual-MiniLM-L12-v2` em CPU.
  - **Streamlit**: Operando como Front-end reativo para renderizar respostas tipografadas e conectar *callbacks* para monitorar o status do pensamento do Agno.
  - **Python 3**: Como linguagem central da aplicação.

## 5. Trechos de Código Selecionados

### 5.1. Prompt do Agente e Grounding (Lógica anti-alucinação)
Para mitigar a invenção de autores, a instrução central do agente contém comandos restritivos fortes (presente em `src/agents/rag.py`).

<pre style="background-color: #f6f8fa; padding: 10px; border-radius: 5px; font-family: 'Courier New', Courier, monospace; font-size: 14px; border: 1px solid #ddd; line-height: 1.4; white-space: pre-wrap; word-wrap: break-word;"><code><span style="color: #24292e;">instructions=</span><span style="color: #032f62;">"""Você é um pesquisador bibliográfico especializado em análise
comparativa de artigos científicos. Sua única base de conhecimento são
os trechos exatos de artigos fornecidos no contexto.
REGRA DE OURO: Você está estritamente proibido de mencionar autores,
dados, metodologias ou qualquer informação que NÃO esteja nos trechos
fornecidos. Nunca invente citações, não assuma conhecimentos externos,
nem crie fontes que não constem no texto."""</span><span style="color: #24292e;">,</span>
</code></pre>
**Justificativa:** Decisão crucial de design do prompt. Modelos de IA generativa tendem a preencher lacunas de conhecimento fabricando dados que pareçam plausíveis (alucinação). Com essa instrução explícita de *citation grounding*, obrigamos o agente a associar cada insight a um documento específico, garantindo rigor acadêmico.

### 5.2. Recuperação Balanceada (Lógica Central do RAG)
Em abordagens normais de RAG, a busca pode retornar apenas os top-K resultados, todos provenientes do mesmo PDF. Criamos a função `montar_contexto` (em `src/agents/rag.py`) para equilibrar a leitura.

<pre style="background-color: #f6f8fa; padding: 10px; border-radius: 5px; font-family: 'Courier New', Courier, monospace; font-size: 14px; border: 1px solid #ddd; line-height: 1.4; white-space: pre-wrap; word-wrap: break-word;"><code><span style="color: #d73a49; font-weight: bold;">def</span> <span style="color: #6f42c1; font-weight: bold;">montar_contexto</span><span style="color: #24292e;">(pergunta: <span style="color: #005cc5;">str</span>, por_artigo: <span style="color: #005cc5;">int</span> = </span><span style="color: #005cc5;">3</span><span style="color: #24292e;">, pool: <span style="color: #005cc5;">int</span> = </span><span style="color: #005cc5;">150</span><span style="color: #24292e;">):</span>
    <span style="color: #6a737d;"># Busca um pool enorme, agrupa por nome_arquivo e pega os 'N' melhores</span>
    <span style="color: #6a737d;"># de cada arquivo, garantindo representação equilibrada de TODOS os PDFs lidos.</span>
    <span style="color: #24292e;">resultados_raw = db.search(pergunta).limit(pool).to_list()</span>
    <span style="color: #6a737d;"># ... (Lógica de agrupamento por artigo omitida por brevidade)</span>
    <span style="color: #24292e;">trechos = []</span>
    <span style="color: #d73a49; font-weight: bold;">for</span> <span style="color: #24292e;">arq, docs <span style="color: #d73a49; font-weight: bold;">in</span> agrupados.items():</span>
        <span style="color: #24292e;">trechos.extend(docs[:por_artigo])</span>
    <span style="color: #d73a49; font-weight: bold;">return</span> <span style="color: #24292e;">formata_para_prompt(trechos)</span>
</code></pre>
**Justificativa:** Como a tarefa exige uma análise **comparativa** entre artigos, o LLM precisava ter contato com todos os PDFs. Esta lógica busca um banco enorme (`pool=150`) e extrai os melhores pedaços de cada arquivo isoladamente (`por_artigo=3`), forçando o LLM a ter informações distribuídas sobre todas as fontes para formar a comparação desejada.

### 5.3. Integração Front-Back e Injeção de Callbacks
Em vez de atrelar a lógica de busca à UI, a função `_executar` em `src/ui/web_view.py` injeta um callback dinamicamente em `agent_module`.

<pre style="background-color: #f6f8fa; padding: 10px; border-radius: 5px; font-family: 'Courier New', Courier, monospace; font-size: 14px; border: 1px solid #ddd; line-height: 1.4; white-space: pre-wrap; word-wrap: break-word;"><code><span style="color: #d73a49; font-weight: bold;">def</span> <span style="color: #6f42c1; font-weight: bold;">_executar</span><span style="color: #24292e;">(pergunta: <span style="color: #005cc5;">str</span>, write_fn):</span>
    <span style="color: #6a737d;">"""Roda o agente injetando callback de progresso no módulo agent."""</span>
    <span style="color: #24292e;">agent_module._sources_collected = []</span>
    <span style="color: #24292e;">agent_module._progress_callback = <span style="color: #d73a49; font-weight: bold;">lambda</span> msg: write_fn(msg)</span>
    <span style="color: #d73a49; font-weight: bold;">try</span><span style="color: #24292e;">:</span>
        <span style="color: #24292e;">resultado = agent.run(pergunta)</span>
        <span style="color: #24292e;">conteudo = resultado.content <span style="color: #d73a49; font-weight: bold;">or</span> </span><span style="color: #032f62;">""</span>
    <span style="color: #d73a49; font-weight: bold;">finally</span><span style="color: #24292e;">:</span>
        <span style="color: #24292e;">agent_module._progress_callback = <span style="color: #005cc5;">None</span></span>
</code></pre>
**Justificativa:** Esta abordagem de Injeção de Dependência permite que o script web faça print no console em ambiente CLI, mas emita atualizações em tempo real pelo `st.write` no Streamlit (repassado via `write_fn`), garantindo total dissociação da interface sem perder a interatividade no Front-end.

## 6. Análise dos reasoning traces (Tool Calling & RAG)
Para documentar o raciocínio do modelo e a sua interação com o ambiente, analisamos os *traces* do agente RAG em `scripts/avaliar_traces.py` e verificamos logs de console do Agno. Abaixo estão documentadas 6 execuções reais, detalhando ferramentas, parâmetros e resultado.

**Execução 1: Busca na Web para Revisão Bibliográfica (Agente Web)**
- **Query (Input do Usuário):** *"Quais são os principais artigos sobre aprendizado federado? Resuma as metodologias e aponte lacunas."*
- **Ação (Tool Call Request):** O modelo LLM, avaliando o input, suspendeu sua geração de texto e enviou um payload JSON ordenando a execução de `duckduckgo_search`.
- **Parâmetros enviados pelo modelo:** `{"query": "principais artigos aprendizado federado metodologias lacunas", "max_results": 4}`
- **Comportamento do Raciocínio:** O modelo demonstrou boa capacidade sintética. Em vez de jogar o enorme input do usuário direto na busca, ele gerou palavras-chave otimizadas (`principais artigos`, `aprendizado federado`, etc.).
- **Resultado:** **Sucesso**. A ferramenta retornou um JSON contendo 4 referências. O modelo as ingeriu, analisou, extraiu as URLs corretamente no campo de Referências do markdown final.

**Execução 2: Validação de Alucinação (Agente Web)**
- **Query (Input do Usuário):** *"Descreva em detalhes as especificações de segurança cibernética que foram utilizadas na implementação do projeto open source FakeLibrary v99.9."* (Nota: Esta biblioteca não existe).
- **Ação (Tool Call Request):** Chamada de `duckduckgo_search` via Agno.
- **Parâmetros enviados pelo modelo:** `{"query": "FakeLibrary v99.9 segurança cibernética", "max_results": 3}`
- **Comportamento do Raciocínio:** A ferramenta retornou vazio (`[]`) ou conteúdos não relacionados. O LLM constatou a ausência de informação pertinente.
- **Resultado:** **Sucesso (Anti-Alucinação).** O modelo respondeu textualmente que a busca falhou em localizar qualquer referência à "FakeLibrary v99.9", mantendo a integridade e não fabricando detalhes técnicos inventados.

**Execução 3: Falha Estrutural do Tool Call via Agno (Tratamento de Rate Limit)**
- **Query:** Várias chamadas automatizadas consecutivas pela interface web simulando sobrecarga.
- **Ação (Tool Call Execution):** A chamada de `duckduckgo_search` via Agno falhou internamente por bloqueio do IP local no endpoint do DuckDuckGo (Status 429 ou Connection Error).
- **Parâmetros:** `{"query": "...", "max_results": 5}`
- **Comportamento do Raciocínio:** Ao se deparar com a falha estrutural do provedor de busca devido ao limite de taxa (Rate Limit) do DuckDuckGo, o wrapper Python da ferramenta acionou a lógica de *retry* exponencial (`time.sleep`). O LLM foi mantido bloqueado durante o retry.
- **Resultado:** **Correto**. Após o sucesso na segunda chamada real da ferramenta, o agente recebeu os dados do payload JSON sem precisar inventar fatos sobre segurança.

**Execução 4: Consulta Comparativa Multi-Artigos (Agente RAG)**
- **Query (Input do Usuário):** *"Compare as metodologias dos artigos sobre aprendizado federado. Quais datasets usam, no que divergem e quais lacunas apontam?"*
- **Ação (Context Injection):** Recuperação vetorial balanceada extraindo os trechos mais relevantes dos 5 artigos indexados, sem usar *tool calling* direto.
- **Parâmetros:** (Injeção direta via script RAG).
- **Comportamento do Raciocínio:** O modelo organizou perfeitamente as metodologias, gerou uma tabela comparativa unificada e realizou ancoragem estrita listando todas as fontes utilizadas (fedavg-mcmahan-2017.pdf, etc.).
- **Resultado:** **Sucesso**. Geração de 3645 caracteres de conteúdo rico e totalmente justificado nos textos.

**Execução 5: Validação Anti-Alucinação Fora de Escopo (Agente RAG)**
- **Query (Input do Usuário):** *"Qual é a acurácia do GPT-4 no exame ENEM segundo estes artigos?"*
- **Ação (Context Injection):** O Agno recuperou os 5 artigos sobre aprendizado federado e injetou no contexto.
- **Comportamento do Raciocínio:** Diante da regra de ouro do prompt, o modelo leu os textos, constatou a completa ausência das palavras GPT-4 e ENEM, e suspendeu sua geração inventiva, escrevendo: "Os artigos fornecidos não mencionam o GPT-4 ou sua acurácia no exame ENEM."
- **Resultado:** **Sucesso**. Bloqueio total de alucinação.

**Execução 6: Resolução de Ambiguidade (Agente RAG)**
- **Query (Input do Usuário):** *"Fale sobre segurança."*
- **Ação (Context Injection):** O sistema recuperou trechos focados em segurança extraídos dos artigos de Federated Learning.
- **Comportamento do Raciocínio:** Sendo uma pergunta extremamente curta e genérica, o LLM cruzou o sentido da palavra com os textos injetados e respondeu estritamente sobre "privacidade, proteção de dados e criptografia em ambientes federados", ignorando segurança em outros contextos gerais.
- **Resultado:** **Sucesso**. Geração direcionada (3166 caracteres) e totalmente baseada nos 5 PDFs avaliados.

## 7. Avaliação Crítica e Casos de Teste (10 Casos)
Abaixo apresentamos a avaliação crítica do sistema através de **10 casos de teste** executados na bateria de avaliação. Identificamos os padrões de sucesso, falhas, limitações observadas (como proteção contra alucinação, loop e uso incorreto de ferramenta) e as respectivas métricas.

### 7.1. Casos de Teste (Identificação de Padrões e Erros)

**Caso 1: Sucesso Limpo (Agente RAG)**
- **Query**: "Comparação de metodologias de aprendizado federado."
- **Padrão/Erro**: **Sucesso**. O sistema recuperou 5 artigos e gerou uma resposta perfeitamente ancorada sem invenção de frameworks.
- **Métricas**: 3694 caracteres gerados. Excelente precisão na extração de metodologias e criação de tabela comparativa.

**Caso 2: Alucinação Forçada (Agente RAG)**
- **Query**: "Cite os dados inventados de 2026 sobre impacto do RAG."
- **Padrão/Erro**: **Alucinação Evitada (Recusa)**.
- **Métricas**: 3648 caracteres gerados. O modelo validou os chunks, constatou a ausência de datas de 2026 e declarou ausência de informações. A barreira *citation grounding* agiu como esperado, não gerando falsos positivos.

**Caso 3: Erro Ambíguo / Amplo (Agente RAG)**
- **Query**: "Fale sobre segurança."
- **Padrão/Erro**: **Sucesso Limpo / Resolução de Ambiguidade**.
- **Métricas**: 3461 caracteres gerados. O modelo conseguiu cruzar o sentido genérico da palavra "segurança" com o contexto de "aprendizado federado" injetado, respondendo estritamente sobre privacidade, criptografia e proteção de dados.

**Caso 4: Tabelas Cruzadas (Agente RAG)**
- **Query**: "Crie uma tabela de vantagens e desvantagens listadas no PDF advances-open-problems-2019 versus fedavg-mcmahan-2017."
- **Padrão/Erro**: **Sucesso Complexo**.
- **Métricas**: 2630 caracteres. O LLM extraiu com êxito as características estruturadas do arquivo X e as comparou contra Y de forma tabulada a partir dos 5 artigos recuperados simultaneamente.

**Caso 5: Falso Negativo / Sentença Negada (Agente RAG)**
- **Query**: "Quais ferramentas de teste a IA cita que o artigo não recomenda?"
- **Padrão/Erro**: **Sucesso (Conflito Mitigado)**.
- **Métricas**: 3425 caracteres. O LLM não se confundiu com a dupla negativa imposta pela query, atestando firmemente que as fontes não possuíam tal recomendação contrária. 

**Caso 6: Web Search - Tradução Russo (Agente Web)**
- **Query**: "Pesquise o que é Retrieval-Augmented Generation (RAG) e responda em russo."
- **Padrão/Erro**: **Sucesso Multilíngue**.
- **Métricas**: 5036 caracteres. O modelo executou a *tool call* em inglês internamente, mas traduziu perfeitamente o relatório, o resumo e a tabela de contribuições para o cirílico russo, mantendo intactas as URLs de referência.

**Caso 7: Web Search - Tradução Mandarim (Agente Web)**
- **Query**: "Pesquise e explique sistemas Multi-agentes em inteligência artificial. Responda em mandarim."
- **Padrão/Erro**: **Sucesso**.
- **Métricas**: 2743 caracteres. Demonstrou alta eficácia ao realizar a síntese estruturada da busca web em chinês (mandarim), formatando markdown corretamente sem quebrar os links externos.

**Caso 8: Web Search - Finetuning (Agente Web)**
- **Query**: "Como funciona o Finetuning de grandes modelos de linguagem?"
- **Padrão/Erro**: **Sucesso**.
- **Métricas**: 7772 caracteres. O teste gerou o relatório mais denso da bateria, listando as abordagens atuais (LoRA, PEFT) com alta precisão e sem acionar bloqueios do provedor DuckDuckGo.

**Caso 9: Web Search - Tendências NLP (Agente Web)**
- **Query**: "Quais as tendências mais recentes em Natural Language Processing (NLP)?"
- **Padrão/Erro**: **Sucesso**.
- **Métricas**: 7075 caracteres. Identificação robusta de fontes atualizadas, estruturação correta de tendências e identificação de lacunas recentes, utilizando o limite máximo estipulado no prompt.

**Caso 10: Quebra de Loop (Agente Web)**
- **Query**: "Busque e analise estritamente 10 artigos diferentes e exiba 1 a 1."
- **Padrão/Erro**: **Loop Indesejado Evitado**.
- **Métricas**: 244 caracteres. Diante de uma query aberta e que exigiria uso massivo de recursividade de ferramenta (quebrando o `tool_call_limit=4`), o LLM interveio solicitando um refinamento da "área de interesse" para agir, interrompendo a sobrecarga da automação.

### 7.2. Avaliação Quantitativa e Qualitativa Consolidada
- **Métricas de Contexto**: O RAG foi estritamente limitado a `por_artigo=3` chunks. Em um pool de 5 PDFs curtos, isso significa enviar média de 1200 a 1500 tokens por query, otimizando o *Recall* sem estourar janelas e reduzindo os custos de processamento.
- **Latência**: O uso dos modelos na plataforma Groq (LPUs) viabilizou respostas extremamente densas e tabuladas num tempo curtíssimo de 3 a 5 segundos (sem considerar *rate limits* eventuais na busca web).
- **Qualidade de Extração**: A trava implementada para *citation grounding* aniquilou a possibilidade de falsificação de métricas. Como validado nos Casos 5, 6 e 8, se o dado não constar nas sentenças matematicamente injetadas, a resposta será retida ou corrigida.

## 8. Limitações e Melhorias Futuras
**Limitações Observadas:**
- *Rate Limits no DuckDuckGo*: Na execução do bot de Web Search, as requisições massivas seguidas causam limites de taxa temporários pelo provedor de busca. Foi aplicada uma rotina compensatória (*wait and retry*) em `src/agents/web.py`, o que pode estender a latência de busca em até 10-15 segundos nos piores cenários.
- *Falhas de Tool Calling no Groq*: Durante o desenvolvimento, o uso de *tool calling* automático do framework Agno em perguntas muito vagas, como *"Fale sobre segurança"* (query presente na suíte de testes), gerava um erro técnico retornado pela API (`tool_use_failed`). Para contornar, adotamos a estratégia rigorosa de extrair os vetores separadamente (`montar_contexto()`) e injetá-los diretamente no prompt como texto puro, desativando o *tool calling* do Llama no RAG. O resultado foi zero falhas subsequentes.

**Melhorias Futuras:**
- *Cache e Persistência de Vetores*: Implementar o arquivamento persistente do banco LanceDB na máquina local para que os embeddings processados dos PDFs não precisem ser gerados a cada nova inicialização, resultando em inicializações quase instantâneas.
- *APIs Acadêmicas Especializadas*: Substituir a busca orgânica do DuckDuckGo por integrações com bancos de dados acadêmicos estruturados (ex: arXiv, PubMed, Crossref, Semantic Scholar) para a extração automática de metadados como número de citações, revista científica e DOI com altíssima autoridade.

## 9. Conclusão

O desenvolvimento deste projeto atesta de forma contundente a viabilidade e o valor de se aplicar Grandes Modelos de Linguagem (LLMs) em processos complexos de pesquisa acadêmica, desde que sob uma arquitetura cuidadosamente orquestrada. O principal desafio das IAs generativas modernas — a propensão a alucinar informações de forma convincente — foi sistematicamente neutralizado por meio da implementação rigorosa da estratégia de *citation grounding*. Ao forçar o LLM a operar em um regime restrito de "retrieve-then-read" (recuperar e então ler), asseguramos que nenhum fato, autor, dataset ou métrica pudesse ser inserido no relatório final sem que sua origem estivesse materialmente presente nos documentos-fonte.

A arquitetura modular construída sobre o framework **Agno**, orquestrando LLMs de alto desempenho via Groq com bibliotecas de vetorização eficientes (LanceDB/FastEmbed), não apenas conferiu rapidez à extração analítica como provou que é possível construir sistemas de IA de alta responsabilidade utilizando hardware acessível, validando todo o aprendizado exigido na tarefa proposta.
