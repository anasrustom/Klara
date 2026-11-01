# Backend Implementation Guide

## 🎯 Overview

The backend has **5 main service modules** that need implementation:

```
src/services/
├── extraction.py   → Extract data from contracts
├── risks.py        → Identify and analyze risks
├── summary.py      → Generate summaries
├── chat.py         → Handle Q&A
└── rag.py          → RAG for context retrieval
```

All services are **skeleton files with clear TODO comments**. Follow the structure and implement the methods.

---

## 📋 Implementation Order

### Phase 1: Core Extraction & Analysis (Priority 1)

#### 1.1 Extraction Service (`extraction.py`)

**Goal**: Extract structured data from contract text using Gemini.

**Key Methods to Implement**:
- `extract_all(contract_text)` → Returns all extracted data
- `extract_parties(contract_text)` → List of parties
- `extract_dates(contract_text)` → List of key dates
- `extract_financial_terms(contract_text)` → Financial terms
- `extract_governing_law(contract_text)` → Governing law
- `extract_jurisdiction(contract_text)` → Jurisdiction

**Example Gemini Prompt**:
```python
prompt = f"""
Extract the following from this contract:
1. All parties involved (name, type: individual/organization, role: client/vendor/partner)
2. All key dates (type: effective/expiration/renewal, date, description)
3. Financial terms (type, amount, currency, description)
4. Governing law
5. Jurisdiction

Contract text:
{contract_text}

Return as JSON.
"""

response = await self.model.generate_content_async(prompt)
data = json.loads(response.text)
```

**Database Storage**:
After extraction, save to database tables:
- `contract_parties` (use models from `src/models/contract.py`)
- `key_dates`
- `financial_terms`
- Update `contracts` table (governing_law, jurisdiction, industry, etc.)

---

#### 1.2 Risk Service (`risks.py`)

**Goal**: Identify risks and compliance issues.

**Key Methods**:
- `analyze_risks(contract_text, extracted_data)` → List of risks
- `check_missing_clauses(contract_text)` → Missing standard clauses
- `identify_unusual_clauses(contract_text)` → Unusual/risky clauses
- `check_consistency(contract_text)` → Inconsistencies
- `assess_compliance(contract_text, jurisdiction)` → Compliance issues

**Standard Clauses to Check**:
- Confidentiality
- Force majeure
- Termination
- Dispute resolution
- Indemnification
- Limitation of liability
- Intellectual property
- Data protection

**Risk Severity Levels**:
- `critical` - Major legal/financial exposure
- `high` - Significant risk, needs attention
- `medium` - Moderate concern
- `low` - Minor issue

**Example**:
```python
async def analyze_risks(self, contract_text, extracted_data=None):
    prompt = f"""
    Analyze this contract for risks. Identify:
    1. Missing standard clauses (confidentiality, force majeure, etc.)
    2. Unusual or high-risk clauses (unlimited liability, one-sided terms)
    3. Inconsistencies in defined terms
    4. Compliance issues
    
    For each risk, provide:
    - risk_type: missing_clause/unusual_clause/non_standard/inconsistency/compliance
    - severity: low/medium/high/critical
    - title: Brief description
    - description: Detailed explanation
    - recommendation: Suggested action
    - clause_reference: Section/clause reference
    
    Contract: {contract_text}
    
    Return as JSON array.
    """
    
    response = await self.model.generate_content_async(prompt)
    risks = json.loads(response.text)
    return risks
```

**Database Storage**:
Save to `risks` table (use `src/models/risk.py`)

---

#### 1.3 Summary Service (`summary.py`)

**Goal**: Generate human-readable summaries.

**Key Methods**:
- `generate_summary(contract_text, extracted_data, risks)` → Complete summary
- `generate_executive_summary(contract_text)` → 1-2 paragraph summary
- `extract_purpose(contract_text)` → Contract purpose
- `extract_scope(contract_text)` → Contract scope
- `identify_key_obligations(contract_text)` → Obligations by party

**Example**:
```python
async def generate_executive_summary(self, contract_text):
    prompt = f"""
    Generate a concise executive summary (1-2 paragraphs) of this contract.
    
    Include:
    - Who the parties are
    - What the contract is about
    - Key terms (dates, amounts)
    - Main obligations
    
    Contract: {contract_text[:5000]}  # Limit for token count
    
    Write in professional, clear language.
    """
    
    response = await self.model.generate_content_async(prompt)
    return response.text
```

**Database Storage**:
Update `contracts` table: `summary`, `purpose`, `scope`

---

### Phase 2: RAG Implementation (Priority 2)

#### 2.1 RAG Service (`rag.py`)

**Goal**: Enable semantic search for Q&A.

**Key Concepts**:
- **Chunking**: Split contract into smaller sections
- **Embedding**: Convert text to vectors
- **Storage**: Store vectors with metadata
- **Search**: Find relevant chunks for queries

**Key Methods**:
- `index_contract(contract_id, contract_text)` → Index for search
- `search_contract(contract_id, query)` → Find relevant sections
- `chunk_text(text)` → Split into chunks
- `generate_embedding(text)` → Create vector

**Chunking Strategy**:
```python
def chunk_text(self, text, chunk_size=500, overlap=50):
    # Split by sentences first
    sentences = text.split('. ')
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) < chunk_size:
            current_chunk += sentence + ". "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks
```

**Embedding with Gemini**:
```python
async def generate_embedding(self, text):
    # Use Gemini embedding API
    result = genai.embed_content(
        model="models/embedding-001",
        content=text,
        task_type="retrieval_document"
    )
    return result['embedding']
```

**Simple Vector Store** (for MVP):
```python
# In-memory storage (use ChromaDB/FAISS for production)
self.vector_store = {
    "contract_id_1": [
        {
            "chunk_id": 0,
            "text": "This agreement...",
            "embedding": [0.1, 0.2, ...],
        },
        # More chunks...
    ]
}
```

**Search**:
```python
async def search_contract(self, contract_id, query, top_k=5):
    # Generate query embedding
    query_embedding = await self.generate_embedding(query)
    
    # Get contract chunks
    chunks = self.vector_store.get(contract_id, [])
    
    # Calculate similarities
    results = []
    for chunk in chunks:
        similarity = self.calculate_similarity(
            query_embedding,
            chunk['embedding']
        )
        results.append({
            "text": chunk['text'],
            "score": similarity
        })
    
    # Sort and return top_k
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:top_k]
```

---

### Phase 3: Chat Integration (Priority 3)

#### 3.1 Chat Service (`chat.py`)

**Goal**: Answer questions using RAG + Gemini.

**Key Methods**:
- `answer_question(question, contract_id, contract_text, context)`
- `answer_contract_question(question, contract_id)`
- `answer_general_question(question, user_id)`

**Implementation**:
```python
async def answer_contract_question(self, question, contract_id):
    # 1. Get relevant context using RAG
    from src.services.rag import rag_service
    
    relevant_chunks = await rag_service.search_contract(
        contract_id,
        question,
        top_k=3
    )
    
    # 2. Build context from chunks
    context = "\n\n".join([chunk['text'] for chunk in relevant_chunks])
    
    # 3. Create prompt
    prompt = f"""
    Answer this question about the contract based on the provided context.
    
    Context from contract:
    {context}
    
    Question: {question}
    
    Provide a clear, accurate answer. If the information is not in the context, say so.
    """
    
    # 4. Get answer from Gemini
    response = await self.model.generate_content_async(prompt)
    
    # 5. Extract sources
    sources = [chunk['text'][:200] + "..." for chunk in relevant_chunks]
    
    return {
        "answer": response.text,
        "sources": sources,
        "confidence": 0.8  # Can calculate based on similarity scores
    }
```

#### 3.2 Update Chat Route (`api/routes/chat.py`)

Uncomment the TODO code and connect to chat_service:

```python
if contract_id:
    result = await chat_service.answer_contract_question(
        question=message,
        contract_id=contract_id
    )
else:
    result = await chat_service.answer_general_question(
        question=message,
        user_id=current_user.id
    )

ai_response = result['answer']
sources = result['sources']
```

---

### Phase 4: Complete Upload Pipeline

#### 4.1 Update Upload Route (`api/routes/upload.py`)

Uncomment and complete the pipeline:

```python
# After saving file to disk...

# Step 1: Extract text
if file_type == FileType.pdf:
    text = await OCRService.extract_text_from_pdf(file_path)
else:
    text = await OCRService.extract_text_from_docx(file_path)

# Step 2: Extract structured data
extracted_data = await extraction_service.extract_all(text)

# Save parties
for party_data in extracted_data['parties']:
    party = ContractParty(
        contract_id=contract.id,
        name=party_data['name'],
        type=PartyType[party_data['type']],
        role=PartyRole[party_data['role']]
    )
    db.add(party)

# Save dates, financial terms similarly...

# Step 3: Analyze risks
risks = await risk_service.analyze_risks(text, extracted_data)
for risk_data in risks:
    risk = Risk(
        contract_id=contract.id,
        risk_type=RiskType[risk_data['risk_type']],
        severity=RiskSeverity[risk_data['severity']],
        title=risk_data['title'],
        description=risk_data['description'],
        recommendation=risk_data.get('recommendation'),
        clause_reference=risk_data.get('clause_reference')
    )
    db.add(risk)

# Step 4: Generate summary
summary_data = await summary_service.generate_summary(text, extracted_data, risks)
contract.summary = summary_data['summary']
contract.purpose = summary_data['purpose']
contract.scope = summary_data['scope']

# Step 5: Index for RAG
await rag_service.index_contract(contract.id, text)

# Step 6: Update status
contract.status = ContractStatus.completed
await db.commit()
```

---

## 🔧 Testing Your Implementation

### Test Extraction
```python
# Create a test contract
test_text = """
This Service Agreement is entered into on January 1, 2024
between ABC Corp (Client) and XYZ Services LLC (Vendor).
The total contract value is $50,000...
"""

result = await extraction_service.extract_all(test_text)
print(result['parties'])  # Should show ABC Corp and XYZ Services
print(result['financial_terms'])  # Should show $50,000
```

### Test Risk Analysis
```python
risks = await risk_service.analyze_risks(test_text)
print(f"Found {len(risks)} risks")
for risk in risks:
    print(f"- {risk['severity']}: {risk['title']}")
```

### Test Summary
```python
summary = await summary_service.generate_executive_summary(test_text)
print(summary)
```

### Test RAG
```python
await rag_service.index_contract("test-123", test_text)
results = await rag_service.search_contract("test-123", "What is the payment amount?")
print(results)
```

### Test Chat
```python
answer = await chat_service.answer_contract_question(
    "What is the contract value?",
    "test-123"
)
print(answer['answer'])
print(answer['sources'])
```

---

## 🎓 Helpful Resources

### Gemini API
- Quickstart: https://ai.google.dev/tutorials/python_quickstart
- Embeddings: https://ai.google.dev/api/embeddings
- Prompting Guide: https://ai.google.dev/docs/prompting_intro

### RAG Concepts
- ChromaDB (vector DB): https://docs.trychroma.com/
- Cosine Similarity: https://en.wikipedia.org/wiki/Cosine_similarity

### FastAPI
- Background Tasks: https://fastapi.tiangolo.com/tutorial/background-tasks/
- Async/Await: https://fastapi.tiangolo.com/async/

---

## ⚠️ Common Pitfalls

1. **Token Limits**: Gemini has token limits. Don't send entire contract in one prompt. Use RAG.

2. **Async/Await**: All service methods are async. Don't forget `await`.

3. **JSON Parsing**: Gemini might not always return perfect JSON. Add error handling.

4. **Database Sessions**: Commit changes to database after creating records.

5. **Embeddings Storage**: Start with in-memory for MVP, but plan for persistent storage.

---

## 📞 Questions?

Check the TODO comments in each service file. They have specific implementation hints!
