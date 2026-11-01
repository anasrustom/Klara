# 🚀 Quick Start Guide - AI CLM Platform

## Project Overview
This is an AI-powered Contract Lifecycle Management (CLM) platform with:
- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS
- **Backend**: Python FastAPI + SQLAlchemy
- **Database**: SQLite
- **AI**: Google Gemini API (to be integrated)

---

## 📁 Project Structure
```
AIX-Hackathon/
├── frontend/          # Next.js application (READY TO USE)
├── backend/           # FastAPI server (NEEDS AI IMPLEMENTATION)
├── database/          # Schema reference
└── README.md          # Full documentation
```

---

## ⚡ Quick Setup (5 minutes)

### Step 1: Frontend Setup
```powershell
cd frontend
npm install
npm run dev
```
✅ Frontend ready at http://localhost:3000

### Step 2: Backend Setup
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Edit .env and add your GEMINI_API_KEY
python main.py
```
✅ Backend ready at http://localhost:8000
✅ API Docs at http://localhost:8000/docs

---

## 🎯 What's Already Done

### ✅ Frontend (100% Ready)
- Login/Signup pages
- Dashboard with statistics
- Contract upload page (with PDF/DOCX validation)
- Contracts list with filters and search
- Contract detail page with tabs
- Mini chat interface
- All TypeScript types defined
- Tailwind CSS styling

### ✅ Backend (Structure Ready)
- All API routes created (with placeholders)
- Database models (User, Contract, Risk, Clause, etc.)
- JWT authentication working
- File upload handling
- SQLite database auto-creation

### ✅ Database
- Complete schema designed
- 8 tables with relationships
- Automatic creation via SQLAlchemy

---

## 🔧 What Backend Team Needs to Do

### Priority 1: AI Integration
**File**: `backend/src/services/ai_service.py`

Implement:
```python
async def analyze_contract(contract_text: str):
    # 1. Call Gemini API
    # 2. Extract: parties, dates, financial terms, governing law
    # 3. Assess risks
    # 4. Generate summary
    # 5. Return structured data
```

### Priority 2: Document Processing
**File**: `backend/src/services/ocr_service.py`

Complete:
```python
async def extract_text_from_pdf(file_path: str):
    # PyPDF2 is already installed
    # Extract and clean text
```

### Priority 3: Connect Upload → AI → Database
**File**: `backend/src/api/routes/upload.py`

Add after file save:
```python
# Extract text
text = await OCRService.extract_text_from_pdf(file_path)

# Analyze with AI
analysis = await AIService.analyze_contract(text)

# Save to database
# Create Risk, Party, KeyDate, FinancialTerm records
```

### Priority 4: Chat Implementation
**File**: `backend/src/api/routes/chat.py`

Implement:
```python
async def ask_question(message: str, contract_id: str):
    # Get contract text
    # Call Gemini with context
    # Return answer
```

---

## 🔑 Environment Setup

### Frontend `.env.local`
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Backend `.env`
```
DATABASE_URL=sqlite:///./clm_database.db
SECRET_KEY=change-this-to-random-string
GEMINI_API_KEY=your-gemini-api-key-here
```

**Get Gemini API Key**: https://makersuite.google.com/app/apikey

---

## 📋 Test Checklist

### Frontend Tests
1. ✅ Navigate to http://localhost:3000
2. ✅ Sign up with new account
3. ✅ Login with credentials
4. ✅ View dashboard
5. ✅ Go to upload page
6. ✅ Try uploading a PDF (will work after backend integration)
7. ✅ View contracts list
8. ✅ Check filters and search

### Backend Tests
1. ✅ Visit http://localhost:8000/docs
2. ✅ Test POST /api/auth/signup
3. ✅ Test POST /api/auth/login
4. ✅ Test GET /api/contracts (with token)
5. ⏳ Test POST /api/contracts/upload (needs AI implementation)
6. ⏳ Test POST /api/chat (needs AI implementation)

---

## 🐛 Common Issues & Solutions

### Frontend: TypeScript Errors
**Problem**: Red squiggles everywhere
**Solution**: Run `npm install` first

### Backend: Import Errors
**Problem**: `ModuleNotFoundError`
**Solution**: 
```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Backend: Database Not Created
**Problem**: No `clm_database.db` file
**Solution**: Just run `python main.py` - it auto-creates

### Frontend: Can't Connect to Backend
**Problem**: API calls fail
**Solution**: 
1. Check backend is running on port 8000
2. Check `.env.local` has correct API URL
3. Check CORS settings in `backend/main.py`

---

## 📚 Key Files Reference

### Frontend
- `src/app/*/page.tsx` - All pages
- `src/types/index.ts` - TypeScript types
- `src/app/globals.css` - Global styles

### Backend
- `main.py` - FastAPI app entry point
- `src/api/routes/*.py` - API endpoints
- `src/models/*.py` - Database models
- `src/services/*.py` - **YOUR WORK HERE**

### Database
- Auto-created at `backend/clm_database.db`
- Schema reference: `database/schema.sql`

---

## 🎓 Learning Resources

### Next.js
- Docs: https://nextjs.org/docs
- App Router: https://nextjs.org/docs/app

### FastAPI
- Docs: https://fastapi.tiangolo.com/
- Tutorial: https://fastapi.tiangolo.com/tutorial/

### Gemini API
- Docs: https://ai.google.dev/docs
- Python SDK: https://ai.google.dev/tutorials/python_quickstart

---

## 🤝 Team Workflow

1. **Frontend Team**: Test UI, report issues, refine UX
2. **Backend Team**: Implement AI services, test with frontend
3. **Integration**: Test end-to-end workflow together

---

## 🎯 Demo Scenario

For hackathon demo:
1. Sign up as "Legal Officer"
2. Upload sample contract PDF
3. Show AI analysis (parties, dates, risks)
4. Ask questions in chat
5. Show dashboard statistics

---

## 📞 Need Help?

- Check `README.md` for full details
- Frontend guide: `frontend/SETUP.md`
- Backend guide: `backend/SETUP.md`
- API docs: http://localhost:8000/docs (when running)

---

**Ready to code? Start with backend AI integration! 🚀**
