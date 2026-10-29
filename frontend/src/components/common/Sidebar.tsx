import React from 'react';
import {
  LayoutDashboard, Users, Calendar, Stethoscope,
  FlaskConical, BarChart3, ShieldAlert, History, Activity,
  ChevronLeft, ChevronRight, HeartPulse
} from 'lucide-react';

export type NavItemKey =
  | 'dashboard'
  | 'patients'
  | 'appointments'
  | 'encounters'
  | 'orders'
  | 'reports'
  | 'data-quality'
  | 'audit'
  | 'health';

interface SidebarProps {
  currentTab: NavItemKey;
  onSelectTab: (tab: NavItemKey) => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
  waitingCount?: number;
  openDqCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  collapsed,
  onToggleCollapse,
  waitingCount = 0,
  openDqCount = 0
}) => {
  const navItems = [
    { key: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { key: 'patients', label: 'Patient Registry', icon: Users },
    { key: 'appointments', label: 'Appointments', icon: Calendar, badge: waitingCount > 0 ? waitingCount : undefined, badgeColor: 'bg-amber-100 text-amber-800' },
    { key: 'encounters', label: 'Encounters', icon: Stethoscope },
    { key: 'orders', label: 'Orders & Results', icon: FlaskConical },
    { key: 'reports', label: 'Reporting Workspace', icon: BarChart3 },
    { key: 'data-quality', label: 'Data Quality & Remediation', icon: ShieldAlert, badge: openDqCount > 0 ? openDqCount : undefined, badgeColor: 'bg-rose-100 text-rose-800' },
    { key: 'audit', label: 'Audit Explorer', icon: History },
    { key: 'health', label: 'System Health', icon: Activity },
  ];

  return (
    <aside
      className={`fixed top-0 left-0 z-30 h-screen transition-all duration-300 bg-brand-900 text-slate-100 flex flex-col border-r border-slate-800 ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-slate-800/80">
        <div className="flex items-center space-x-3 overflow-hidden">
          <div className="p-2 rounded-lg bg-teal-500/20 text-teal-400 flex-shrink-0">
            <HeartPulse className="w-6 h-6" />
          </div>
          {!collapsed && (
            <div className="flex flex-col">
              <span className="font-bold text-lg text-white tracking-tight">CareFlow</span>
              <span className="text-[10px] text-teal-300 font-mono tracking-widest uppercase">Clinical Ops</span>
            </div>
          )}
        </div>
        <button
          onClick={onToggleCollapse}
          className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.key;
          return (
            <button
              key={item.key}
              onClick={() => onSelectTab(item.key as NavItemKey)}
              className={`w-full flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? 'bg-teal-600/90 text-white shadow-sm'
                  : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`}
              title={collapsed ? item.label : undefined}
            >
              <Icon className={`w-5 h-5 flex-shrink-0 ${isActive ? 'text-white' : 'text-slate-400'}`} />
              {!collapsed && (
                <span className="ml-3 flex-1 text-left truncate">{item.label}</span>
              )}
              {!collapsed && item.badge !== undefined && (
                <span className={`ml-2 text-xs font-semibold px-2 py-0.5 rounded-full ${item.badgeColor || 'bg-slate-700 text-slate-200'}`}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer Info */}
      {!collapsed && (
        <div className="p-4 border-t border-slate-800/80 bg-brand-900/60 text-xs text-slate-400">
          <div className="flex items-center justify-between font-mono">
            <span>Engine:</span>
            <span className="text-teal-400 font-semibold">Oracle Free / Live</span>
          </div>
          <div className="mt-1 text-[11px] text-slate-500">CareFlow v1.0 • Portfolio Ed.</div>
        </div>
      )}
    </aside>
  );
};
