'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

type Language = 'en' | 'ar';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

// Translations
const translations: Record<Language, Record<string, string>> = {
  en: {
    // Navigation
    'nav.dashboard': 'Dashboard',
    'nav.upload': 'Upload',
    'nav.contracts': 'Contracts',
    'nav.logout': 'Logout',
    
    // Common
    'common.loading': 'Loading...',
    'common.welcome': 'Welcome',
    'common.search': 'Search',
    'common.filter': 'Filter',
    'common.all': 'All',
    'common.save': 'Save',
    'common.cancel': 'Cancel',
    'common.delete': 'Delete',
    'common.edit': 'Edit',
    'common.view': 'View',
    'common.download': 'Download',
    'common.hide': 'Hide',
    'common.show': 'Show',
    'common.more': 'more',
    
    // Auth
    'auth.login': 'Login',
    'auth.signup': 'Sign Up',
    'auth.email': 'Email Address',
    'auth.password': 'Password',
    'auth.fullName': 'Full Name',
    'auth.confirmPassword': 'Confirm Password',
    'auth.rememberMe': 'Remember me',
    'auth.forgotPassword': 'Forgot password?',
    'auth.noAccount': "Don't have an account?",
    'auth.hasAccount': 'Already have an account?',
    'auth.signInHere': 'Sign in here',
    'auth.signUpHere': 'Sign up here',
    'auth.name': 'Full Name',
    'auth.role': 'Role',
    'auth.creatingAccount': 'Creating account...',
    'auth.haveAccount': 'Already have an account?',
    
    // Dashboard
    'dashboard.title': 'Klara Dashboard',
    'dashboard.subtitle': 'Your intelligent contract lifecycle management system',
    'dashboard.welcomeBack': 'Welcome back',
    'dashboard.stats.total': 'Total Contracts',
    'dashboard.stats.awaiting': 'Awaiting Review',
    'dashboard.stats.risks': 'High Risk Items',
    'dashboard.stats.expiring': 'Expiring Soon',
    'dashboard.stats.days': 'days',
    'dashboard.quickActions': 'Quick Actions',
    'dashboard.action.upload': 'Upload Contract',
    'dashboard.action.uploadDesc': 'Add new contract for AI analysis',
    'dashboard.action.view': 'View All Contracts',
    'dashboard.action.viewDesc': 'Browse and manage contracts',
    'dashboard.action.chat': 'Ask AI Assistant',
    'dashboard.action.chatDesc': 'Get instant contract insights',
    'dashboard.recentUploads': 'Recent Uploads',
    'dashboard.viewAll': 'View all contracts',
    'dashboard.noUploads': 'No contracts uploaded yet',
    'dashboard.getStarted': 'Get started by uploading your first contract',
    
    // Upload
    'upload.title': 'Upload Contract',
    'upload.dragDrop': 'Drag and drop your contract here',
    'upload.or': 'or',
    'upload.browse': 'Browse Files',
    'upload.supported': 'Supported formats: PDF, DOCX (Max 10MB)',
    'upload.uploading': 'Uploading',
    'upload.analyzing': 'Analyzing contract with AI...',
    'upload.success': 'Contract uploaded successfully!',
    'upload.error': 'Upload failed. Please try again.',
    'upload.selectFile': 'Please select a file',
    'upload.features': 'What happens next?',
    'upload.feature.extract': 'AI extracts key clauses',
    'upload.feature.analyze': 'Risk analysis performed',
    'upload.feature.summary': 'Summary generated',
    'upload.feature.chat': 'Ask questions anytime',
    
    // Contracts
    'contracts.title': 'All Contracts',
    'contracts.filters': 'Filters',
    'contracts.search': 'Search contracts...',
    'contracts.industry': 'Industry',
    'contracts.allIndustries': 'All Industries',
    'contracts.industry.technology': 'Technology',
    'contracts.industry.finance': 'Finance',
    'contracts.industry.healthcare': 'Healthcare',
    'contracts.industry.manufacturing': 'Manufacturing',
    'contracts.governingLaw': 'Governing Law',
    'contracts.allLaws': 'All Laws',
    'contracts.status': 'Status',
    'contracts.allStatuses': 'All Statuses',
    'contracts.status.completed': 'Completed',
    'contracts.status.processing': 'Processing',
    'contracts.status.pending': 'Pending',
    'contracts.status.failed': 'Failed',
    'contracts.aiAssistant': 'AI Assistant',
    'contracts.askQuestion': 'Ask about contracts...',
    'contracts.noContracts': 'No contracts found',
    'contracts.getStarted': 'Get started by uploading your first contract for AI analysis',
    'contracts.uploadContract': 'Upload Contract',
    'contracts.analysisInProgress': 'AI analysis in progress...',
    'contracts.risks': 'risks',
    'contracts.more': 'more',
    
    // Contract Detail
    'detail.backToContracts': 'Back to Contracts',
    'detail.summary': 'Summary',
    'detail.clauses': 'Key Clauses',
    'detail.risks': 'Risk Analysis',
    'detail.chat': 'Ask Questions',
    'detail.noSummary': 'Summary is being generated...',
    'detail.noClauses': 'No clauses extracted yet',
    'detail.noRisks': 'No risks identified',
    'detail.riskLevel': 'Risk Level',
    'detail.mitigation': 'Mitigation',

    // Contract Detail: analysis, labels and chat
    'detail.loading': "Loading contract...",
    'detail.notFound': "Contract not found",
    'detail.edit': "Edit Contract",
    'detail.saveChanges': "Save Changes",
    'detail.saveFailed': "Failed to save changes. Please try again.",
    'detail.tab.overview': "Overview",
    'detail.tab.parties': "Parties & Dates",
    'detail.contractStatus': "Contract Status",
    'detail.contractSummary': "Contract Summary",
    'detail.summaryPlaceholder': "Enter contract summary...",
    'detail.purpose': "Purpose",
    'detail.scope': "Scope",
    'detail.highlights': "Key Highlights",
    'detail.contractType': "Contract Type",
    'detail.industry': "Industry",
    'detail.governingLaw': "Governing Law",
    'detail.jurisdiction': "Jurisdiction",
    'detail.notStated': "Not stated",
    'detail.financialTerms': "Financial Terms",
    'detail.noFinancialTerms': "No financial terms identified.",
    'detail.amountNotStated': "No amount stated",
    'detail.topRisks': "Top Risks",
    'detail.allRisks': "All Risks",
    'detail.noHighRisks': "No high-severity risks identified.",
    'detail.recommendation': "Recommendation",
    'detail.source': "Source",
    'detail.page': "Page",
    'detail.reference': "Reference",
    'detail.type': "Type",
    'detail.role': "Role",
    'detail.parties': "Contracting Parties",
    'detail.noParties': "No parties identified.",
    'detail.keyDates': "Key Dates",
    'detail.noDates': "The contract states no calendar dates.",
    'detail.undatedTerms': "Dates set by events",
    'detail.obligations': "Key Obligations",
    'detail.addRisk': "Add Risk",
    'detail.riskTitle': "Risk Title",
    'detail.riskTitlePlaceholder': "Enter risk title...",
    'detail.description': "Description",
    'detail.descriptionPlaceholder': "Describe the risk...",
    'detail.severity': "Severity",
    'detail.riskType': "Risk Type",
    'detail.recommendationOptional': "Recommendation (optional)",
    'detail.recommendationPlaceholder': "Enter recommendation...",
    'detail.riskAddFailed': "Failed to add risk. Please try again.",
    'detail.riskDeleteFailed': "Failed to delete risk. Please try again.",
    'detail.notAnalyzed': "This contract has not been analyzed yet.",
    'detail.analysisFailed': "The last AI analysis did not finish.",
    'detail.runAnalysis': "Run AI analysis",
    'detail.analyzing': "Analyzing contract...",
    'detail.askKlara': "Ask Klara AI",
    'detail.askKlaraDesc': "Ask anything about this contract. Every answer cites the passage it comes from.",
    'detail.riskProfile': "Risk Profile",
    'detail.pages': "pages",
    'detail.lang.en': "English",
    'detail.lang.ar': "Arabic",

    'riskType.missing_clause': "Missing Clause",
    'riskType.unusual_clause': "Unusual Clause",
    'riskType.non_standard': "Non-Standard",
    'riskType.inconsistency': "Inconsistency",
    'riskType.compliance': "Compliance",

    'role.client': "Client",
    'role.vendor': "Vendor",
    'role.partner': "Partner",
    'role.other': "Other",

    'partyType.organization': "Organization",
    'partyType.individual': "Individual",

    'dateType.effective_date': "Effective Date",
    'dateType.expiration_date': "Expiration Date",
    'dateType.renewal_date': "Renewal Date",
    'dateType.milestone': "Milestone",
    'dateType.other': "Other Date",

    'termType.payment': "Payment",
    'termType.penalty': "Penalty",
    'termType.deposit': "Deposit",
    'termType.other': "Other",

    'chat.title': "Klara AI",
    'chat.subtitle.contract': "Answers from this contract, with sources",
    'chat.subtitle.portfolio': "Answers from all your contracts, with sources",
    'chat.welcome.contract': "Ask me anything about this contract. I answer only from its text and show you the passage behind every answer.",
    'chat.welcome.portfolio': "Ask me anything about your contracts. I search all of them and show you the passage behind every answer.",
    'chat.suggest.contract.1': "Who can terminate for convenience, and with how much notice?",
    'chat.suggest.contract.2': "Is there a cap on liability?",
    'chat.suggest.contract.3': "What are the payment terms?",
    'chat.suggest.portfolio.1': "Which contracts allow termination for convenience?",
    'chat.suggest.portfolio.2': "Which governing laws apply across my contracts?",
    'chat.placeholder': "Ask a question...",
    'chat.send': "Send",
    'chat.thinking': "Reading the contract...",
    'chat.hint': "Enter to send · Shift+Enter for a new line",
    'chat.error': "Klara could not answer right now. Please try again.",
    'chat.sessionExpired': "Your session has expired. Please log in again.",
    'chat.notFound': "This contract could not be found.",
    'chat.sources': "Sources",
    'chat.page': "p.",
    'chat.source': "Source",
    'chat.openContract': "Open contract",
    'chat.clear': "Clear chat",
    'chat.retry': "Retry",
    'chat.close': "Close",
    
    // Risk Levels
    'risk.critical': 'Critical',
    'risk.high': 'High',
    'risk.medium': 'Medium',
    'risk.low': 'Low',
    
    // Languages
    'lang.english': 'English',
    'lang.arabic': 'العربية',
    'lang.bilingual': 'English & Arabic Support',
  },
  ar: {
    // Navigation
    'nav.dashboard': 'لوحة التحكم',
    'nav.upload': 'رفع',
    'nav.contracts': 'العقود',
    'nav.logout': 'تسجيل خروج',
    
    // Common
    'common.loading': 'جاري التحميل...',
    'common.welcome': 'مرحباً',
    'common.search': 'بحث',
    'common.filter': 'تصفية',
    'common.all': 'الكل',
    'common.save': 'حفظ',
    'common.cancel': 'إلغاء',
    'common.delete': 'حذف',
    'common.edit': 'تعديل',
    'common.view': 'عرض',
    'common.download': 'تحميل',
    'common.hide': 'إخفاء',
    'common.show': 'إظهار',
    'common.more': 'المزيد',
    
    // Auth
    'auth.login': 'تسجيل الدخول',
    'auth.signup': 'إنشاء حساب',
    'auth.email': 'البريد الإلكتروني',
    'auth.password': 'كلمة المرور',
    'auth.fullName': 'الاسم الكامل',
    'auth.confirmPassword': 'تأكيد كلمة المرور',
    'auth.rememberMe': 'تذكرني',
    'auth.forgotPassword': 'نسيت كلمة المرور؟',
    'auth.noAccount': 'ليس لديك حساب؟',
    'auth.hasAccount': 'لديك حساب بالفعل؟',
    'auth.signInHere': 'سجل دخولك هنا',
    'auth.signUpHere': 'أنشئ حسابك هنا',
    'auth.name': 'الاسم الكامل',
    'auth.role': 'الدور',
    'auth.creatingAccount': 'جاري إنشاء الحساب...',
    'auth.haveAccount': 'لديك حساب بالفعل؟',
    
    // Dashboard
    'dashboard.title': 'لوحة تحكم كلارا',
    'dashboard.subtitle': 'نظامك الذكي لإدارة دورة حياة العقود',
    'dashboard.welcomeBack': 'مرحباً بعودتك',
    'dashboard.stats.total': 'إجمالي العقود',
    'dashboard.stats.awaiting': 'بانتظار المراجعة',
    'dashboard.stats.risks': 'العناصر عالية المخاطر',
    'dashboard.stats.expiring': 'تنتهي قريباً',
    'dashboard.stats.days': 'أيام',
    'dashboard.quickActions': 'إجراءات سريعة',
    'dashboard.action.upload': 'رفع عقد',
    'dashboard.action.uploadDesc': 'إضافة عقد جديد للتحليل بالذكاء الاصطناعي',
    'dashboard.action.view': 'عرض جميع العقود',
    'dashboard.action.viewDesc': 'تصفح وإدارة العقود',
    'dashboard.action.chat': 'اسأل المساعد الذكي',
    'dashboard.action.chatDesc': 'احصل على رؤى فورية للعقود',
    'dashboard.recentUploads': 'آخر الملفات المرفوعة',
    'dashboard.viewAll': 'عرض جميع العقود',
    'dashboard.noUploads': 'لا توجد عقود مرفوعة بعد',
    'dashboard.getStarted': 'ابدأ برفع عقدك الأول',
    
    // Upload
    'upload.title': 'رفع عقد',
    'upload.dragDrop': 'اسحب وأفلت عقدك هنا',
    'upload.or': 'أو',
    'upload.browse': 'تصفح الملفات',
    'upload.supported': 'الصيغ المدعومة: PDF، DOCX (حد أقصى 10 ميجابايت)',
    'upload.uploading': 'جاري الرفع',
    'upload.analyzing': 'جاري تحليل العقد بالذكاء الاصطناعي...',
    'upload.success': 'تم رفع العقد بنجاح!',
    'upload.error': 'فشل الرفع. يرجى المحاولة مرة أخرى.',
    'upload.selectFile': 'يرجى تحديد ملف',
    'upload.features': 'ماذا يحدث بعد ذلك؟',
    'upload.feature.extract': 'الذكاء الاصطناعي يستخرج البنود الرئيسية',
    'upload.feature.analyze': 'يتم إجراء تحليل المخاطر',
    'upload.feature.summary': 'يتم إنشاء الملخص',
    'upload.feature.chat': 'اطرح الأسئلة في أي وقت',
    
    // Contracts
    'contracts.title': 'جميع العقود',
    'contracts.filters': 'التصفية',
    'contracts.search': 'البحث في العقود...',
    'contracts.industry': 'الصناعة',
    'contracts.allIndustries': 'جميع الصناعات',
    'contracts.industry.technology': 'التكنولوجيا',
    'contracts.industry.finance': 'المالية',
    'contracts.industry.healthcare': 'الرعاية الصحية',
    'contracts.industry.manufacturing': 'التصنيع',
    'contracts.governingLaw': 'القانون الحاكم',
    'contracts.allLaws': 'جميع القوانين',
    'contracts.status': 'الحالة',
    'contracts.allStatuses': 'جميع الحالات',
    'contracts.status.completed': 'مكتمل',
    'contracts.status.processing': 'قيد المعالجة',
    'contracts.status.pending': 'معلق',
    'contracts.status.failed': 'فشل',
    'contracts.aiAssistant': 'المساعد الذكي',
    'contracts.askQuestion': 'اسأل عن العقود...',
    'contracts.noContracts': 'لم يتم العثور على عقود',
    'contracts.getStarted': 'ابدأ برفع عقدك الأول لتحليله بالذكاء الاصطناعي',
    'contracts.uploadContract': 'رفع عقد',
    'contracts.analysisInProgress': 'التحليل بالذكاء الاصطناعي قيد التقدم...',
    'contracts.risks': 'مخاطر',
    'contracts.more': 'المزيد',
    
    // Contract Detail
    'detail.backToContracts': 'العودة إلى العقود',
    'detail.summary': 'الملخص',
    'detail.clauses': 'البنود الرئيسية',
    'detail.risks': 'تحليل المخاطر',
    'detail.chat': 'طرح الأسئلة',
    'detail.noSummary': 'جاري إنشاء الملخص...',
    'detail.noClauses': 'لم يتم استخراج بنود بعد',
    'detail.noRisks': 'لم يتم تحديد مخاطر',
    'detail.riskLevel': 'مستوى المخاطر',
    'detail.mitigation': 'التخفيف',

    // Contract Detail: analysis, labels and chat
    'detail.loading': "جاري تحميل العقد...",
    'detail.notFound': "العقد غير موجود",
    'detail.edit': "تعديل العقد",
    'detail.saveChanges': "حفظ التغييرات",
    'detail.saveFailed': "تعذر حفظ التغييرات. يرجى المحاولة مرة أخرى.",
    'detail.tab.overview': "نظرة عامة",
    'detail.tab.parties': "الأطراف والتواريخ",
    'detail.contractStatus': "حالة العقد",
    'detail.contractSummary': "ملخص العقد",
    'detail.summaryPlaceholder': "أدخل ملخص العقد...",
    'detail.purpose': "الغرض",
    'detail.scope': "النطاق",
    'detail.highlights': "أبرز النقاط",
    'detail.contractType': "نوع العقد",
    'detail.industry': "القطاع",
    'detail.governingLaw': "القانون الحاكم",
    'detail.jurisdiction': "الاختصاص القضائي",
    'detail.notStated': "غير مذكور",
    'detail.financialTerms': "الشروط المالية",
    'detail.noFinancialTerms': "لم يتم تحديد شروط مالية.",
    'detail.amountNotStated': "لم يذكر مبلغ",
    'detail.topRisks': "أهم المخاطر",
    'detail.allRisks': "جميع المخاطر",
    'detail.noHighRisks': "لم يتم تحديد مخاطر عالية الخطورة.",
    'detail.recommendation': "التوصية",
    'detail.source': "المصدر",
    'detail.page': "صفحة",
    'detail.reference': "المرجع",
    'detail.type': "النوع",
    'detail.role': "الدور",
    'detail.parties': "أطراف العقد",
    'detail.noParties': "لم يتم تحديد أطراف.",
    'detail.keyDates': "التواريخ الرئيسية",
    'detail.noDates': "لا يذكر العقد تواريخ محددة.",
    'detail.undatedTerms': "تواريخ مرتبطة بأحداث",
    'detail.obligations': "الالتزامات الرئيسية",
    'detail.addRisk': "إضافة خطر",
    'detail.riskTitle': "عنوان الخطر",
    'detail.riskTitlePlaceholder': "أدخل عنوان الخطر...",
    'detail.description': "الوصف",
    'detail.descriptionPlaceholder': "صف الخطر...",
    'detail.severity': "درجة الخطورة",
    'detail.riskType': "نوع الخطر",
    'detail.recommendationOptional': "التوصية (اختياري)",
    'detail.recommendationPlaceholder': "أدخل التوصية...",
    'detail.riskAddFailed': "تعذر إضافة الخطر. يرجى المحاولة مرة أخرى.",
    'detail.riskDeleteFailed': "تعذر حذف الخطر. يرجى المحاولة مرة أخرى.",
    'detail.notAnalyzed': "لم يتم تحليل هذا العقد بعد.",
    'detail.analysisFailed': "لم يكتمل آخر تحليل بالذكاء الاصطناعي.",
    'detail.runAnalysis': "تشغيل التحليل الذكي",
    'detail.analyzing': "جاري تحليل العقد...",
    'detail.askKlara': "اسأل كلارا",
    'detail.askKlaraDesc': "اسأل أي سؤال عن هذا العقد. كل إجابة تشير إلى النص الذي جاءت منه.",
    'detail.riskProfile': "ملف المخاطر",
    'detail.pages': "صفحات",
    'detail.lang.en': "الإنجليزية",
    'detail.lang.ar': "العربية",

    'riskType.missing_clause': "بند مفقود",
    'riskType.unusual_clause': "بند غير معتاد",
    'riskType.non_standard': "غير قياسي",
    'riskType.inconsistency': "عدم اتساق",
    'riskType.compliance': "امتثال",

    'role.client': "العميل",
    'role.vendor': "المورد",
    'role.partner': "شريك",
    'role.other': "أخرى",

    'partyType.organization': "جهة اعتبارية",
    'partyType.individual': "فرد",

    'dateType.effective_date': "تاريخ السريان",
    'dateType.expiration_date': "تاريخ الانتهاء",
    'dateType.renewal_date': "تاريخ التجديد",
    'dateType.milestone': "مرحلة",
    'dateType.other': "تاريخ آخر",

    'termType.payment': "دفعة",
    'termType.penalty': "غرامة",
    'termType.deposit': "تأمين",
    'termType.other': "أخرى",

    'chat.title': "كلارا",
    'chat.subtitle.contract': "إجابات من هذا العقد مع مصادرها",
    'chat.subtitle.portfolio': "إجابات من جميع عقودك مع مصادرها",
    'chat.welcome.contract': "اسألني أي شيء عن هذا العقد. أجيب من نصه فقط وأعرض لك المقطع الذي تستند إليه كل إجابة.",
    'chat.welcome.portfolio': "اسألني أي شيء عن عقودك. أبحث فيها جميعا وأعرض لك المقطع الذي تستند إليه كل إجابة.",
    'chat.suggest.contract.1': "من يحق له إنهاء العقد للملاءمة، وما مدة الإشعار؟",
    'chat.suggest.contract.2': "هل يوجد حد أقصى للمسؤولية؟",
    'chat.suggest.contract.3': "ما هي شروط الدفع؟",
    'chat.suggest.portfolio.1': "أي العقود تسمح بالإنهاء للملاءمة؟",
    'chat.suggest.portfolio.2': "ما القوانين الحاكمة في عقودي؟",
    'chat.placeholder': "اكتب سؤالك...",
    'chat.send': "إرسال",
    'chat.thinking': "جاري قراءة العقد...",
    'chat.hint': "Enter للإرسال · Shift+Enter لسطر جديد",
    'chat.error': "تعذر على كلارا الإجابة الآن. يرجى المحاولة مرة أخرى.",
    'chat.sessionExpired': "انتهت صلاحية الجلسة. يرجى تسجيل الدخول مرة أخرى.",
    'chat.notFound': "تعذر العثور على هذا العقد.",
    'chat.sources': "المصادر",
    'chat.page': "ص",
    'chat.source': "مصدر",
    'chat.openContract': "فتح العقد",
    'chat.clear': "مسح المحادثة",
    'chat.retry': "إعادة المحاولة",
    'chat.close': "إغلاق",
    
    // Risk Levels
    'risk.critical': 'حرج',
    'risk.high': 'عالي',
    'risk.medium': 'متوسط',
    'risk.low': 'منخفض',
    
    // Languages
    'lang.english': 'English',
    'lang.arabic': 'العربية',
    'lang.bilingual': 'دعم اللغتين العربية والإنجليزية',
  },
};

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>('en');

  // Load saved language from localStorage
  useEffect(() => {
    const savedLang = localStorage.getItem('language') as Language;
    if (savedLang && (savedLang === 'en' || savedLang === 'ar')) {
      setLanguageState(savedLang);
    }
  }, []);

  // Update document direction and save to localStorage
  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem('language', lang);
    
    // Update document direction
    if (typeof document !== 'undefined') {
      document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
      document.documentElement.lang = lang;
    }
  };

  // Translation function
  const t = (key: string): string => {
    return translations[language][key] || key;
  };

  // Set initial direction
  useEffect(() => {
    if (typeof document !== 'undefined') {
      document.documentElement.dir = language === 'ar' ? 'rtl' : 'ltr';
      document.documentElement.lang = language;
    }
  }, [language]);

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}
