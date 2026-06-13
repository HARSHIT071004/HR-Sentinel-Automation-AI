import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { useThemeStore } from '../stores/themeStore';
import {
  LayoutDashboard,
  Users,
  Upload,
  Brain,
  Sun,
  Moon,
  LogOut,
  ChevronRight,
  House,
  MessageSquareText,
  Plus,
} from 'lucide-react';
import { cn } from '../lib/utils';

const navItems = [
  { path: '/', label: 'Home', icon: House },
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/employees', label: 'Employees', icon: Users },
  { path: '/attendance', label: 'Upload', icon: Upload },
  { path: '/ai', label: 'AI Insights', icon: Brain },
  { path: '/copilot', label: 'Copilot', icon: MessageSquareText },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const logout = useAuthStore((state) => state.logout);
  const user = useAuthStore((state) => state.user);
  const { theme, toggle } = useThemeStore();
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <div className="min-h-screen bg-background flex">
      <aside className="w-64 bg-sidebar border-r border-sidebar-border flex flex-col shrink-0">
        {/* Brand */}
        <div className="px-5 py-3 border-b border-sidebar-border">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-primary rounded-xl flex items-center justify-center shadow-lg shadow-primary/25">
              <span className="text-primary-foreground font-bold text-sm">HR</span>
            </div>
            <div>
              <h1 className="text-sm font-bold text-foreground tracking-tight">
                HR Sentinel
              </h1>
              <p className="text-[10px] text-muted-foreground uppercase tracking-widest">
                AI Platform
              </p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map((item) => {
            const active = location.pathname === item.path;
            const Icon = item.icon;
            return (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className={cn(
                  'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all group',
                  active
                    ? 'bg-sidebar-active text-sidebar-active-fg'
                    : 'text-sidebar-foreground hover:bg-sidebar-hover hover:text-foreground'
                )}
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span className="flex-1 text-left">{item.label}</span>
                {active && (
                  <ChevronRight className="w-3.5 h-3.5 text-sidebar-active-fg" />
                )}
              </button>
            );
          })}
        </nav>

        {/* Bottom: user info */}
        <div className="px-4 py-2.5">
          <p className="text-xs font-medium text-foreground truncate leading-tight">
            {user?.full_name}
          </p>
          <p className="text-[9px] text-muted-foreground uppercase tracking-wider leading-tight">
            {user?.role?.replace('_', ' ')}
          </p>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-h-screen overflow-hidden">
        <div className="flex items-center justify-between px-6 py-3 border-b border-border shrink-0">
          {location.pathname === '/copilot' && (
            <h1 className="text-sm font-semibold text-foreground">HR Copilot</h1>
          )}
          <div className="flex items-center gap-2 ml-auto">
            {location.pathname === '/copilot' && (
              <button
                onClick={() => navigate('/copilot?new=1')}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary text-primary-foreground text-xs font-medium hover:bg-primary/90 transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                New Chat
              </button>
            )}
            <button
              onClick={toggle}
              className="w-9 h-9 flex items-center justify-center rounded-lg text-muted-foreground hover:bg-accent hover:text-foreground transition-all"
              title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            >
              {theme === 'dark' ? (
                <Sun className="w-4 h-4" />
              ) : (
                <Moon className="w-4 h-4" />
              )}
            </button>
            <button
              onClick={() => { logout(); navigate('/login'); }}
              className="w-9 h-9 flex items-center justify-center rounded-lg text-muted-foreground hover:bg-accent hover:text-destructive transition-all"
              title="Sign out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
        <main className="flex-1 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
