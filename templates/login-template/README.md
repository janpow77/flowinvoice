# Login Template

A beautiful, animated login page template with Google OAuth support. Features a jumping fish animation over binary data water, glassmorphism design, and full Cloudflare Tunnel compatibility.

## How to Use This Template

### Option 1: Direct Clone & Copy

```bash
# Clone the repo
git clone https://github.com/janpow77/flowinvoice.git

# Copy login template to your project
cp -r flowinvoice/templates/login-template/* your-project/

# Clean up
rm -rf flowinvoice
```

### Option 2: Git Subtree (Recommended - allows updates)

```bash
# Add template to your repo
git subtree add --prefix=templates/login \
  https://github.com/janpow77/flowinvoice.git main --squash

# Later: Pull updates
git subtree pull --prefix=templates/login \
  https://github.com/janpow77/flowinvoice.git main --squash
```

### Option 3: Setup Script

```bash
# Download and run setup script
curl -sL https://raw.githubusercontent.com/janpow77/flowinvoice/main/templates/setup.sh -o setup.sh
chmod +x setup.sh
./setup.sh login ./my-project
```

### Option 4: Direct Download (ZIP)

1. Go to: https://github.com/janpow77/flowinvoice
2. Code → Download ZIP
3. Extract `templates/login-template/` to your project

---

## Features

- Animated fish jumping over binary data "water"
- Glassmorphism (frosted glass) login card
- Google OAuth integration
- JWT-based authentication
- Inactivity timeout (10 minutes)
- Role-based access control
- Cloudflare Tunnel ready
- Dark/Light theme support
- Responsive design

## Preview

The login page features:
- Gradient blue background
- Animated binary data flowing like water at the bottom
- Your logo jumping out of the "water"
- Frosted glass login form
- Animated bubbles

## Quick Start

### Frontend Setup

1. Copy files to your React project:
   ```bash
   cp -r frontend/components/* your-project/src/components/
   cp -r frontend/pages/* your-project/src/pages/
   cp -r frontend/context/* your-project/src/context/
   cp frontend/styles/login-animations.css your-project/src/styles/
   cp frontend/public/* your-project/public/  # Logo
   ```

2. Add routes in your App.tsx:
   ```tsx
   import Login from './pages/Login'
   import GoogleCallback from './pages/GoogleCallback'

   <Route path="/login" element={<Login />} />
   <Route path="/auth/google/callback" element={<GoogleCallback />} />
   ```

3. Wrap your app with AuthProvider:
   ```tsx
   import { AuthProvider, ProtectedRoute } from './context/AuthContext'

   <AuthProvider>
     <Routes>
       <Route path="/login" element={<Login />} />
       <Route path="/*" element={
         <ProtectedRoute>
           {/* Your protected routes */}
         </ProtectedRoute>
       } />
     </Routes>
   </AuthProvider>
   ```

4. Install dependencies:
   ```bash
   npm install axios react-router-dom
   ```

### Backend Setup (FastAPI)

1. Copy backend files:
   ```bash
   cp backend/auth.py your-project/app/api/
   cp backend/config_additions.py your-project/  # Merge with your config
   ```

2. Add to your config.py:
   ```python
   # Google OAuth
   google_client_id: str | None = None
   google_client_secret: SecretStr | None = None
   google_redirect_uri: str = "http://localhost:3000/auth/google/callback"

   # JWT
   jwt_algorithm: str = "HS256"
   jwt_expire_hours: int = 24
   ```

3. Add User model fields for OAuth:
   ```python
   auth_provider: Mapped[str | None] = mapped_column(String(20), nullable=True)
   google_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
   ```

4. Install dependencies:
   ```bash
   pip install python-jose httpx
   ```

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "Google+ API" or "People API"
4. Go to "Credentials" -> "Create Credentials" -> "OAuth Client ID"
5. Choose "Web application"
6. Add authorized redirect URIs:
   - Development: `http://localhost:3000/auth/google/callback`
   - Production: `https://your-domain.com/auth/google/callback`
7. Copy Client ID and Client Secret

### Environment Variables

```bash
# Backend
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=https://your-domain.com/auth/google/callback
SECRET_KEY=your-secret-key-for-jwt
```

### Cloudflare Tunnel Configuration

1. Set up Cloudflare Tunnel to your backend
2. Update `GOOGLE_REDIRECT_URI` to use your Cloudflare domain
3. Add the domain to Google OAuth authorized redirect URIs
4. Enable "Access" policies if needed for additional security

## Customization

### Logo

The template includes a sample logo (`public/auditlogo.png`). Replace with your own:
```tsx
// In Login.tsx, update these lines:
<img src="/your-logo.png" alt="Logo" className="h-24 w-auto mx-auto" />
```
Or copy the included logo to your public folder and use `/auditlogo.png`.

### Colors

The template uses Tailwind CSS with blue gradients. Modify these classes:
- Background: `from-blue-900 via-blue-700 to-blue-500`
- Button: `bg-blue-600 hover:bg-blue-500`
- Accents: `text-blue-200`, `border-white/20`

### Brand Name

Update the title in Login.tsx:
```tsx
<h1 className="text-5xl font-extrabold text-white">
  Your Brand
</h1>
<p className="text-blue-200 text-sm">
  Your Tagline
</p>
```

### Demo Users

Disable or customize demo user hints:
```tsx
{/* Remove or modify this section */}
<div className="mt-6 pt-4 border-t border-white/10">
  <p className="text-xs text-blue-200/60 text-center">
    Demo: admin / admin
  </p>
</div>
```

## Security Notes

- The template uses CSRF protection via state tokens
- JWT tokens expire after 24 hours (configurable)
- Inactivity timeout logs out users after 10 minutes
- Passwords are hashed with bcrypt
- Google OAuth tokens are never stored on the client

## File Structure

```
login-template/
├── frontend/
│   ├── public/
│   │   ├── auditlogo.png      # Logo (PNG for raster)
│   │   └── auditlogo.svg      # Logo (SVG for vector)
│   ├── components/
│   │   └── ui/
│   │       ├── Button.tsx
│   │       └── Input.tsx
│   ├── pages/
│   │   ├── Login.tsx          # Main login page
│   │   └── GoogleCallback.tsx  # OAuth callback handler
│   ├── context/
│   │   └── AuthContext.tsx    # Auth state management
│   └── styles/
│       └── login-animations.css # CSS animations
├── backend/
│   ├── auth.py                # FastAPI auth endpoints
│   └── config_additions.py    # Config snippets
└── README.md
```

## License

MIT - Feel free to use in your projects.
