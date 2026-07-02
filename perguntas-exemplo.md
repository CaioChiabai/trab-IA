# Perguntas de exemplo — pesquisador RAG multi-artigos

Perguntas prontas para testar/demonstrar o agente (`agent_rag.py` / `app_rag.py`)
sobre o corpus de 5 artigos de **aprendizado federado** em `artigos/`.

> Dica: perguntas **específicas e completas** funcionam melhor. Graças à
> recuperação balanceada, as comparativas cobrem os 5 artigos.

---

## 1. Comparativas (mostram o RAG multi-artigo — ideais para a demo)

- Compare as metodologias dos artigos sobre aprendizado federado. Quais datasets usam, no que divergem e quais lacunas apontam?
- Quais são as diferentes abordagens para reduzir o custo de comunicação propostas nos artigos?
- Como os artigos tratam a questão de privacidade e segurança dos dados?
- Faça uma tabela comparando os artigos por metodologia, dataset e principal contribuição.

## 2. Datasets, métricas e resultados

- Quais datasets e métricas de avaliação são usados nos experimentos descritos nos artigos?
- Que resultados quantitativos (acurácia, número de rodadas de comunicação) os artigos relatam?
- Quais artigos usam os datasets MNIST e CIFAR-10?

## 3. Factuais / específicas (o agente acerta bem)

- Qual artigo propõe o algoritmo FedAvg (Federated Averaging) e como ele funciona?
- O que os artigos dizem sobre dados não-IID e como isso afeta o treinamento?
- Qual a diferença entre aprendizado federado horizontal e vertical segundo os artigos?
- O que é o problema de heterogeneidade de sistemas (system heterogeneity) mencionado nos artigos?

## 4. Lacunas e trabalhos futuros

- Quais são os principais problemas em aberto e desafios de pesquisa apontados nos artigos?
- Que direções de trabalho futuro os autores sugerem?

## 5. Casos "de propósito" (para a avaliação crítica do relatório)

Estes servem para mostrar o comportamento do agente em situações difíceis:

- **Fora do escopo** (deve responder *"não encontrado nos artigos ingeridos"*, sem inventar):
  - Qual é a acurácia do GPT-4 no exame ENEM segundo estes artigos?
  - O que os artigos dizem sobre carros autônomos?
- **Ambígua / vaga** (resposta mais genérica; útil para discutir limitações):
  - Fale sobre segurança.
  - Explique tudo.

---

## Como conferir se está funcionando

- Na interface web, olhe **"Artigos recuperados"** acima da resposta.
- Na resposta, a seção **"6. Fontes citadas"** deve listar os artigos usados.
- Para as comparativas, a **tabela** deve ter **uma linha por artigo**.
