# UI Design System & Customization Guide

## Color Palette

The application uses a professional color scheme that can be easily customized. All colors are defined in CSS variables and Tailwind configuration.

### Current Colors

**Primary Colors:**
- `#441768` - Deep Purple (Main brand color)
- `#1A2155` - Dark Navy (Secondary accent)

**Neutral Colors:**
- `#000000` - Black
- `#FFFFFF` - White
- `#F2F2F2` - Light Gray

### How to Change Colors

#### Method 1: CSS Variables (Recommended for Quick Changes)

Edit `frontend/src/app/globals.css`:

```css
:root {
  --color-primary: #441768;      /* Change this to your primary color */
  --color-secondary: #1A2155;    /* Change this to your secondary color */
  --color-dark: #000000;
  --color-light: #FFFFFF;
  --color-light-gray: #F2F2F2;
}
```

#### Method 2: Tailwind Configuration (For Complete Control)

Edit `frontend/tailwind.config.js`:

```javascript
colors: {
  primary: {
    900: '#441768',  // Main brand color
    // Add more shades if needed
  },
  secondary: {
    900: '#1A2155',  // Secondary color
    // Add more shades if needed
  },
}
```

## Typography

- **Primary Font**: Inter (Latin scripts)
- **Arabic Font**: Cairo (Arabic scripts)

To change fonts, edit `frontend/src/app/layout.tsx`.

## Animations

The UI includes smooth animations for better user experience:

### Available Animations

1. **fade-in** - Simple fade in effect
2. **fade-in-up** - Fade in with upward movement
3. **fade-in-down** - Fade in with downward movement
4. **slide-in-left** - Slide from left
5. **slide-in-right** - Slide from right
6. **scale-in** - Scale up from smaller size
7. **pulse-slow** - Slow pulsing effect
8. **shimmer** - Loading shimmer effect
9. **hover-lift** - Lift effect on hover

### Usage Examples

```tsx
// Fade in animation
<div className="animate-fade-in">Content</div>

// Fade in with delay
<div className="animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
  Content
</div>

// Hover lift effect
<div className="hover-lift">Hoverable card</div>
```

### Custom Animation Timing

You can adjust animation durations in `tailwind.config.js` under the `keyframes` section.

## Component Styles

### Pre-built Classes

The design system includes pre-built component classes:

#### Buttons
- `btn` - Base button style
- `btn-primary` - Primary action button
- `btn-secondary` - Secondary action button
- `btn-outline` - Outlined button
- `btn-ghost` - Ghost button (text only)

#### Cards
- `card` - Basic card with shadow
- `card-hover` - Card with hover effects
- `card-gradient` - Card with gradient background

#### Inputs
- `input` - Standard input field
- `input-error` - Error state input

#### Badges
- `badge` - Base badge
- `badge-success` - Green success badge
- `badge-warning` - Yellow warning badge
- `badge-error` - Red error badge
- `badge-info` - Blue info badge
- `badge-primary` - Primary color badge

## Shadows & Effects

### Custom Shadows
- `shadow-soft` - Soft shadow
- `shadow-soft-lg` - Large soft shadow
- `shadow-glow` - Glowing shadow (primary color)
- `shadow-glow-lg` - Large glowing shadow

### Glass Effect
- `glass-effect` - Frosted glass effect (light)
- `glass-effect-dark` - Frosted glass effect (dark)

## Responsive Design

All components are responsive and work across:
- Mobile (< 640px)
- Tablet (640px - 1024px)
- Desktop (> 1024px)

## RTL Support (Arabic)

The application supports Right-to-Left layouts for Arabic content. The layout automatically switches when the HTML lang attribute is set to "ar".

## Best Practices

1. **Use CSS variables** for colors that might change frequently
2. **Use Tailwind classes** for spacing, sizing, and layout
3. **Apply animations sparingly** to avoid overwhelming users
4. **Test on multiple devices** to ensure responsive behavior
5. **Maintain accessibility** - ensure sufficient color contrast

## Accessibility

- All interactive elements have focus states
- Color combinations meet WCAG AA standards
- Animations respect prefers-reduced-motion
- Semantic HTML is used throughout

## Quick Customization Checklist

- [ ] Update primary color in CSS variables
- [ ] Update secondary color in CSS variables
- [ ] Update Tailwind color palette
- [ ] Test color contrast for accessibility
- [ ] Review animations on different devices
- [ ] Test RTL layout if using Arabic
- [ ] Verify responsive behavior

## Examples

### Creating a Custom Colored Button

```tsx
// Using pre-built classes
<button className="btn btn-primary">Click Me</button>

// Custom color with Tailwind
<button className="btn bg-purple-600 hover:bg-purple-700 text-white">
  Custom Button
</button>
```

### Creating an Animated Card

```tsx
<div className="card hover-lift animate-fade-in-up" 
     style={{ animationDelay: '0.3s' }}>
  <div className="p-6">
    <h3 className="text-xl font-bold mb-2">Card Title</h3>
    <p className="text-gray-600">Card content goes here</p>
  </div>
</div>
```

### Adding a Gradient Background

```tsx
<div className="bg-gradient-primary p-8 rounded-xl text-white">
  Gradient content
</div>
```

## Support

For questions or issues with the UI design system, please refer to:
- Tailwind CSS Documentation: https://tailwindcss.com/docs
- Next.js Documentation: https://nextjs.org/docs
