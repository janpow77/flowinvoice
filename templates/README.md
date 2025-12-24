# FlowAudit Templates

Reusable templates for building web applications.

## Available Templates

### 1. Login Template (`login-template/`)

Beautiful animated login page with:
- Jumping fish/logo animation over binary data "water"
- Glassmorphism design
- Google OAuth integration
- JWT authentication
- Cloudflare Tunnel ready

[View Documentation](./login-template/README.md)

### 2. UI Kit Template (`ui-kit-template/`)

Complete design system and component library:
- CSS design system with semantic tokens
- Dark/Light mode support
- Sidebar navigation with role-based filtering
- UI Components (Button, Input, Card, Badge, Alert, etc.)
- Tailwind CSS configuration

[View Documentation](./ui-kit-template/README.md)

### 3. Complete App Template (`complete-app-template/`) - RECOMMENDED

Everything combined in one ready-to-use template:
- Login page with animations + Google OAuth
- Complete design system + dark/light mode
- All UI components (Button, Input, Card, Badge, etc.)
- Sidebar layout with role-based navigation
- FastAPI backend auth endpoints
- Logo files (PNG + SVG)

[View Documentation](./complete-app-template/README.md)

---

## How to Use These Templates

### Method 1: Setup Script (Easiest)

```bash
# Download setup script
curl -sL https://raw.githubusercontent.com/janpow77/flowinvoice/main/templates/setup.sh -o setup.sh
chmod +x setup.sh

# Install login template only
./setup.sh login ./my-project

# Install UI kit template only
./setup.sh ui-kit ./my-project

# Install both templates (merged)
./setup.sh both ./my-project

# Install complete app template (recommended)
./setup.sh complete ./my-project
```

### Method 2: Direct Clone & Copy

```bash
# Clone and copy what you need
git clone https://github.com/janpow77/flowinvoice.git

# Copy templates
cp -r flowinvoice/templates/login-template/* your-project/
cp -r flowinvoice/templates/ui-kit-template/* your-project/

# Clean up
rm -rf flowinvoice
```

### Method 3: Git Subtree (Recommended for updates)

Add templates as a subtree in your project - allows pulling updates later:

```bash
# Add templates folder to your repo
git subtree add --prefix=templates \
  https://github.com/janpow77/flowinvoice.git main --squash

# Later: Update templates
git subtree pull --prefix=templates \
  https://github.com/janpow77/flowinvoice.git main --squash
```

### Method 4: Direct Download (ZIP)

1. Go to: https://github.com/janpow77/flowinvoice
2. Click: Code → Download ZIP
3. Extract `templates/` folder to your project

### Method 5: GitHub Template Repository

1. Fork this repo
2. Go to Settings → Template repository → Enable
3. Use "Use this template" button for new projects

---

## Template Contents

```
templates/
├── complete-app-template/   # RECOMMENDED - Everything combined
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── components/  # Layout + all UI components
│   │   │   ├── context/     # Auth + Theme contexts
│   │   │   ├── pages/       # Login, GoogleCallback
│   │   │   └── styles/      # Design system + animations
│   │   ├── public/          # Logo files
│   │   └── tailwind.config.js
│   ├── backend/             # FastAPI auth endpoints
│   └── README.md
│
├── login-template/          # Login only
│   ├── frontend/
│   │   ├── pages/           # Login, GoogleCallback
│   │   ├── context/         # AuthContext
│   │   ├── components/ui/   # Button, Input
│   │   ├── styles/          # Animations CSS
│   │   └── public/          # Logo files
│   ├── backend/             # FastAPI auth endpoints
│   └── README.md
│
├── ui-kit-template/         # UI Kit only
│   ├── frontend/
│   │   ├── components/      # Layout, UI components
│   │   ├── context/         # Theme, Auth contexts
│   │   ├── styles/          # Design system CSS
│   │   └── public/          # Logo files
│   ├── tailwind.config.js
│   └── README.md
│
├── setup.sh                 # Setup script
└── README.md                # This file
```

## Quick Start for New Project

```bash
# 1. Create new project
mkdir my-new-app && cd my-new-app
npm create vite@latest . -- --template react-ts

# 2. Get templates
git clone https://github.com/janpow77/flowinvoice.git temp
cp -r temp/templates/ui-kit-template/frontend/* ./
cp -r temp/templates/login-template/frontend/pages/* ./src/pages/
rm -rf temp

# 3. Install dependencies
npm install tailwindcss postcss autoprefixer clsx lucide-react react-router-dom axios

# 4. Init Tailwind
npx tailwindcss init -p

# 5. Replace tailwind.config.js and src/index.css with template versions

# 6. Start developing!
npm run dev
```

## License

MIT
