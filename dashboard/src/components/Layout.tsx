import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

const navItems = [
  { path: '/', label: 'Dashboard' },
  { path: '/employees', label: 'Employees' },
  { path: '/attendance', label: 'Upload' },
  { path: '/ai', label: 'AI Insights' },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const logout = useAuthStore((state) => state.logout);
  const user = useAuthStore((state) => state.user);
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex">
      <aside className="w-64 bg-[#0f0f17] border-r border-[#1e1e2e] flex flex-col">
        <div className="px-5 py-5 border-b border-[#1e1e2e]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-[#6366f1] rounded-xl flex items-center shadow-lg">
              <span className="text-white font-bold text-sm">HR</span>
            </div>
            <div>
              <h1 className="text-sm font-bold text-white tracking-tight">HR Sentinel</h1>
              <p className="text-[10px] text-[#a1a1aa] uppercase tracking-widest">AI Platform</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map((item) => {
            const active = location.pathname === item.path;
            return (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  active
                    ? 'bg-[#1a1a2e] text-[#a78bfa]'
                    : 'text-[#a1a1aa] hover:text-white hover:bg-[#1a1a2e]'
                }`}
              >
                {item.label}
              </button>
            );
          })}
        </nav>

        <div className="px-3 py-4 border-t border-[#1e1e2e]">
          <div className="flex items-center gap-3 px-2 mb-3">
            <div className="w-8 h-8 bg-[#22c55e] rounded-full flex items-center justify-center text-xs font-bold text-white">
              {user?.full_name?.[0] || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{user?.full_name}</p>
              <p className="text-[10px] text-[#a1a1aa] uppercase">{user?.role}</p>
            </div>
          </div>
          <button
            onClick={() => { logout(); navigate('/login'); }}
            className="w-full px-3 py-2 text-xs text-[#a1a1aa] hover:text-[#ef4444] hover:bg-[#1a1a2e] rounded-lg transition-colors"
          >
            Sign out
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-h-screen overflow-hidden">
        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
