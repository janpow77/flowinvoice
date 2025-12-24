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

---

## How to Use These Templates

### Method 1: Direct Copy

```bash
# Clone and copy what you need
git clone https://github.com/janpow77/flowinvoice.git
cp -r flowinvoice/templates/login-template/* your-project/
cp -r flowinvoice/templates/ui-kit-template/* your-project/
```

### Method 2: Git Subtree (Recommended)

Add templates as a subtree in your project:

```bash
# Add templates folder to your repo
git subtree add --prefix=templates \
  https://github.com/janpow77/flowinvoice.git main --squash

# Update templates later
git subtree pull --prefix=templates \
  https://github.com/janpow77/flowinvoice.git main --squash
```

### Method 3: GitHub Template

1. Fork this repo
2. Go to Settings → Template repository → Enable
3. Use "Use this template" button for new projects

### Method 4: npx Script (Coming Soon)

```bash
# Future: Download templates via npx
npx @janpow77/create-app --template login
npx @janpow77/create-app --template ui-kit
```

---

## Template Contents

```
templates/
├── login-template/
│   ├── frontend/
│   │   ├── pages/           # Login, GoogleCallback
│   │   ├── context/         # AuthContext
│   │   ├── components/ui/   # Button, Input
│   │   ├── styles/          # Animations CSS
│   │   └── public/          # Logo files
│   ├── backend/             # FastAPI auth endpoints
│   └── README.md
│
├── ui-kit-template/
│   ├── frontend/
│   │   ├── components/      # Layout, UI components
│   │   ├── context/         # Theme, Auth contexts
│   │   ├── styles/          # Design system CSS
│   │   └── public/          # Logo files
│   ├── tailwind.config.js
│   └── README.md
│
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
