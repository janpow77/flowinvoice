/**
 * Landing Page / Frontpage
 *
 * Complete landing page with:
 * - Hero section with animation
 * - Features grid
 * - Call-to-action sections
 * - Dark mode support
 */

import { useNavigate } from 'react-router-dom'
import { useTheme, ThemeToggle } from '../context/ThemeContext'
import {
  Sparkles,
  Shield,
  Zap,
  Globe,
  ArrowRight,
  Check,
  Moon,
  Sun,
  BarChart3,
  Lock,
  Smartphone,
  Cloud
} from 'lucide-react'

interface Feature {
  icon: React.ReactNode
  title: string
  description: string
}

const features: Feature[] = [
  {
    icon: <Shield className="w-8 h-8" />,
    title: 'Sicher',
    description: 'Enterprise-grade Sicherheit mit OAuth 2.0 und JWT Authentication.'
  },
  {
    icon: <Zap className="w-8 h-8" />,
    title: 'Schnell',
    description: 'Optimierte Performance mit React 18 und modernen Web-Technologien.'
  },
  {
    icon: <Globe className="w-8 h-8" />,
    title: 'Global',
    description: 'Mehrsprachig und optimiert für internationale Nutzer.'
  },
  {
    icon: <BarChart3 className="w-8 h-8" />,
    title: 'Analytics',
    description: 'Integrierte Dashboards und Echtzeit-Statistiken.'
  },
  {
    icon: <Smartphone className="w-8 h-8" />,
    title: 'Responsive',
    description: 'Perfekte Darstellung auf allen Geräten und Bildschirmgrößen.'
  },
  {
    icon: <Cloud className="w-8 h-8" />,
    title: 'Cloud Ready',
    description: 'Docker-Container und Cloudflare Tunnel Support.'
  }
]

const pricingPlans = [
  {
    name: 'Starter',
    price: '0',
    description: 'Perfekt zum Ausprobieren',
    features: ['Bis zu 100 Dokumente', 'Basis-Analyse', 'Community Support'],
    cta: 'Kostenlos starten',
    highlighted: false
  },
  {
    name: 'Professional',
    price: '49',
    description: 'Für wachsende Teams',
    features: ['Unbegrenzte Dokumente', 'KI-Analyse', 'Priority Support', 'API Zugang', 'Team-Features'],
    cta: 'Jetzt upgraden',
    highlighted: true
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    description: 'Für große Organisationen',
    features: ['Alles in Professional', 'On-Premise Option', 'Custom Integration', 'SLA Garantie', '24/7 Support'],
    cta: 'Kontakt aufnehmen',
    highlighted: false
  }
]

export default function LandingPage() {
  const navigate = useNavigate()
  const { theme } = useTheme()

  return (
    <div className="min-h-screen bg-theme-app">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-theme-panel/80 backdrop-blur-md border-b border-theme-border-subtle">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <img
                src="/auditlogo.svg"
                alt="Logo"
                className="h-8 w-8"
              />
              <span className="text-xl font-bold text-theme-text-primary">
                YourBrand
              </span>
            </div>

            {/* Nav Links */}
            <div className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-theme-text-secondary hover:text-theme-text-primary transition-colors">
                Features
              </a>
              <a href="#pricing" className="text-theme-text-secondary hover:text-theme-text-primary transition-colors">
                Preise
              </a>
              <a href="#about" className="text-theme-text-secondary hover:text-theme-text-primary transition-colors">
                Über uns
              </a>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-4">
              <ThemeToggle />
              <button
                onClick={() => navigate('/login')}
                className="btn btn-primary"
              >
                Anmelden
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 overflow-hidden">
        {/* Background Gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-accent-primary/10 via-transparent to-purple-500/10" />

        {/* Animated Background Elements */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-20 left-10 w-72 h-72 bg-accent-primary/20 rounded-full blur-3xl animate-pulse" />
          <div className="absolute bottom-20 right-10 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-accent-primary/10 text-accent-primary mb-8">
              <Sparkles className="w-4 h-4" />
              <span className="text-sm font-medium">Neu: KI-gestützte Analyse</span>
            </div>

            {/* Title */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-theme-text-primary mb-6">
              Willkommen bei
              <span className="block text-transparent bg-clip-text bg-gradient-to-r from-accent-primary to-purple-500">
                YourBrand
              </span>
            </h1>

            {/* Subtitle */}
            <p className="max-w-2xl mx-auto text-xl text-theme-text-secondary mb-10">
              Die moderne Plattform für Ihr Unternehmen. Sicher, schnell und intelligent.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={() => navigate('/login')}
                className="btn btn-primary btn-lg group"
              >
                Kostenlos starten
                <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
              </button>
              <button
                onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })}
                className="btn btn-outline btn-lg"
              >
                Mehr erfahren
              </button>
            </div>

            {/* Trust Badges */}
            <div className="mt-12 flex flex-wrap justify-center gap-8 text-theme-text-muted">
              <div className="flex items-center gap-2">
                <Lock className="w-5 h-5" />
                <span>DSGVO konform</span>
              </div>
              <div className="flex items-center gap-2">
                <Shield className="w-5 h-5" />
                <span>SSL verschlüsselt</span>
              </div>
              <div className="flex items-center gap-2">
                <Cloud className="w-5 h-5" />
                <span>EU Hosting</span>
              </div>
            </div>
          </div>

          {/* Hero Image/Dashboard Preview */}
          <div className="mt-16 relative">
            <div className="absolute inset-0 bg-gradient-to-t from-theme-app via-transparent to-transparent z-10" />
            <div className="rounded-xl overflow-hidden shadow-2xl border border-theme-border-subtle bg-theme-card">
              <div className="p-4 border-b border-theme-border-subtle flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-red-500" />
                <div className="w-3 h-3 rounded-full bg-yellow-500" />
                <div className="w-3 h-3 rounded-full bg-green-500" />
              </div>
              <div className="p-8 bg-theme-elevated">
                <div className="grid grid-cols-3 gap-4">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-24 rounded-lg bg-theme-card animate-pulse" />
                  ))}
                </div>
                <div className="mt-4 h-48 rounded-lg bg-theme-card animate-pulse" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 bg-theme-elevated">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-theme-text-primary mb-4">
              Alles was Sie brauchen
            </h2>
            <p className="text-lg text-theme-text-secondary max-w-2xl mx-auto">
              Moderne Funktionen für moderne Anforderungen.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div
                key={index}
                className="card card-hover p-6 group"
              >
                <div className="w-12 h-12 rounded-lg bg-accent-primary/10 text-accent-primary flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  {feature.icon}
                </div>
                <h3 className="text-xl font-semibold text-theme-text-primary mb-2">
                  {feature.title}
                </h3>
                <p className="text-theme-text-secondary">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-20 bg-gradient-to-r from-accent-primary to-purple-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8 text-center text-white">
            {[
              { value: '10K+', label: 'Aktive Nutzer' },
              { value: '99.9%', label: 'Uptime' },
              { value: '50M+', label: 'Dokumente' },
              { value: '4.9/5', label: 'Bewertung' }
            ].map((stat, index) => (
              <div key={index}>
                <div className="text-4xl sm:text-5xl font-bold mb-2">{stat.value}</div>
                <div className="text-white/80">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 bg-theme-app">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-theme-text-primary mb-4">
              Transparente Preise
            </h2>
            <p className="text-lg text-theme-text-secondary max-w-2xl mx-auto">
              Wählen Sie den Plan, der zu Ihnen passt.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {pricingPlans.map((plan, index) => (
              <div
                key={index}
                className={`card p-8 relative ${
                  plan.highlighted
                    ? 'border-2 border-accent-primary shadow-lg shadow-accent-primary/20'
                    : ''
                }`}
              >
                {plan.highlighted && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-accent-primary text-white text-sm font-medium">
                    Beliebt
                  </div>
                )}
                <div className="text-center mb-6">
                  <h3 className="text-xl font-bold text-theme-text-primary mb-2">
                    {plan.name}
                  </h3>
                  <p className="text-theme-text-muted text-sm mb-4">
                    {plan.description}
                  </p>
                  <div className="flex items-baseline justify-center gap-1">
                    {plan.price !== 'Custom' && <span className="text-2xl text-theme-text-secondary">€</span>}
                    <span className="text-5xl font-bold text-theme-text-primary">{plan.price}</span>
                    {plan.price !== 'Custom' && <span className="text-theme-text-secondary">/Monat</span>}
                  </div>
                </div>
                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature, i) => (
                    <li key={i} className="flex items-center gap-3 text-theme-text-secondary">
                      <Check className="w-5 h-5 text-status-success flex-shrink-0" />
                      {feature}
                    </li>
                  ))}
                </ul>
                <button
                  onClick={() => navigate('/login')}
                  className={`w-full btn ${plan.highlighted ? 'btn-primary' : 'btn-outline'}`}
                >
                  {plan.cta}
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-theme-elevated">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl sm:text-4xl font-bold text-theme-text-primary mb-6">
            Bereit loszulegen?
          </h2>
          <p className="text-xl text-theme-text-secondary mb-10">
            Starten Sie noch heute kostenlos und entdecken Sie alle Möglichkeiten.
          </p>
          <button
            onClick={() => navigate('/login')}
            className="btn btn-primary btn-lg group"
          >
            Jetzt kostenlos starten
            <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer id="about" className="py-12 bg-theme-panel border-t border-theme-border-subtle">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            {/* Brand */}
            <div className="md:col-span-1">
              <div className="flex items-center gap-3 mb-4">
                <img src="/auditlogo.svg" alt="Logo" className="h-8 w-8" />
                <span className="text-xl font-bold text-theme-text-primary">YourBrand</span>
              </div>
              <p className="text-theme-text-muted text-sm">
                Die moderne Plattform für Ihr Unternehmen.
              </p>
            </div>

            {/* Links */}
            <div>
              <h4 className="font-semibold text-theme-text-primary mb-4">Produkt</h4>
              <ul className="space-y-2 text-theme-text-secondary text-sm">
                <li><a href="#features" className="hover:text-theme-text-primary">Features</a></li>
                <li><a href="#pricing" className="hover:text-theme-text-primary">Preise</a></li>
                <li><a href="#" className="hover:text-theme-text-primary">Changelog</a></li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold text-theme-text-primary mb-4">Ressourcen</h4>
              <ul className="space-y-2 text-theme-text-secondary text-sm">
                <li><a href="#" className="hover:text-theme-text-primary">Dokumentation</a></li>
                <li><a href="#" className="hover:text-theme-text-primary">API</a></li>
                <li><a href="#" className="hover:text-theme-text-primary">Blog</a></li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold text-theme-text-primary mb-4">Rechtliches</h4>
              <ul className="space-y-2 text-theme-text-secondary text-sm">
                <li><a href="#" className="hover:text-theme-text-primary">Datenschutz</a></li>
                <li><a href="#" className="hover:text-theme-text-primary">Impressum</a></li>
                <li><a href="#" className="hover:text-theme-text-primary">AGB</a></li>
              </ul>
            </div>
          </div>

          <div className="mt-12 pt-8 border-t border-theme-border-subtle flex flex-col sm:flex-row justify-between items-center gap-4">
            <p className="text-theme-text-muted text-sm">
              © {new Date().getFullYear()} YourBrand. Alle Rechte vorbehalten.
            </p>
            <div className="flex items-center gap-2">
              <ThemeToggle />
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
