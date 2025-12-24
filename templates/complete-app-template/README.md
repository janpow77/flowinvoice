# Complete App Template

A complete, production-ready React application template with:
- Beautiful animated login page with Google OAuth
- Complete design system with semantic colors
- Dark/Light mode with system preference
- Sidebar navigation with role-based access
- Reusable UI components
- FastAPI backend auth endpoints

## Features

### Pages
- **Landing Page** - Hero, Features, Pricing, Stats, CTA sections
- **Login Page** - Animated with Google OAuth button
- **Google Callback** - OAuth redirect handler

### Authentication
- Google OAuth integration
- JWT-based authentication
- Inactivity timeout (10 minutes)
- Role-based access control (RBAC)
- CSRF protection
- Cloudflare Tunnel ready

### UI Components
- **Button** - Primary, secondary, outline, ghost, success, warning, danger
- **Input** - Text, textarea, select, checkbox, radio with validation
- **Card** - Container with header, body, footer + StatCard
- **Badge** - Status badges and indicators
- **Alert** - Info, success, warning, error notifications
- **LogoSpinner** - Animated loading with progress

### Design System
- Semantic color tokens (auto-adapt to dark/light)
- Tailwind CSS configuration
- CSS component classes
- Responsive design

### Layout
- App shell with collapsible sidebar
- Header with user menu
- Role-based navigation filtering
- Mobile responsive

### Animations
- Login page with jumping fish animation
- Binary data "water" flow effect
- Glassmorphism (frosted glass) design
- Animated bubbles

---

## Quick Start

### 1. Copy to your project

```bash
# Clone and copy
git clone https://github.com/janpow77/flowinvoice.git temp
cp -r temp/templates/complete-app-template/* your-project/
rm -rf temp
```

### 2. Install dependencies

```bash
cd your-project/frontend
npm install react react-dom react-router-dom axios
npm install tailwindcss postcss autoprefixer clsx lucide-react
npx tailwindcss init -p
```

### 3. Setup Tailwind

Copy `tailwind.config.js` from template and update your `index.css`:

```css
@import './styles/design-system.css';
@import './styles/login-animations.css';
```

### 4. Wrap your app

```tsx
// App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from './context/ThemeContext'
import { AuthProvider, ProtectedRoute } from './context/AuthContext'
import Layout from './components/Layout'
import LandingPage from './pages/LandingPage'
import Login from './pages/Login'
import GoogleCallback from './pages/GoogleCallback'

function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <Routes>
            {/* Public routes */}
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<Login />} />
            <Route path="/auth/google/callback" element={<GoogleCallback />} />

            {/* Protected routes */}
            <Route path="/app/*" element={
              <ProtectedRoute>
                <Layout>
                  {/* Your app routes here */}
                </Layout>
              </ProtectedRoute>
            } />
          </Routes>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  )
}

export default App
```

### 5. Backend Setup (FastAPI)

```bash
cd your-project/backend
pip install python-jose httpx bcrypt
```

Add to your FastAPI app:
```python
from backend.auth import auth_router
app.include_router(auth_router, prefix="/api")
```

### 6. Environment Variables

```bash
# Backend
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=https://your-domain.com/auth/google/callback
SECRET_KEY=your-jwt-secret-key
```

---

## File Structure

```
complete-app-template/
├── frontend/
│   ├── public/
│   │   ├── auditlogo.png           # Logo (PNG)
│   │   └── auditlogo.svg           # Logo (SVG)
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
│   │   │   ├── ThemeContext.tsx    # Dark/Light mode
│   │   │   └── AuthContext.tsx     # Authentication + OAuth
│   │   ├── pages/
│   │   │   ├── LandingPage.tsx     # Landing/Frontpage with Hero, Features, CTA
│   │   │   ├── Login.tsx           # Login page with animation
│   │   │   └── GoogleCallback.tsx  # OAuth callback
│   │   └── styles/
│   │       ├── design-system.css   # Complete design system
│   │       └── login-animations.css# Login animations
│   └── tailwind.config.js
├── backend/
│   ├── auth.py                     # FastAPI auth endpoints
│   └── config_additions.py         # Config snippets
└── README.md
```

---

## Customization

### Logo
Replace files in `public/`:
- `auditlogo.png` - Raster logo
- `auditlogo.svg` - Vector logo

Update references:
```tsx
<img src="/your-logo.png" alt="Logo" />
```

### Brand Colors
Edit CSS variables in `design-system.css`:
```css
:root {
  --color-primary-500: #3b82f6;  /* Your brand blue */
  --color-primary-600: #2563eb;
  --color-accent-primary: #2563eb;
}
```

### Navigation Items
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
<span className="text-xl font-bold">YourBrand</span>
```

And in `Login.tsx`:
```tsx
<h1 className="text-5xl font-extrabold text-white">YourBrand</h1>
```

---

## Design System Classes

### Semantic Colors

```css
/* Backgrounds */
bg-theme-app        /* Main app background */
bg-theme-panel      /* Sidebar, header */
bg-theme-card       /* Cards */
bg-theme-elevated   /* Elevated surfaces */
bg-theme-hover      /* Hover states */

/* Text */
text-theme-text-primary    /* Main text */
text-theme-text-secondary  /* Secondary */
text-theme-text-muted      /* Muted */

/* Borders */
border-theme-border-default
border-theme-border-subtle

/* Accents */
text-accent-primary
bg-accent-primary

/* Status */
text-status-success / bg-status-success-bg
text-status-warning / bg-status-warning-bg
text-status-danger / bg-status-danger-bg
text-status-info / bg-status-info-bg
```

### Component Classes

```css
/* Buttons */
.btn .btn-primary .btn-secondary .btn-outline .btn-ghost
.btn-success .btn-warning .btn-danger .btn-sm .btn-lg

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
.modal .modal-backdrop .modal-content

/* Loading */
.skeleton .skeleton-text .skeleton-circle
```

---

## Component Examples

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
  <CardHeader title="Users" subtitle="Manage users" />
  <CardBody>{/* Content */}</CardBody>
</Card>

<StatCard
  label="Total Users"
  value={1234}
  icon={<Users />}
  change="+12%"
  changePositive
/>
```

### Theme Toggle
```tsx
import { ThemeToggle } from './context/ThemeContext'

<ThemeToggle />           {/* Simple toggle */}
<ThemeToggle showSystem /> {/* With system option */}
```

### Protected Route
```tsx
import { ProtectedRoute, AdminRoute } from './context/AuthContext'

{/* Any authenticated user */}
<ProtectedRoute>
  <Dashboard />
</ProtectedRoute>

{/* Admin only */}
<AdminRoute>
  <AdminPanel />
</AdminRoute>

{/* Specific roles */}
<ProtectedRoute allowedRoles={['admin', 'manager']}>
  <Reports />
</ProtectedRoute>
```

---

## Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create project → Enable "People API"
3. Credentials → Create OAuth Client ID → Web application
4. Add redirect URIs:
   - Dev: `http://localhost:3000/auth/google/callback`
   - Prod: `https://your-domain.com/auth/google/callback`
5. Copy Client ID and Secret to environment

---

## Security Notes

- CSRF protection via state tokens
- JWT tokens expire after 24 hours
- Inactivity auto-logout after 10 minutes
- Passwords hashed with bcrypt
- OAuth tokens never stored client-side

---

## License

MIT - Feel free to use in your projects.
