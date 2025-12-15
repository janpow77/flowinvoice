// Datei: frontend/src/pages/Login.tsx
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import axios from 'axios';

// --- CSS Animationen ---
const cssAnimations = `
  @keyframes fishJump {
    0% {
      transform: translateY(150px) translateX(-80px) rotate(-30deg);
      opacity: 0;
    }
    15% {
      opacity: 1;
    }
    50% {
      transform: translateY(-250px) translateX(0px) rotate(10deg);
    }
    85% {
      opacity: 1;
    }
    100% {
      transform: translateY(150px) translateX(80px) rotate(45deg);
      opacity: 0;
    }
  }

  .animate-fish-jump {
    animation: fishJump 7s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    filter: drop-shadow(0 0 20px rgba(96, 165, 250, 0.6));
  }

  @keyframes waveMove {
    0% { transform: translateX(0); }
    50% { transform: translateX(-25px); }
    100% { transform: translateX(0); }
  }

  .wave-animation {
    animation: waveMove 6s ease-in-out infinite;
  }

  .wave-animation-reverse {
    animation: waveMove 8s ease-in-out infinite reverse;
  }
`;

// SVG Fisch-Icon
const FishIcon = () => (
  <svg
    viewBox="0 0 64 64"
    className="w-full h-full"
    fill="currentColor"
  >
    {/* Fischkörper */}
    <ellipse cx="28" cy="32" rx="20" ry="12" className="text-blue-300" />
    {/* Schwanzflosse */}
    <polygon points="48,32 60,20 60,44" className="text-blue-400" />
    {/* Rückenflosse */}
    <polygon points="24,20 32,8 36,20" className="text-blue-400" />
    {/* Bauchflosse */}
    <polygon points="26,44 30,52 34,44" className="text-blue-400" />
    {/* Auge */}
    <circle cx="18" cy="30" r="3" className="text-white" />
    <circle cx="17" cy="29" r="1.5" className="text-blue-900" />
    {/* Kiemen */}
    <path d="M22 28 Q20 32 22 36" stroke="currentColor" strokeWidth="1.5" fill="none" className="text-blue-500" />
    {/* Schuppen-Muster */}
    <path d="M28 26 Q32 28 28 30" stroke="currentColor" strokeWidth="1" fill="none" className="text-blue-200/50" />
    <path d="M34 28 Q38 30 34 32" stroke="currentColor" strokeWidth="1" fill="none" className="text-blue-200/50" />
    <path d="M28 34 Q32 36 28 38" stroke="currentColor" strokeWidth="1" fill="none" className="text-blue-200/50" />
  </svg>
);

export default function Login() {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Redirect wenn bereits eingeloggt
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);

      const response = await axios.post('/api/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });

      login(response.data.access_token);
      navigate('/');
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 401) {
        setError('Ungültige Anmeldedaten.');
      } else {
        setError('Ein Fehler ist aufgetreten. Bitte versuchen Sie es erneut.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-900 via-blue-700 to-blue-500 relative overflow-hidden flex flex-col justify-center items-center py-12 sm:px-6 lg:px-8">
      <style>{cssAnimations}</style>

      {/* --- DATENTEICH / WELLEN (HINTERGRUND) --- */}

      {/* Hintere Welle (tiefer, dunkler) */}
      <div className="absolute bottom-0 left-0 right-0 z-0 pointer-events-none wave-animation-reverse">
        <svg
          className="w-full h-40"
          viewBox="0 0 1440 320"
          preserveAspectRatio="none"
        >
          <path
            fill="rgba(30, 64, 175, 0.6)"
            d="M0,256L48,240C96,224,192,192,288,181.3C384,171,480,181,576,197.3C672,213,768,235,864,229.3C960,224,1056,192,1152,181.3C1248,171,1344,181,1392,186.7L1440,192L1440,320L1392,320C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z"
          />
        </svg>
      </div>

      {/* Vordere Welle (heller) */}
      <div className="absolute bottom-0 left-0 right-0 z-10 pointer-events-none wave-animation">
        <svg
          className="w-full h-32"
          viewBox="0 0 1440 320"
          preserveAspectRatio="none"
        >
          <path
            fill="rgba(59, 130, 246, 0.8)"
            d="M0,224L48,213.3C96,203,192,181,288,181.3C384,181,480,203,576,224C672,245,768,267,864,261.3C960,256,1056,224,1152,202.7C1248,181,1344,171,1392,165.3L1440,160L1440,320L1392,320C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z"
          />
        </svg>
      </div>

      {/* Der springende Fisch */}
      <div className="absolute bottom-20 left-1/2 -ml-10 z-20 w-20 h-20 animate-fish-jump pointer-events-none">
        <FishIcon />
      </div>

      {/* --- LOGIN BEREICH (VORDERGRUND) --- */}
      <div className="relative z-30 sm:mx-auto sm:w-full sm:max-w-md px-4">

        {/* Logo und Überschrift */}
        <div className="text-center mb-8">
          <img
            src="/auditlogo.svg"
            alt="FlowAudit Logo"
            className="h-24 w-auto mx-auto mb-4 drop-shadow-lg"
            onError={(e) => {
              const target = e.target as HTMLImageElement;
              if (!target.src.endsWith('.png')) {
                target.src = '/auditlogo.png';
              }
            }}
          />
          <h1 className="text-5xl sm:text-6xl font-extrabold text-white drop-shadow-lg tracking-tight">
            flowaudit
          </h1>
          <p className="mt-2 text-blue-200 text-sm uppercase tracking-widest font-medium">
            Automated Audit Systems
          </p>
        </div>

        {/* Login Karte (Milchglas / Frosted Glass) */}
        <div className="bg-white/10 backdrop-blur-lg border border-white/20 py-8 px-6 shadow-2xl rounded-2xl sm:px-10">
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="username" className="block text-sm font-semibold text-blue-100 mb-2">
                Kennung
              </label>
              <Input
                id="username"
                name="username"
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-white/10 border-white/30 text-white placeholder-blue-200/60 focus:border-blue-300 focus:ring-2 focus:ring-blue-300/50 h-12 rounded-lg"
                placeholder="Benutzername"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-semibold text-blue-100 mb-2">
                Passwort
              </label>
              <Input
                id="password"
                name="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-white/10 border-white/30 text-white placeholder-blue-200/60 focus:border-blue-300 focus:ring-2 focus:ring-blue-300/50 h-12 rounded-lg"
                placeholder="••••••••"
              />
            </div>

            {error && (
              <div className="text-sm text-center text-red-100 bg-red-500/30 py-3 px-4 rounded-lg border border-red-400/30">
                {error}
              </div>
            )}

            <div>
              <Button
                type="submit"
                fullWidth
                loading={loading}
                className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 h-12 shadow-lg shadow-blue-900/50 border-none text-base rounded-lg transition-all duration-200 hover:shadow-xl hover:shadow-blue-800/50"
              >
                Login
              </Button>
            </div>
          </form>

          {/* Hinweis für Demo-Zugänge */}
          <div className="mt-6 pt-4 border-t border-white/10">
            <p className="text-xs text-blue-200/60 text-center">
              Demo: admin / admin oder user / user
            </p>
          </div>
        </div>
      </div>

      {/* Kleine Deko-Elemente (Blasen) */}
      <div className="absolute bottom-40 left-1/4 w-3 h-3 bg-blue-300/30 rounded-full animate-bounce" style={{ animationDelay: '0s', animationDuration: '3s' }} />
      <div className="absolute bottom-52 left-1/3 w-2 h-2 bg-blue-200/20 rounded-full animate-bounce" style={{ animationDelay: '1s', animationDuration: '4s' }} />
      <div className="absolute bottom-36 right-1/4 w-4 h-4 bg-blue-300/25 rounded-full animate-bounce" style={{ animationDelay: '0.5s', animationDuration: '3.5s' }} />
      <div className="absolute bottom-60 right-1/3 w-2 h-2 bg-blue-200/30 rounded-full animate-bounce" style={{ animationDelay: '1.5s', animationDuration: '4.5s' }} />
    </div>
  );
}
