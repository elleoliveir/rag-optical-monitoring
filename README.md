# 📡 RAG para monitoramento de redes ópticas

![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python) ![Ollama](https://img.shields.io/badge/LLM_local-Ollama-black?style=for-the-badge) ![FAISS](https://img.shields.io/badge/Busca_vetorial-FAISS-6A4FB8?style=for-the-badge)

Sistema de **RAG (Retrieval-Augmented Generation)** que permite fazer perguntas em linguagem natural sobre dados de monitoramento de uma rede óptica, como potência de amplificadores, BER e OSNR, e receber respostas baseadas nos próprios dados, e não no "conhecimento geral" do modelo.

Tudo roda localmente: o modelo de linguagem (Llama 3.1 8B) é servido pelo Ollama, e a busca vetorial é feita com FAISS.

---

## 🎯 A pergunta por trás do projeto

Um LLM sozinho não sabe nada sobre a *sua* rede. Perguntado "qual amplificador causou as falhas?", ele inventa uma resposta genérica e plausível. A ideia aqui é medir o que muda quando o modelo recebe, junto com a pergunta, os trechos de telemetria mais relevantes.

Por isso o script responde cada pergunta **duas vezes**, sem RAG e com RAG, e salva as duas respostas lado a lado em `results.json`.

---

## ⚙️ Como funciona

```
CSV de telemetria (falhas hard e soft)
        │
        ▼
build_docs_*.py ── agrupa as medições em janelas de 1 minuto e escreve
        │          um relatório em texto por janela (BER, OSNR por dispositivo;
        │          potência de entrada/saída por amplificador; se houve falha)
        ▼
docs/*.txt
        │
        ▼
rag_ollama.py
  ├─ embeddings com all-MiniLM-L6-v2 (sentence-transformers), normalizados
  ├─ índice FAISS por produto interno (equivale a similaridade de cosseno)
  ├─ para cada pergunta: recupera os 4 relatórios mais parecidos
  ├─ resposta SEM RAG: só a pergunta
  └─ resposta COM RAG: pergunta + relatórios, com a instrução de usar
     apenas o contexto e dizer quando não houver evidência suficiente
        │
        ▼
results.json (pergunta, resposta sem RAG, resposta com RAG, documentos recuperados)
```

---

## 🔍 Exemplo de resultado

**Pergunta:** *Which amplifier is mainly responsible for the detected failures?*

| Sem RAG | Com RAG |
|---|---|
| Inventa um componente genérico ("Error Detection Amplifier") que não existe na rede. | Analisa as potências de entrada e saída dos amplificadores reais da rede (Ampli1, Ampli3, Ampli4) presentes nos relatórios recuperados. |

Pela documentação do dataset, a resposta certa é o **Ampli1**, onde as falhas foram provocadas. Com RAG, o modelo passa a raciocinar sobre os equipamentos reais e aponta o Ampli1 primeiro, mas ainda não chega a uma conclusão única. Esse é um dos pontos a melhorar.

As respostas completas das quatro perguntas de teste estão em [`results.json`](results.json).

---

## ⚠️ Limitações observadas

Uma análise honesta dos resultados atuais, que guia os próximos passos:

- **Avaliação qualitativa:** são 4 perguntas, comparadas lado a lado, sem métrica automática.
- **Recuperação imperfeita:** na pergunta sobre falhas *soft*, os 4 documentos recuperados vieram do conjunto *hard*, porque os relatórios são muito parecidos entre si em texto.
- **Documentos duplicados:** relatórios antigos na raiz de `docs/` aparecem junto com os de `docs/soft/`.
- **Raciocínio numérico:** o modelo às vezes confunde dispositivos com amplificadores ou interpreta potências de forma equivocada.

**Próximos passos:** filtrar por tipo de falha antes da busca, incluir metadados (horário, ID do equipamento) nos relatórios, criar um conjunto maior de perguntas com respostas conhecidas e medir a taxa de acerto.

---

## 🗂️ Dados

O projeto usa o **[Optical Failure Dataset](https://github.com/Network-And-Services/optical-failure-dataset)**, público, coletado no testbed ARNO (InRete Lab, TeCIP, Scuola Superiore Sant'Anna). A rede tem dois equipamentos SPO 1400 (que medem BER e OSNR) e quatro amplificadores EDFA (que medem potência de entrada e saída), com amostras a cada 3,5 segundos.

- **HardFailure_dataset.csv:** 10 horas, com falhas periódicas que interrompem o enlace.
- **SoftFailure_dataset.csv:** 8 horas, com falhas que degradam BER e OSNR sem derrubar a rede.

Nos dois casos, as falhas foram provocadas por atenuação na entrada do **Ampli1**. Isso dá uma resposta conhecida para checar o sistema. Os arquivos de dados não estão incluídos neste repositório.

---

## 🛠️ Tecnologias

- **Linguagem:** Python
- **Dados:** pandas
- **Embeddings:** sentence-transformers (`all-MiniLM-L6-v2`)
- **Busca vetorial:** FAISS (`IndexFlatIP`)
- **LLM local:** Ollama (`llama3.1:8b`, configurável pela variável `OLLAMA_MODEL`)

---

## 🚀 Como executar

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Instale o [Ollama](https://ollama.com) e baixe o modelo:
   ```bash
   ollama pull llama3.1:8b
   ```
3. Baixe os arquivos `HardFailure_dataset.csv` e `SoftFailure_dataset.csv` do dataset público (veja [Dados](#-dados)), coloque-os nas pastas `hard/` e `soft/` e gere os relatórios:
   ```bash
   python build_docs_hard.py
   python build_docs_soft.py
   ```
4. Com o Ollama rodando, execute:
   ```bash
   python rag_ollama.py
   ```

---

## 👩‍💻 Autora

**Adryele Oliveira** · [@elleoliveir](https://github.com/elleoliveir) · [Portfólio](https://elleoliveir.github.io)
