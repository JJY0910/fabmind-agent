import Link from "next/link";
import { Activity, LayoutDashboard, ShieldAlert, CheckSquare, FileText, Settings, Factory, History } from "lucide-react";

export function Sidebar() {
  return (
    <aside data-testid="app-sidebar" className="w-64 border-r border-[#1a2c4d] bg-[#0a1322] flex flex-col h-screen fixed left-0 top-0 text-slate-300 z-20">
      <div className="h-16 flex items-center px-6 border-b border-[#1a2c4d] bg-[#050b14]/50">
        <Factory className="w-6 h-6 text-[#00e5ff] mr-3" />
        <span className="font-bold tracking-widest text-white text-lg drop-shadow-[0_0_8px_rgba(0,229,255,0.4)]">FABMIND</span>
      </div>
      
      <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
        <div className="text-xs font-semibold text-slate-500 mb-4 px-2 tracking-wider">DIAGNOSIS</div>
        <Link href="/" data-testid="sidebar-nav-dashboard" className="flex items-center gap-3 px-3 py-2.5 bg-[#111d33] text-[#00e5ff] rounded-md border border-[#1a2c4d] shadow-[0_0_10px_rgba(0,229,255,0.1)] transition-all hover:bg-[#1a2c4d]">
          <LayoutDashboard className="w-4 h-4" />
          <span className="font-medium text-sm">Dashboard</span>
        </Link>
        <Link href="/equipment" data-testid="sidebar-nav-equipment" className="flex items-center gap-3 px-3 py-2.5 hover:bg-[#111d33] text-slate-400 hover:text-slate-200 rounded-md transition-colors group">
          <Activity className="w-4 h-4 group-hover:text-[#00e5ff] transition-colors" />
          <span className="font-medium text-sm">Equipment</span>
        </Link>
        <Link href="/active-incidents" data-testid="sidebar-nav-active-incidents" className="flex items-center gap-3 px-3 py-2.5 hover:bg-[#111d33] text-slate-400 hover:text-slate-200 rounded-md transition-colors group">
          <ShieldAlert className="w-4 h-4 group-hover:text-[#ff3366] transition-colors" />
          <span className="font-medium text-sm">Active Incidents</span>
        </Link>

        <div className="text-xs font-semibold text-slate-500 mt-8 mb-4 px-2 tracking-wider">REPORTS & AUDIT</div>
        <Link href="/checklists" data-testid="sidebar-nav-checklists" className="flex items-center gap-3 px-3 py-2.5 hover:bg-[#111d33] text-slate-400 hover:text-slate-200 rounded-md transition-colors group">
          <CheckSquare className="w-4 h-4 group-hover:text-[#00cc66] transition-colors" />
          <span className="font-medium text-sm">Checklists</span>
        </Link>
        <Link href="/approvals" data-testid="sidebar-nav-approvals" className="flex items-center gap-3 px-3 py-2.5 hover:bg-[#111d33] text-slate-400 hover:text-slate-200 rounded-md transition-colors group">
          <div className="flex items-center gap-3 flex-1">
            <FileText className="w-4 h-4 group-hover:text-[#ffaa00] transition-colors" />
            <span className="font-medium text-sm">Approvals</span>
          </div>
          <span className="bg-[#ffaa00] text-black text-[10px] font-bold px-1.5 py-0.5 rounded shadow-[0_0_8px_rgba(255,170,0,0.4)]">3</span>
        </Link>

        <div className="text-xs font-semibold text-slate-500 mt-8 mb-4 px-2 tracking-wider">SYSTEM</div>
        <Link href="/audit-events" data-testid="sidebar-nav-audit-console" className="flex items-center gap-3 px-3 py-2.5 hover:bg-[#111d33] text-slate-400 hover:text-slate-200 rounded-md transition-colors group">
          <History className="w-4 h-4 group-hover:text-[#00e5ff] transition-colors" />
          <span className="font-medium text-sm">Audit Console</span>
        </Link>
        <Link href="/settings" data-testid="sidebar-nav-settings" className="flex items-center gap-3 px-3 py-2.5 hover:bg-[#111d33] text-slate-400 hover:text-slate-200 rounded-md transition-colors">
          <Settings className="w-4 h-4" />
          <span className="font-medium text-sm">Settings</span>
        </Link>
      </nav>
      
      <div className="p-4 border-t border-[#1a2c4d] bg-[#050b14]/30">
        <div className="bg-[#111d33] rounded-lg p-3 border border-[#1a2c4d] flex items-center gap-3 hover:bg-[#1a2c4d] transition-colors cursor-pointer">
          <div className="w-8 h-8 rounded-full bg-[#00e5ff] flex items-center justify-center text-black font-bold text-xs shadow-[0_0_10px_rgba(0,229,255,0.3)]">
            EN
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-medium text-white">Engineer Kim</span>
            <span className="text-[10px] text-slate-400 font-mono">ID: E-2024-991</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
