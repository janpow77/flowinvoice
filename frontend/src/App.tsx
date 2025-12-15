import { Suspense, lazy } from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import { LoadingScreen } from './components/ui/LogoSpinner'
import { AuthProvider, ProtectedRoute } from './context/AuthContext'

// Lazy-loaded Pages für bessere Performance
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Projects = lazy(() => import('./pages/Projects'))
const ProjectDetail = lazy(() => import('./pages/ProjectDetail'))
const Documents = lazy(() => import('./pages/Documents'))
const DocumentDetail = lazy(() => import('./pages/DocumentDetail'))
const Statistics = lazy(() => import('./pages/Statistics'))
const Settings = lazy(() => import('./pages/Settings'))
const Login = lazy(() => import('./pages/Login'))

function App() {
  return (
    <AuthProvider>
      <Suspense fallback={<LoadingScreen message="Seite wird geladen..." />}>
        <Routes>
          {/* Öffentliche Route: Login */}
          <Route path="/login" element={<Login />} />

          {/* Geschützte Routen: Erfordern Authentifizierung */}
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <Layout>
                  <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/projects" element={<Projects />} />
                    <Route path="/projects/:id" element={<ProjectDetail />} />
                    <Route path="/documents" element={<Documents />} />
                    <Route path="/documents/:id" element={<DocumentDetail />} />
                    <Route path="/statistics" element={<Statistics />} />
                    <Route path="/settings" element={<Settings />} />
                  </Routes>
                </Layout>
              </ProtectedRoute>
            }
          />
        </Routes>
      </Suspense>
    </AuthProvider>
  )
}

export default App
