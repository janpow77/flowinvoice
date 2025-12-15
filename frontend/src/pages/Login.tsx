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
      transform: translateY(150px) translateX(-80px) rotate(-15deg) scaleX(-1);
      opacity: 0;
    }
    15% {
      opacity: 1;
    }
    50% {
      transform: translateY(-200px) translateX(0px) rotate(5deg) scaleX(-1);
    }
    85% {
      opacity: 1;
    }
    100% {
      transform: translateY(150px) translateX(80px) rotate(25deg) scaleX(-1);
      opacity: 0;
    }
  }

  .animate-fish-jump {
    animation: fishJump 7s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    filter: drop-shadow(0 0 25px rgba(96, 165, 250, 0.7));
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

  @keyframes dataFlow {
    0% { transform: translateX(0); }
    100% { transform: translateX(-50%); }
  }

  .data-flow {
    animation: dataFlow 20s linear infinite;
  }

  .data-flow-fast {
    animation: dataFlow 15s linear infinite;
  }

  .data-flow-slow {
    animation: dataFlow 25s linear infinite reverse;
  }

  @keyframes binaryPulse {
    0%, 100% { opacity: 0.3; }
    50% { opacity: 0.8; }
  }

  .binary-pulse {
    animation: binaryPulse 3s ease-in-out infinite;
  }
`;

// Springender Fisch - verwendet das echte Logo
const JumpingFish = () => (
  <img
    src="/auditlogo.svg"
    alt="Jumping Fish"
    className="w-full h-full object-contain"
    onError={(e) => {
      const target = e.target as HTMLImageElement;
      if (!target.src.endsWith('.png')) {
        target.src = '/auditlogo.png';
      }
    }}
  />
);

// Statische Binärsequenzen für das Datenwasser (verhindert Flackern)
const BINARY_LINES = [
  '0 1 1 0 0 1 0 1 1 0 1 0 0 1 1 0 1 1 0 0 1 0 1 0 1 1 0 0 1 0 1 1 0 1 0 0 1 1 0 1 0 1 0 0 1 1 0 1 0 1 1 0 0 1 0 1 1 0 1 0 0 1 1 0 1 1 0 0 1 0 1 0 1 1 0 0 1 0 1 1',
  '1 0 0 1 1 0 1 0 0 1 0 1 1 0 0 1 0 0 1 1 0 1 0 1 0 0 1 1 0 1 0 0 1 0 1 1 0 0 1 0 1 0 1 1 0 0 1 0 1 0 0 1 1 0 1 0 0 1 0 1 1 0 0 1 0 0 1 1 0 1 0 1 0 0 1 1 0 1 0 0',
  '0 0 1 0 1 1 0 1 0 0 1 0 1 1 0 1 0 1 0 0 1 1 0 1 0 1 0 0 1 1 0 0 1 0 1 1 0 1 0 0 1 0 1 1 0 1 0 1 0 0 1 1 0 1 0 1 0 0 1 1 0 0 1 0 1 1 0 1 0 0 1 0 1 1 0 1 0 1 0 0',
  '1 1 0 1 0 0 1 0 1 1 0 1 0 0 1 0 1 0 1 1 0 0 1 0 1 0 1 1 0 0 1 1 0 1 0 0 1 0 1 1 0 1 0 0 1 0 1 0 1 1 0 0 1 0 1 0 1 1 0 0 1 1 0 1 0 0 1 0 1 1 0 1 0 0 1 0 1 0 1 1',
  '0 1 0 1 1 0 0 1 0 1 0 1 1 0 0 1 1 0 1 0 0 1 0 1 1 0 1 0 0 1 0 1 0 1 1 0 0 1 0 1 0 1 1 0 0 1 1 0 1 0 0 1 0 1 1 0 1 0 0 1 0 1 0 1 1 0 0 1 0 1 0 1 1 0 0 1 1 0 1 0',
];

// Binäres Datenwasser - fließende 0 und 1
const BinaryDataWater = () => {
  const binaryLines = BINARY_LINES;

  return (
    <div className="absolute bottom-0 left-0 right-0 h-48 overflow-hidden pointer-events-none">
      {/* Wellenförmiger Clip-Path über dem Binärcode */}
      <svg className="absolute bottom-0 left-0 right-0 h-full w-full" preserveAspectRatio="none">
        <defs>
          <clipPath id="waveClip">
            <path d="M0,60 Q180,20 360,50 T720,40 T1080,55 T1440,45 L1440,200 L0,200 Z" />
          </clipPath>
        </defs>
      </svg>

      {/* Hintere Datenschicht (dunkler, langsamer) */}
      <div className="absolute bottom-0 left-0 right-0 h-40 bg-gradient-to-t from-blue-950/90 via-blue-900/70 to-transparent">
        <div className="data-flow-slow whitespace-nowrap font-mono text-xs leading-relaxed pt-8">
          <span className="text-blue-400/40">{binaryLines[0]} {binaryLines[0]}</span>
        </div>
        <div className="data-flow whitespace-nowrap font-mono text-xs leading-relaxed">
          <span className="text-cyan-400/30">{binaryLines[1]} {binaryLines[1]}</span>
        </div>
      </div>

      {/* Mittlere Datenschicht */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-blue-800/80 via-blue-700/50 to-transparent">
        <div className="data-flow-fast whitespace-nowrap font-mono text-sm leading-relaxed pt-4">
          <span className="text-blue-300/50">{binaryLines[2]} {binaryLines[2]}</span>
        </div>
        <div className="data-flow whitespace-nowrap font-mono text-sm leading-relaxed">
          <span className="text-cyan-300/40">{binaryLines[3]} {binaryLines[3]}</span>
        </div>
      </div>

      {/* Vordere Datenschicht (heller, schneller) */}
      <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-blue-600/90 via-blue-500/60 to-transparent">
        <div className="data-flow-fast whitespace-nowrap font-mono text-base leading-relaxed pt-2 binary-pulse">
          <span className="text-blue-200/70">{binaryLines[4]} {binaryLines[4]}</span>
        </div>
      </div>

      {/* Wellenförmige Oberfläche */}
      <div className="absolute bottom-16 left-0 right-0 wave-animation">
        <svg className="w-full h-12" viewBox="0 0 1440 48" preserveAspectRatio="none">
          <path
            fill="rgba(96, 165, 250, 0.3)"
            d="M0,24 Q180,8 360,20 T720,16 T1080,22 T1440,18 L1440,48 L0,48 Z"
          />
        </svg>
      </div>
      <div className="absolute bottom-12 left-0 right-0 wave-animation-reverse">
        <svg className="w-full h-10" viewBox="0 0 1440 40" preserveAspectRatio="none">
          <path
            fill="rgba(59, 130, 246, 0.4)"
            d="M0,20 Q180,4 360,16 T720,12 T1080,18 T1440,14 L1440,40 L0,40 Z"
          />
        </svg>
      </div>
    </div>
  );
};

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

      {/* --- BINÄRES DATENWASSER (0 und 1 fließen wie Wasser) --- */}
      <BinaryDataWater />

      {/* Der springende Fisch - das bunte Logo springt aus dem Datenwasser */}
      <div className="absolute bottom-20 left-1/2 -ml-16 z-20 w-32 h-20 animate-fish-jump pointer-events-none">
        <JumpingFish />
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
