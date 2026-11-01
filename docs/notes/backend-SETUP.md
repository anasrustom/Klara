# Backend Installation & Setup Guide

## Quick Start

1. **Create Virtual Environment**
   ```powershell
   cd backend
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. **Install Dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Setup Environment**
   ```powershell
   copy .env.example .env
   ```
   
   Edit `.env` and add:
   - Your Gemini API key
   - Change SECRET_KEY for production

4. **Run the Server**
   ```powershell
   python main.py
   ```

5. **Test API**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

## Database

SQLite database will be automatically created on first run.
Location: `backend/clm_database.db`

## File Uploads

Uploaded files are stored in: `backend/uploads/`

## API Documentation

Interactive API docs available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## TODO for Backend Team

### Service Architecture
The backend is organized into 5 main AI services:

1. **extraction.py** - Extract structured data from contracts
   - Parties, dates, financial terms, governing law, etc.
   
2. **risks.py** - Identify and analyze contract risks
   - Missing clauses, unusual terms, compliance issues
   
3. **summary.py** - Generate contract summaries
   - Executive summary, purpose, scope, key obligations
   
4. **chat.py** - Handle natural language Q&A
   - Answer questions about contracts using AI
   
5. **rag.py** - RAG implementation
   - Document chunking, embeddings, semantic search
   - Used by chat.py and summary.py for context

### High Priority - Core Pipeline
### High Priority - Core Pipeline

**1. Extraction Service** (`src/services/extraction.py`)
   - Implement `extract_all()` method
   - Extract parties, dates, financial terms
   - Extract governing law and jurisdiction
   - Return structured data

**2. Risk Service** (`src/services/risks.py`)
   - Implement `analyze_risks()` method
   - Check for missing standard clauses
   - Identify unusual or high-risk clauses
   - Rate severity (low/medium/high/critical)

**3. Summary Service** (`src/services/summary.py`)
   - Implement `generate_summary()` method
   - Generate executive summary (1-2 paragraphs)
   - Extract purpose and scope
   - Create highlights

**4. Upload Pipeline** (`src/api/routes/upload.py`)
   - Uncomment and complete the TODO pipeline
   - Connect: OCR → Extraction → Risks → Summary → RAG
   - Save all extracted data to database

### Medium Priority

**5. RAG Service** (`src/services/rag.py`)
   - Implement document chunking
   - Generate embeddings with Gemini
   - Store in vector database
   - Implement semantic search

**6. Chat Service** (`src/services/chat.py`)
   - Implement `answer_contract_question()`
   - Use RAG for context retrieval
   - Generate answers with Gemini
   - Return with source citations

**7. Chat Route** (`src/api/routes/chat.py`)
   - Uncomment TODO code
   - Connect to chat_service
   - Save to chat_history table

### Low Priority
   - Add proper exception handling
   - Validation improvements
   - Logging

7. **Security**
   - Rate limiting
   - File upload security
   - Input sanitization

## Testing

```powershell
# Install pytest
pip install pytest pytest-asyncio

# Run tests (when created)
pytest
```

## Common Issues

**Import errors?**
- Make sure virtual environment is activated
- Run `pip install -r requirements.txt` again

**Database errors?**
- Delete `clm_database.db` and restart

**API not accessible?**
- Check if port 8000 is free
- Try `netstat -ano | findstr :8000`
