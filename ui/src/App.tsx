import { Routes, Route, NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  FolderOpen,
  PlusCircle,
  BookOpen,
  Settings as SettingsIcon,
  Shield,
  Flame,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { useState } from 'react';
import { cn } from './lib/utils';
import Dashboard from './pages/Dashboard';
import CaseView from './pages/CaseView';
import NewCase from './pages/NewCase';
import Evidence from './pages/Evidence';
import Playbooks from './pages/Playbooks';
import Settings from './pages/Settings';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/cases/new', icon: PlusCircle, label: 'New Case' },
  { to: '/evidence', icon: FolderOpen, label: 'Evidence' },
  { to: '/playbooks', icon: BookOpen, label: 'Playbooks' },
  { to: '/settings', icon: SettingsIcon, label: 'Settings' },
];

function Sidebar({ collapsed, onToggle }: { collapsed: boolean; onToggle: () => void }) {
  const location = useLocation();

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 h-screen bg-surface border-r border-surface-border flex flex-col z-50 transition-all duration-300',
        collapsed ? 'w-16' : 'w-60'
      )}
    >
      {/* Branding */}
      <div className="flex items-center gap-3 px-4 h-16 border-b border-surface-border shrink-0">
        <div className="relative flex items-center justify-center w-8 h-8">
          <Shield className="w-7 h-7 text-accent" />
          <Flame className="w-4 h-4 text-critical absolute -top-0.5 -right-0.5" />
        </div>
        {!collapsed && (
          <div className="flex flex-col">
            <span className="text-lg font-bold tracking-tight text-text-primary">
              DFIR<span className="text-critical">e</span>
              <span className="text-warning">ball</span>
              <span className="text-accent">z</span>
            </span>
            <span className="text-[10px] text-text-muted uppercase tracking-widest -mt-1">
              Digital Forensics
            </span>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 flex flex-col gap-1 p-2 mt-2">
        {navItems.map((item) => {
          const isActive =
            item.to === '/'
              ? location.pathname === '/'
              : location.pathname.startsWith(item.to);
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-all duration-150',
                isActive
                  ? 'bg-accent/15 text-accent border border-accent/20'
                  : 'text-text-secondary hover:text-text-primary hover:bg-surface-hover border border-transparent'
              )}
            >
              <item.icon className="w-5 h-5 shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </NavLink>
          );
        })}
      </nav>

      {/* Status */}
      {!collapsed && (
        <div className="p-3 mx-2 mb-2 bg-background rounded-lg border border-surface-border">
          <div className="flex items-center gap-2 text-xs">
            <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
            <span className="text-text-secondary">API Connected</span>
          </div>
          <p className="text-[10px] text-text-muted mt-1">localhost:8800</p>
        </div>
      )}

      {/* Collapse toggle */}
      <button
        onClick={onToggle}
        className="flex items-center justify-center h-10 border-t border-surface-border text-text-muted hover:text-text-primary transition-colors"
      >
        {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
      </button>
    </aside>
  );
}

export default function App() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="min-h-screen bg-background">
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />
      <main
        className={cn(
          'transition-all duration-300 min-h-screen',
          collapsed ? 'ml-16' : 'ml-60'
        )}
      >
        <div className="p-6 max-w-[1600px] mx-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/cases/new" element={<NewCase />} />
            <Route path="/cases/:caseId" element={<CaseView />} />
            <Route path="/evidence" element={<Evidence />} />
            <Route path="/playbooks" element={<Playbooks />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}
