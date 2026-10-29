import React from 'react';
import { Search, ShieldAlert, User, Bell, RefreshCw } from 'lucide-react';

interface NavbarProps {
  onSearch?: (term: string) => void;
  onRefresh?: () => void;
  environmentName?: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  onSearch,
  onRefresh,
  environmentName = "Simulated Clinical Environment (Synthetic Data)"
}) => {
  return (
    <header className="h-16 bg-white border-b border-slate-200/80 px-6 flex items-center justify-between sticky top-0 z-20 shadow-xs">
      {/* Search Bar */}
      <div className="flex items-center space-x-3 w-96">
        <div className="relative w-full">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search patients, MRN, orders, encounters..."
            onChange={(e) => onSearch && onSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 bg-slate-100/70 border border-transparent rounded-lg text-sm text-slate-800 placeholder-slate-400 focus:bg-white focus:border-slate-300 focus:outline-none transition-all"
          />
        </div>
      </div>

      {/* Center Environment Pill */}
      <div className="hidden lg:flex items-center space-x-2 px-3 py-1 rounded-full bg-amber-50 border border-amber-200/80 text-amber-800 text-xs font-semibold tracking-wide">
        <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
        <span>{environmentName}</span>
      </div>

      {/* Right Controls */}
      <div className="flex items-center space-x-4">
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
            title="Refresh database view"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        )}

        <div className="h-6 w-px bg-slate-200"></div>

        {/* User Badge */}
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-full bg-brand-700 text-white flex items-center justify-center font-semibold text-xs shadow-xs">
            ER
          </div>
          <div className="hidden sm:flex flex-col text-left">
            <span className="text-xs font-semibold text-slate-900 leading-none">Dr. Elena Rostova</span>
            <span className="text-[11px] text-slate-500 leading-tight mt-0.5">Attending Physician • Cardiology</span>
          </div>
        </div>
      </div>
    </header>
  );
};
