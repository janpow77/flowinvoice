# UI Kit Template

A complete design system and component library for React applications with Tailwind CSS. Includes dark/light mode, semantic colors, and reusable components.

## Features

- Complete CSS design system with semantic tokens
- Dark/Light mode with system preference support
- Sidebar navigation with role-based filtering
- Reusable UI components (Button, Input, Card, Badge, Alert, etc.)
- Tailwind CSS configuration with custom theme
- Logo spinner with progress indicator
- Responsive layout

## Components Included

### Core Components
- **Button** - Primary, secondary, outline, ghost, success, warning, danger variants
- **Input** - Text, textarea, select, checkbox, radio with validation
- **Card** - Container with header, body, footer sections + StatCard
- **Badge** - Status badges and indicators
- **Alert** - Info, success, warning, error notifications
- **LogoSpinner** - Animated loading indicator with progress

### Layout
- **Layout** - Complete app shell with sidebar + header
- **Navigation** - Role-based sidebar navigation

### Theme
- **ThemeProvider** - Dark/light/system mode context
- **ThemeToggle** - Toggle button component

## Quick Start

### 1. Copy files to your project

```bash
# Core styles
cp frontend/src/styles/design-system.css your-project/src/index.css

# Tailwind config
cp frontend/tailwind.config.js your-project/

# Components
cp -r frontend/src/components/* your-project/src/components/
cp -r frontend/src/context/* your-project/src/context/

# Logo
cp frontend/public/* your-project/public/
```

### 2. Install dependencies

```bash
npm install tailwindcss clsx lucide-react react-router-dom
```

### 3. Wrap your app

```tsx
import { ThemeProvider } from './context/ThemeContext'
import { AuthProvider, ProtectedRoute } from './context/AuthContext'
import Layout from './components/Layout'

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/*" element={
            <ProtectedRoute>
              <Layout>
                {/* Your routes */}
              </Layout>
            </ProtectedRoute>
          } />
        </Routes>
      </AuthProvider>
    </ThemeProvider>
  )
}
```

## Design System

### Semantic Colors

The design system uses semantic color tokens that automatically adapt to light/dark mode:

```css
/* Backgrounds */
bg-theme-app      /* Main app background */
bg-theme-panel    /* Sidebar, header backgrounds */
bg-theme-card     /* Card backgrounds */
bg-theme-elevated /* Elevated surfaces */
bg-theme-hover    /* Hover states */

/* Text */
text-theme-text-primary    /* Main text */
text-theme-text-secondary  /* Secondary text */
text-theme-text-muted      /* Muted/subtle text */

/* Borders */
border-theme-border-default  /* Standard borders */
border-theme-border-subtle   /* Subtle borders */

/* Accents */
text-accent-primary    /* Primary accent color */
bg-accent-primary      /* Primary accent background */

/* Status */
text-status-success / bg-status-success-bg
text-status-warning / bg-status-warning-bg
text-status-danger / bg-status-danger-bg
text-status-info / bg-status-info-bg
```

### Component Classes

Pre-built component classes in CSS:

```css
/* Buttons */
.btn .btn-primary .btn-secondary .btn-outline .btn-ghost
.btn-success .btn-warning .btn-danger
.btn-sm .btn-lg

/* Forms */
.input .input-error .select .textarea
.checkbox .radio .label .helper-text .error-text

/* Cards */
.card .card-hover .card-header .card-body .card-footer

/* Badges */
.badge .badge-primary .badge-success .badge-warning .badge-error

/* Alerts */
.alert .alert-info .alert-success .alert-warning .alert-error

/* Navigation */
.nav-link .nav-link-active

/* Tables */
.table

/* Modals */
.modal .modal-backdrop .modal-content .modal-header .modal-body .modal-footer

/* Progress */
.progress .progress-bar

/* Skeleton loading */
.skeleton .skeleton-text .skeleton-circle
```

## Customization

### Colors

Edit the CSS variables in `design-system.css`:

```css
:root {
  /* Change primary color (blue) */
  --color-primary-500: #3b82f6;
  --color-primary-600: #2563eb;

  /* Change accent */
  --color-accent-primary: #2563eb;
}
```

### Logo

Replace files in `public/`:
- `auditlogo.png` - Raster logo
- `auditlogo.svg` - Vector logo

Update paths in components:
```tsx
<img src="/your-logo.png" alt="Logo" />
```

### Navigation

Edit `Layout.tsx`:

```tsx
const navigationItems: NavItem[] = [
  { key: 'dashboard', label: 'Dashboard', href: '/', icon: LayoutDashboard },
  { key: 'products', label: 'Products', href: '/products', icon: Package },
  // Add your routes...
]
```

### Brand Name

Update in `Layout.tsx`:
```tsx
<span className="text-xl font-bold">
  YourBrand
</span>
```

## File Structure

```
ui-kit-template/
├── frontend/
│   ├── public/
│   │   ├── auditlogo.png
│   │   └── auditlogo.svg
│   ├── src/
│   │   ├── components/
│   │   │   ├── Layout.tsx          # App shell with sidebar
│   │   │   └── ui/
│   │   │       ├── Button.tsx
│   │   │       ├── Input.tsx
│   │   │       ├── Card.tsx
│   │   │       ├── Badge.tsx
│   │   │       └── LogoSpinner.tsx
│   │   ├── context/
│   │   │   ├── ThemeContext.tsx    # Dark/light mode
│   │   │   └── AuthContext.tsx     # Authentication
│   │   └── styles/
│   │       └── design-system.css   # Complete CSS design system
│   └── tailwind.config.js
└── README.md
```

## Usage Examples

### Button

```tsx
import { Button } from './components/ui/Button'

<Button variant="primary">Save</Button>
<Button variant="outline" size="sm">Cancel</Button>
<Button variant="danger" loading={isDeleting}>Delete</Button>
```

### Card

```tsx
import { Card, CardHeader, CardBody, StatCard } from './components/ui/Card'

<Card>
  <CardHeader title="Users" subtitle="Manage your users" />
  <CardBody>
    {/* Content */}
  </CardBody>
</Card>

<StatCard
  label="Total Users"
  value={1234}
  icon={<Users />}
  change="+12%"
  changePositive
/>
```

### Badge & Alert

```tsx
import { Badge, Alert } from './components/ui/Badge'

<Badge variant="success">Active</Badge>
<Badge variant="warning" dot>Pending</Badge>

<Alert variant="info" title="Note">
  This is an informational message.
</Alert>
```

### Theme Toggle

```tsx
import { ThemeToggle } from './context/ThemeContext'

// Simple toggle
<ThemeToggle />

// With system option
<ThemeToggle showSystem />
```

## Dark Mode

The template uses Tailwind's `class` strategy for dark mode. The `ThemeProvider` automatically:

1. Reads preference from localStorage
2. Listens to system preference changes (when theme='system')
3. Adds/removes `dark` class on `<html>`

All semantic color classes automatically adjust in dark mode.

## License

MIT - Feel free to use in your projects.
