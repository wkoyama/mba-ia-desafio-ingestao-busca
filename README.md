# Desafio MBA Engenharia de Software com IA - Full Cycle

# Ingestão e Busca Semântica com LangChain + Postgres (pgVector)

## Objetivo
- Ingerir `document.pdf`, dividir em chunks, gerar embeddings (Google Gemini).
- Armazenar no Postgres com pgVector.
- Perguntar via CLI e obter respostas **apenas** com base no PDF.

## Tecnologias
- Python + LangChain
- PostgreSQL + pgVector (via Docker Compose)
- Google Gemini (chaves via `.env`)

## Estrutura

```
├── docker-compose.yml
├── requirements.txt
├── src/
│   ├── ingest.py
│   ├── search.py
│   ├── chat.py
│   └── check_db.py
├── document.pdf
└── README.md
```

## Passos para rodar

### 1. Pré-requisitos
- Docker & Docker Compose
- Python 3.10+
- Chave da API do Google Gemini

### 2. Configuração do ambiente Python

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configuração das variáveis de ambiente

Configure as chaves de API no arquivo `.env`:

```
cp .env.example .env
```

Edite o arquivo .env e edite a chave do google e demais propriedades como modelo abaixo:

```env
# Configurações do PostgreSQL
PGHOST=localhost
PGPORT=5432
PGUSER=postgres
PGPASSWORD=postgres
PGDATABASE=langchain_db
TABLE_NAME=documents

# Configurações da API do Google
GOOGLE_API_KEY=sua_chave_api_do_google_aqui

# Configurações de busca
TOP_K=10
```

**Como obter a chave da API do Google:**
1. Acesse [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Faça login com sua conta Google
3. Clique em "Create API Key"
4. Copie a chave e cole no arquivo `.env`

### 4. Subir Postgres com pgVector

```bash
docker compose up -d
```

**Aguarde o banco subir completamente** (pode levar alguns minutos na primeira execução).

### 5. Verificar e criar conexão com o banco

```bash
python src/check_db.py
```

Este comando verifica se a conexão com o PostgreSQL está funcionando.

### 6. Ingestão do PDF

1. Coloque seu arquivo PDF na raiz do projeto com o nome `document.pdf`
2. Execute o comando de ingestão:

```bash
python src/ingest.py
```

**O que acontece durante a ingestão:**
- Lê as páginas do PDF com PyPDFLoader
- Divide em chunks (1000 caracteres, overlap 150)
- Gera embeddings usando Google Gemini (modelo: `models/embedding-001`)
- Insere vetores no Postgres (coleção `documents`)

### 7. Chat CLI

```bash
python src/chat.py
```

**Como usar:**
- Digite sua pergunta no prompt
- Pressione Enter para enviar
- Digite `sair`, `exit` ou `quit` para encerrar

**O que acontece internamente:**
- Vetoriza a pergunta
- Busca os k=10 itens mais relevantes
- Monta o CONTEXTO
- Chama o LLM (Google Gemini - modelo: `gemini-2.5-flash-lite`)
- Imprime a resposta

**Regras:** O LLM responde somente com base no CONTEXTO ou retorna: "Não tenho informações necessárias para responder sua pergunta."

### Exemplo de uso:
```
PERGUNTA: Qual o faturamento da Empresa SuperTechIABrazil?
RESPOSTA: O faturamento foi de 10 milhões de reais.

PERGUNTA: Qual é a capital da França?
RESPOSTA: Não tenho informações necessárias para responder sua pergunta.
```

## Troubleshooting

### Erro: "GoogleGenerativeAIEmbeddings não disponível"
```bash
pip install langchain-google-genai
```

### Erro: "PGVector não disponível"
```bash
pip install langchain-postgres
```

### Erro de conexão com PostgreSQL
1. Verifique se o Docker está rodando: `docker ps`
2. Verifique se o container está ativo: `docker compose ps`
3. Teste a conexão: `python src/check_db.py`

### Erro: "Arquivo PDF não encontrado"
- Certifique-se de que o arquivo está na raiz do projeto
- Verifique se o nome é exatamente `document.pdf`

### Erro: "Defina GOOGLE_API_KEY no .env"
- Verifique se o arquivo `.env` existe na raiz
- Confirme se a chave está correta (sem espaços extras)

