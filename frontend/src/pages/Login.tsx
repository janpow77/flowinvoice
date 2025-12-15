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
      transform: translateY(180px) translateX(-50px) rotate(-45deg);
      opacity: 0;
    }
    10% {
      opacity: 1;
    }
    45% {
      transform: translateY(-260px) translateX(0px) rotate(0deg);
    }
    55% {
      transform: translateY(-260px) translateX(10px) rotate(10deg);
    }
    90% {
      opacity: 1;
    }
    100% {
      transform: translateY(180px) translateX(80px) rotate(60deg);
      opacity: 0;
    }
  }

  .animate-fish-jump {
    animation: fishJump 8s cubic-bezier(0.45, 0.05, 0.55, 0.95) infinite;
    /* Kleiner Schatten unter dem Logo für 3D-Effekt */
    filter: drop-shadow(0 10px 15px rgba(0,0,0,0.3));
  }

  @keyframes floatData {
    0% { transform: translateY(0px); opacity: 0.3; }
    50% { transform: translateY(-10px); opacity: 0.6; }
    100% { transform: translateY(0px); opacity: 0.3; }
  }

  .data-stream {
    font-family: 'Courier New', monospace;
    font-size: 10px;
    line-height: 10px;
    color: rgba(147, 197, 253, 0.3); /* Helles Daten-Blau, transparent */
    user-select: none;
    overflow: hidden;
  }
`;

export default function Login() {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  // State für den "Datenteich"-Inhalt (zufällige 0en und 1en)
  const [binaryData, setBinaryData] = useState('');

  // Redirect wenn bereits eingeloggt
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  // Generiere den "Datenteich"-Hintergrund beim Laden
  useEffect(() => {
    let data = '';
    for (let i = 0; i < 4000; i++) {
      data += Math.random() > 0.5 ? '1 ' : '0 ';
    }
    setBinaryData(data);
  }, []);

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
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-blue-900 to-blue-600 relative overflow-hidden flex flex-col justify-center items-center py-12 sm:px-6 lg:px-8 font-sans">
      <style>{cssAnimations}</style>

      {/* --- DATENTEICH (HINTERGRUND) --- */}
      <div className="absolute inset-x-0 bottom-0 h-1/3 z-0 pointer-events-none">

        {/* Das springende Logo (Fisch) */}
        <div className="absolute bottom-0 left-1/2 ml-[-40px] mb-[-20px] animate-fish-jump z-20 w-24 h-24">
           {/* Hier wird das Logo als Bild geladen */}
           <img
             src="/auditlogo.svg"
             alt="Jumping Logo"
             className="w-full h-full object-contain"
             onError={(e) => {
               const target = e.target as HTMLImageElement;
               target.src = '/auditlogo.png'; // Fallback
             }}
           />
        </div>

        {/* Die Oberfläche des Teichs (SVG Welle) */}
        <div className="absolute top-[-50px] left-0 right-0 z-10 text-blue-500">
           <svg className="w-full h-24" viewBox="0 0 1440 320" preserveAspectRatio="none">
               <path fill="currentColor" fillOpacity="1" d="M0,224L48,213.3C96,203,192,181,288,181.3C384,181,480,203,576,224C672,245,768,267,864,261.3C960,256,1056,224,1152,202.7C1248,181,1344,171,1392,165.3L1440,160L1440,320L1392,320C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z"></path>
           </svg>
        </div>

        {/* Das Innere des Teichs: Binärcode statt Wasser */}
        <div className="absolute inset-0 bg-blue-800/80 overflow-hidden flex flex-wrap content-start p-4 data-stream" style={{animation: 'floatData 3s ease-in-out infinite'}}>
            {/* Der Binärcode füllt den unteren Bereich */}
            <div className="w-full break-all text-justify opacity-40">
                {binaryData}
            </div>
        </div>
      </div>


      {/* --- LOGIN BEREICH (VORDERGRUND) --- */}
      <div className="relative z-30 sm:mx-auto sm:w-full sm:max-w-md">

        {/* Titel oberhalb */}
        <div className="text-center mb-10">
            <h1 className="text-6xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-100 to-white drop-shadow-lg tracking-tight">
            flowaudit
            </h1>
            <p className="mt-2 text-blue-200 text-sm uppercase tracking-widest font-semibold">
            Automated Audit Systems
            </p>
        </div>

        {/* Login Karte (Milchglas) */}
        <div className="bg-white/10 backdrop-blur-md border border-white/20 py-8 px-6 shadow-2xl rounded-2xl sm:px-10">
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="username" className="block text-xs font-bold text-blue-100 uppercase mb-1">
                Kennung
              </label>
              <Input
                id="username"
                name="username"
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="bg-blue-900/40 border-blue-400/30 text-white placeholder-blue-300/50 focus:border-blue-300 focus:ring-1 focus:ring-blue-300 h-11"
                placeholder="Benutzername"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-xs font-bold text-blue-100 uppercase mb-1">
                Passwort
              </label>
              <Input
                id="password"
                name="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="bg-blue-900/40 border-blue-400/30 text-white placeholder-blue-300/50 focus:border-blue-300 focus:ring-1 focus:ring-blue-300 h-11"
                placeholder="••••••••"
              />
            </div>

            {error && (
              <div className="text-sm text-center text-red-200 bg-red-900/40 py-2 px-3 rounded border border-red-500/30">
                {error}
              </div>
            )}

            <div>
              <Button
                type="submit"
                fullWidth
                loading={loading}
                className="bg-blue-500 hover:bg-blue-400 text-white font-bold py-3 shadow-lg shadow-blue-900/50 border-none text-base transition-all transform hover:scale-[1.02]"
              >
                Einloggen
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
