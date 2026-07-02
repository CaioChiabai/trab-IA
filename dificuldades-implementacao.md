# Dificuldades e decisões — implementação do agente RAG (Tema 10)

Documento de apoio (rascunho) para guiar o relatório técnico. Lista, de forma
simples, os problemas que apareceram na prática, a causa e como foram resolvidos.

---

## 1. Problemas técnicos que travaram a implementação

### 1.1. Cota dos embeddings do Gemini (base ficava vazia)
- **O que aconteceu:** a primeira versão usava embeddings do Gemini. Ao indexar os
  PDFs, todos davam erro `429 RESOURCE_EXHAUSTED` (cota do free tier). Resultado:
  **0 vetores na base** — o RAG não tinha o que buscar.
- **Causa:** o nível gratuito de embeddings do Gemini tem limite muito baixo.
- **Solução:** trocar para **embeddings locais** com o `FastEmbed` (modelo ONNX que
  roda na máquina, sem chave de API e sem cota). O projeto ficou reprodutível.

### 1.2. `tool_use_failed` (o principal problema)
- **O que aconteceu:** ao usar busca agêntica (`search_knowledge=True`), o modelo
  no Groq falhava com `Error 400 - tool_use_failed`, emitindo a chamada de função
  num formato inválido (`<function=...>`) em vez do JSON esperado.
- **Causa:** bug conhecido dos modelos Llama no Groq ao chamar ferramentas.
- **Tentativas:**
  1. Trocar `llama-3.3-70b-versatile` → `meta-llama/llama-4-scout-17b-16e-instruct`
     (sugerido no enunciado). Melhorou, mas **ainda falhava ~25% das vezes**.
  2. Instruir o agente a "buscar primeiro" — ajudou um pouco.
- **Solução final:** trocar o modo do RAG para **retrieve-then-read**
  (`add_knowledge_to_context=True`, `search_knowledge=False`): o AGNO recupera os
  trechos e os injeta no contexto **sem exigir chamada de função**. Como o modelo
  nunca precisa emitir uma tool call, o erro **desapareceu** (100% de sucesso nos
  testes).

### 1.3. Instrução de "várias buscas" piorou tudo
- **O que aconteceu:** ao pedir para o agente fazer 2–4 buscas, a taxa de
  `tool_use_failed` **aumentou** (ele tentava uma segunda chamada no meio da
  redação).
- **Lição:** menos chamadas de ferramenta = mais estável. (Depois isso deixou de
  importar, pois migramos para retrieve-then-read.)

### 1.4. Comparação cobria só alguns artigos (top-k concentrado)
- **O que aconteceu:** numa pergunta comparativa, a busca por similaridade trazia
  os 10 trechos mais parecidos — e **9 deles vinham de um único artigo** (um survey
  amplo). Resultado: a resposta só citava 2 dos 5 artigos.
- **Causa:** o RAG recupera os top-k trechos por similaridade global; um artigo
  amplo domina o ranking e "esconde" os específicos.
- **Solução:** **recuperação balanceada por artigo** — em vez do top-k global,
  pegar os N melhores trechos de CADA artigo e juntá-los (`montar_contexto`).
  Agora os 5 artigos sempre entram no contexto e a tabela traz uma linha por artigo.

### 1.5. Alucinação quando a base estava vazia
- **O que aconteceu:** com a base sem vetores (por causa do erro do Gemini), o
  modelo **inventou** uma resposta inteira, com "Artigo 1/2/3" e datasets falsos
  (MNIST, IMDB, etc.) que não existiam.
- **Lição:** é o risco central de um RAG — sem grounding, o modelo preenche o vazio.
  Reforça a importância da regra de citação e de testar casos fora do escopo.

---

## 2. Detalhes de ambiente / "pegadinhas"

- **Codificação no Windows:** o console (cp1252) quebrava ao imprimir caracteres
  como `fi` ou acentos. Resolvido usando a biblioteca `rich` e `PYTHONIOENCODING=utf-8`.
- **Faltavam dependências:** foi preciso instalar `lancedb` (base vetorial),
  `fastembed` (embeddings) e `pypdf` (leitura dos PDFs). O `streamlit` também não
  estava instalado no ambiente.
- **Limite de tokens do Groq (TPM):** o modelo `llama-3.1-8b-instant` estourou o
  limite de 6.000 tokens/min com o contexto do RAG — foi descartado.
- **Não havia PDFs de artigos:** o RAG precisa de arquivos reais para ingerir. Como
  não existiam, foram baixados 5 artigos abertos do arXiv sobre aprendizado
  federado (o exemplo do próprio enunciado) para servir de corpus.
- **Perguntas em PT, artigos em inglês:** foi preciso escolher um embedder
  **multilíngue** (`paraphrase-multilingual-MiniLM-L12-v2`) para a busca funcionar
  bem entre idiomas.
- **Ingestão idempotente:** usar `skip_if_exists` (hash de conteúdo) para não
  reprocessar/re-embeddar os mesmos PDFs a cada execução.

---

## 3. Decisões de projeto (resumo)

| Antes | Depois | Motivo |
|---|---|---|
| Embeddings Gemini (API) | FastEmbed (local) | cota 429, base vazia |
| Llama 3.3 70B | Llama 4 Scout | tool calls malformadas |
| RAG agêntico (tool call) | RAG retrieve-then-read | `tool_use_failed` intermitente |
| Top-k global | Recuperação balanceada por artigo | comparação cobria só 1–2 artigos |
| Sem corpus | 5 PDFs do arXiv | RAG precisa de artigos reais |

---

## 4. Limitações que sobraram (para citar no relatório)

- **Qualidade dos trechos:** a recuperação balanceada já cobre todos os artigos,
  mas busca híbrida ou reranking melhorariam a escolha dos trechos dentro de cada um.
- **Preâmbulo narrativo:** o modelo às vezes começa com "Vou começar buscando…",
  poluindo levemente o Markdown final (cosmético).
- **Citação por nome de arquivo:** hoje a fonte é o nome do PDF; extrair
  título/autores/ano automaticamente deixaria a citação mais rica.
- **Sem avaliação automática:** não há métrica de fidelidade (ex.: RAGAS); a
  avaliação foi feita manualmente sobre poucos casos.

---

## 5. Pontos positivos que funcionaram

- Anti-alucinação: perguntado sobre algo fora dos artigos (GPT-4/ENEM), o agente
  respondeu **"não encontrado nos artigos ingeridos"** em vez de inventar.
- Citation grounding: as respostas citam os arquivos de origem.
- Reprodutibilidade: com embeddings locais, roda sem nenhuma chave além do Groq.
