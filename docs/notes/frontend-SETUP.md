# Frontend Installation & Setup Guide

## Quick Start

1. **Install Dependencies**
   ```powershell
   cd frontend
   npm install
   ```

2. **Create Environment File**
   ```powershell
   copy .env.example .env.local
   ```

3. **Start Development Server**
   ```powershell
   npm run dev
   ```

4. **Open in Browser**
   Navigate to: http://localhost:3000

## Pages Available

- `/` - Auto-redirects to login or dashboard
- `/login` - User login
- `/signup` - User registration
- `/dashboard` - Main dashboard with stats
- `/upload` - Upload contracts
- `/contracts` - List all contracts with filters
- `/contracts/[id]` - Contract detail page

## Environment Variables

Create `.env.local` file:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Notes for Frontend Team

- All pages are ready to use
- TypeScript types are defined in `src/types/index.ts`
- API calls are set up but will need backend running
- File upload validation is implemented (PDF/DOCX, max 10MB)
- Mock data is used when backend is not available

## Common Commands

```powershell
npm run dev      # Start development server
npm run build    # Build for production
npm run start    # Start production server
npm run lint     # Run ESLint
```
