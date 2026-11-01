# 🌍 Arabic/English Language System

## Overview
Complete bilingual support (English/Arabic) with RTL (Right-to-Left) layout support, automatic font switching, and localStorage persistence.

## Features

### ✨ Implemented
- **Language Switcher Component** - Beautiful animated button with globe icon
- **Translation Context** - React Context API for global language state
- **200+ Translations** - Comprehensive translation keys for all pages
- **RTL Support** - Automatic direction switching (ltr/rtl)
- **Font Switching** - Inter for English, Cairo for Arabic
- **localStorage Persistence** - Language preference saved
- **Smooth Animations** - Animated language transitions

## Architecture

### Files Structure
```
src/
├── contexts/
│   └── LanguageContext.tsx      # Translation provider & hook
├── components/
│   └── LanguageSwitcher.tsx     # Language toggle button
└── app/
    ├── layout.tsx               # Wrapped with LanguageProvider
    └── [pages]/                 # Use useLanguage() hook
```

### How It Works

1. **LanguageContext.tsx** - Central translation system
   - Stores all translations (en/ar)
   - Provides `useLanguage()` hook
   - Manages language state
   - Updates HTML `dir` attribute
   - Persists to localStorage

2. **LanguageSwitcher.tsx** - UI Component
   - Shows current language opposite (English → show العربية)
   - Animated globe icon
   - Hover effects
   - Arrow animation based on direction

3. **Usage in Components**
   ```tsx
   import { useLanguage } from '@/contexts/LanguageContext';
   
   function MyComponent() {
     const { t, language } = useLanguage();
     
     return <h1>{t('common.welcome')}</h1>
   }
   ```

## Translation Keys

### Navigation
- `nav.dashboard` - "Dashboard" / "لوحة التحكم"
- `nav.upload` - "Upload" / "رفع"
- `nav.contracts` - "Contracts" / "العقود"
- `nav.logout` - "Logout" / "تسجيل خروج"

### Authentication
- `auth.login` - "Login" / "تسجيل الدخول"
- `auth.signup` - "Sign Up" / "إنشاء حساب"
- `auth.email` - "Email Address" / "البريد الإلكتروني"
- `auth.password` - "Password" / "كلمة المرور"
- `auth.noAccount` - "Don't have an account?" / "ليس لديك حساب؟"
- `auth.signUpHere` - "Sign up here" / "أنشئ حسابك هنا"

### Dashboard
- `dashboard.title` - "AI CLM Dashboard" / "لوحة تحكم إدارة دورة حياة العقود"
- `dashboard.welcomeBack` - "Welcome back" / "مرحباً بعودتك"
- `dashboard.stats.total` - "Total Contracts" / "إجمالي العقود"
- `dashboard.stats.active` - "Active Reviews" / "المراجعات النشطة"
- `dashboard.quickActions` - "Quick Actions" / "إجراءات سريعة"
- `dashboard.recentUploads` - "Recent Uploads" / "آخر الملفات المرفوعة"

### Upload
- `upload.title` - "Upload Contract" / "رفع عقد"
- `upload.dragDrop` - "Drag and drop your contract here" / "اسحب وأفلت عقدك هنا"
- `upload.browse` - "Browse Files" / "تصفح الملفات"
- `upload.analyzing` - "Analyzing contract with AI..." / "جاري تحليل العقد..."
- `upload.success` - "Contract uploaded successfully!" / "تم رفع العقد بنجاح!"

### Contracts
- `contracts.title` - "All Contracts" / "جميع العقود"
- `contracts.filters` - "Filters" / "التصفية"
- `contracts.search` - "Search contracts..." / "البحث في العقود..."
- `contracts.industry` - "Industry" / "الصناعة"
- `contracts.governingLaw` - "Governing Law" / "القانون الحاكم"
- `contracts.status` - "Status" / "الحالة"
- `contracts.aiAssistant` - "AI Assistant" / "المساعد الذكي"
- `contracts.noContracts` - "No contracts found" / "لم يتم العثور على عقود"

### Common
- `common.loading` - "Loading..." / "جاري التحميل..."
- `common.welcome` - "Welcome" / "مرحباً"
- `common.search` - "Search" / "بحث"
- `common.save` - "Save" / "حفظ"
- `common.cancel` - "Cancel" / "إلغاء"

## RTL Support

### CSS Classes
```css
/* Automatic RTL support */
html[dir="rtl"] {
  font-family: var(--font-cairo), sans-serif;
}

html[dir="ltr"] {
  font-family: var(--font-inter), sans-serif;
}
```

### Tailwind RTL Utilities
```tsx
// Use rtl: prefix for RTL-specific styles
<div className="pl-4 rtl:pl-0 rtl:pr-4">
  <input className="input pl-10 rtl:pl-4 rtl:pr-10" />
</div>

// Reverse flex direction
<div className="flex space-x-4 rtl:space-x-reverse">
```

### Icon Flipping
```tsx
// Arrows that flip in RTL
<svg className="rtl:rotate-180">
  <path d="M13 7l5 5m0 0l-5 5m5-5H6" />
</svg>

// Hover animations that respect direction
<svg className="group-hover:translate-x-1 rtl:group-hover:-translate-x-1">
```

## Adding New Translations

### Step 1: Add to LanguageContext.tsx
```tsx
const translations: Record<Language, Record<string, string>> = {
  en: {
    'mypage.title': 'My Page Title',
    'mypage.description': 'Description text',
  },
  ar: {
    'mypage.title': 'عنوان صفحتي',
    'mypage.description': 'نص الوصف',
  },
};
```

### Step 2: Use in Component
```tsx
import { useLanguage } from '@/contexts/LanguageContext';

function MyPage() {
  const { t } = useLanguage();
  
  return (
    <div>
      <h1>{t('mypage.title')}</h1>
      <p>{t('mypage.description')}</p>
    </div>
  );
}
```

## Language Switcher Placement

### Already Integrated In:
- ✅ **Header Component** - Shows in all authenticated pages (dashboard, upload, contracts)
- ✅ **Login Page** - Top-right corner
- ⏳ **Signup Page** - Needs integration
- ⏳ **Contract Detail Page** - Needs integration

### How to Add to New Page:
```tsx
import LanguageSwitcher from '@/components/LanguageSwitcher';

export default function MyPage() {
  return (
    <div>
      <div className="absolute top-6 right-6 z-20">
        <LanguageSwitcher />
      </div>
      {/* Rest of page */}
    </div>
  );
}
```

## Font Configuration

### Google Fonts Setup (layout.tsx)
```tsx
import { Inter, Cairo } from "next/font/google";

const inter = Inter({ 
  subsets: ["latin"],
  variable: '--font-inter',
});

const cairo = Cairo({
  subsets: ["arabic", "latin"],
  variable: '--font-cairo',
});
```

## Browser Compatibility
- ✅ Chrome/Edge - Full support
- ✅ Firefox - Full support
- ✅ Safari - Full support
- ✅ Mobile Browsers - Full support
- ✅ RTL Layout - Native browser support

## Performance
- **Bundle Size**: Minimal impact (~15KB for all translations)
- **Font Loading**: Optimized with Next.js font optimization
- **State Management**: React Context (no external dependencies)
- **Persistence**: localStorage (instant load on revisit)

## Testing

### Manual Testing
1. Open any page
2. Click language switcher
3. Verify:
   - Text changes to Arabic
   - Layout flips to RTL
   - Font changes to Cairo
   - Icons flip correctly
4. Refresh page
5. Verify language persists

### Key Test Cases
- [ ] Login page translation
- [ ] Dashboard stats translation
- [ ] Navigation tabs translation
- [ ] Upload page translation
- [ ] Contracts page translation
- [ ] RTL input fields work correctly
- [ ] Language persists after refresh
- [ ] Font switches automatically

## Future Enhancements
- [ ] Add more pages (signup, contract detail, etc.)
- [ ] Add language selector dropdown (for 3+ languages)
- [ ] Add translation file splitting for better performance
- [ ] Add translation management tool
- [ ] Add missing translation warning in dev mode
- [ ] Add language detection from browser

## Troubleshooting

### Translation Not Showing
- Check translation key exists in LanguageContext.tsx
- Verify `useLanguage()` hook is being called
- Check console for errors

### RTL Not Working
- Verify `html[dir="rtl"]` CSS is in globals.css
- Check Tailwind config includes RTL utilities
- Use `rtl:` prefix for RTL-specific styles

### Language Not Persisting
- Check localStorage is enabled in browser
- Verify LanguageProvider wraps entire app
- Check browser console for localStorage errors

## Support
For issues or questions about the language system:
1. Check this documentation
2. Review LanguageContext.tsx comments
3. Test with browser dev tools
4. Check console for errors
