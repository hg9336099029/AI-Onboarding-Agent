# AI Codebase Onboarding - Backend

AI-powered backend service for understanding codebases through natural language queries.

## Features

- 🔍 **Semantic Code Search**: Find relevant code using natural language
- 🧠 **RAG-based Q&A**: Answer questions grounded in actual code
- 📊 **Execution Flow Analysis**: Trace function call paths
- 📝 **Citation-Backed Responses**: Every answer includes file paths and line numbers
- 🐍 **Python & JavaScript**: Supports multiple languages via AST parsing

## Architecture

```
app/
├── agent/          # RAG orchestration
├── api/            # FastAPI endpoints
├── embeddings/     # OpenAI embeddings + FAISS
├── ingestion/      # Git + AST parsing
├── storage/        # PostgreSQL models
└── utils/          # LLM client
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Required variables:
- `OPENAI_API_KEY`: Your OpenAI API key
- `DATABASE_URL`: PostgreSQL connection string

### 3. Initialize Database

```bash
# Database tables will be created automatically on first run
```

### 4. Run the Server

```bash
# Development
python -m app.main

# Or with uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Health Check
```
GET /api/v1/health
```

### Ingest Repository
```
POST /api/v1/repository/ingest
{
  "repo_url": "https://github.com/user/repo",
  "branch": "main"
}
```

### Query Codebase
```
POST /api/v1/query
{
  "question": "How does authentication work?",
  "repo_id": "user_repo",
  "include_execution_flow": true
}
```

### Get File Content
```
GET /api/v1/file?repo_id=user_repo&file_path=src/auth.py
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development

### Project Structure

- **Agent Layer**: RAG pipeline for code Q&A
- **API Layer**: FastAPI routes and controllers
- **Embeddings**: OpenAI embeddings + FAISS vector search
- **Ingestion**: Git clone, AST parsing, code chunking
- **Storage**: PostgreSQL for metadata, FAISS for vectors

### Adding Language Support

1. Create parser in `app/ingestion/<lang>_ast.py`
2. Update `IngestionService` to use new parser
3. Add file extensions to config

## License

MIT
