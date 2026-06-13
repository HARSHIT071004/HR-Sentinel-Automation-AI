import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { BackgroundPaths } from '../components/ui/background-paths';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const login = useAuthStore((state) => state.login);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen relative bg-[#0a0a0f]">
      <BackgroundPaths />

      <div className="absolute inset-0 flex items-center justify-center z-10">
        <div className="w-full max-w-md px-4">
          <div className="text-center mb-8">
            <div className="w-14 h-14 bg-[#6366f1] rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-[#6366f1]/25">
              <span className="text-white font-bold text-xl">HR</span>
            </div>
            <h1 className="text-2xl font-bold text-white">HR Sentinel AI</h1>
            <p className="text-[#a1a1aa] mt-1">Workforce Intelligence Platform</p>
          </div>

          <div className="bg-[#0f0f17]/90 backdrop-blur-xl border border-[#1e1e2e] rounded-2xl p-8 shadow-2xl">
            {error && (
              <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-white mb-1.5">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-2.5 bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg text-white placeholder-[#a1a1aa] focus:outline-none focus:ring-2 focus:ring-[#6366f1]"
                  placeholder="hr@aegis.com"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white mb-1.5">Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-2.5 bg-[#0a0a0f] border border-[#1e1e2e] rounded-lg text-white placeholder-[#a1a1aa] focus:outline-none focus:ring-2 focus:ring-[#6366f1]"
                  placeholder="Password"
                  required
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 bg-[#6366f1] text-white rounded-lg font-medium hover:bg-[#5558e6] disabled:opacity-50 transition-all"
              >
                {loading ? 'Signing in...' : 'Sign In'}
              </button>
            </form>

            <div className="mt-6 pt-4 border-t border-[#1e1e2e]">
              <p className="text-xs text-[#a1a1aa] text-center">Demo: hr@aegis.com / hr123</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
