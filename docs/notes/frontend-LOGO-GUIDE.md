# Logo & Branding Assets

## Current Logo

The application currently uses a **placeholder logo** consisting of:
- A gradient background (Primary → Secondary color)
- A document/contract icon
- Rounded corners for a modern look

## Logo Locations

The logo appears in the following components:
- `src/components/Logo.tsx` - Main logo component (reusable)
- `src/components/Header.tsx` - Used in header on all authenticated pages
- `src/app/login/page.tsx` - Login page
- `src/app/page.tsx` - Home/loading page
- `src/app/upload/page.tsx` - Upload page

## Favicon

Location: `public/favicon.svg`

The favicon is an SVG version of the logo with:
- 32x32 size
- Gradient background matching brand colors
- Document icon

## How to Replace with Real Logo

### Step 1: Prepare Your Logo Files

You'll need:
1. **Logo image** - PNG or SVG format (recommended: SVG for scalability)
   - Suggested sizes: 
     - Small (40x40px) for header
     - Medium (64x64px) for upload page
     - Large (96x96px) for login/home pages
     - Extra Large (128x128px) for special uses

2. **Favicon** - Multiple formats for best compatibility:
   - `favicon.svg` (modern browsers)
   - `favicon.ico` (16x16, 32x32, 48x48 multi-size)
   - `apple-touch-icon.png` (180x180px for iOS)

### Step 2: Add Logo Files

Place your logo files in:
```
frontend/public/
  ├── logo.svg (or logo.png)
  ├── logo-small.svg
  ├── favicon.svg
  ├── favicon.ico
  └── apple-touch-icon.png
```

### Step 3: Update Logo Component

Edit `src/components/Logo.tsx`:

**Option A: Using Image File**
```tsx
import Image from 'next/image';

export default function Logo({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' | 'xl' }) {
  const sizes = {
    sm: 40,
    md: 48,
    lg: 64,
    xl: 96,
  };

  return (
    <div className="transition-smooth hover:scale-110">
      <Image 
        src="/logo.svg" 
        alt="AI Contract CLM" 
        width={sizes[size]} 
        height={sizes[size]}
        priority
      />
    </div>
  );
}
```

**Option B: Using Custom SVG**
```tsx
export default function Logo({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' | 'xl' }) {
  const sizes = {
    sm: 'w-10 h-10',
    md: 'w-12 h-12',
    lg: 'w-16 h-16',
    xl: 'w-24 h-24',
  };

  return (
    <svg className={sizes[size]} viewBox="0 0 100 100">
      {/* Your custom SVG path here */}
    </svg>
  );
}
```

### Step 4: Update Favicon References

Edit `src/app/layout.tsx`:
```tsx
export const metadata: Metadata = {
  // ... other metadata
  icons: {
    icon: [
      { url: '/favicon.ico' },
      { url: '/favicon.svg', type: 'image/svg+xml' },
    ],
    apple: '/apple-touch-icon.png',
  },
};
```

### Step 5: Test Across Pages

Check the logo appears correctly on:
- [ ] Login page (`/login`)
- [ ] Home page (`/`)
- [ ] Dashboard (`/dashboard`)
- [ ] Upload page (`/upload`)
- [ ] All other authenticated pages

### Step 6: Test Favicon

Check favicon appears in:
- [ ] Browser tab
- [ ] Bookmarks
- [ ] Mobile home screen (iOS/Android)
- [ ] Different browsers (Chrome, Firefox, Safari, Edge)

## Logo Design Guidelines

When creating your real logo, consider:

### Colors
- Primary: #441768 (Deep Purple)
- Secondary: #1A2155 (Dark Navy)
- Or use your finalized brand colors

### Style
- Modern and professional
- Clear at small sizes (favicon)
- Works in both light and dark contexts
- Represents legal/contract technology

### Formats
- **SVG**: Best for web (scalable, small file size)
- **PNG**: Fallback for older browsers
- **ICO**: Traditional favicon format

### Sizes Needed
- 16x16 (browser tab)
- 32x32 (browser tab HD)
- 48x48 (Windows taskbar)
- 64x64 (Windows shortcuts)
- 180x180 (Apple touch icon)
- 192x192 (Android)
- 512x512 (PWA splash screen)

## Quick Replace Checklist

- [ ] Create logo files in required sizes
- [ ] Add files to `public/` folder
- [ ] Update `Logo.tsx` component
- [ ] Update `layout.tsx` metadata
- [ ] Test on all pages
- [ ] Test favicon in browsers
- [ ] Test on mobile devices
- [ ] Update this README with your logo details

## Current Placeholder Specs

The current placeholder uses:
- **Colors**: Gradient from #441768 to #1A2155
- **Icon**: Document/contract symbol
- **Sizes**: Responsive (sm: 32px, md: 40px, lg: 64px, xl: 96px)
- **Effects**: Shadow glow, hover scale
- **Border Radius**: Rounded (0.75rem for md size)

Replace these specifications with your actual logo details once implemented.
