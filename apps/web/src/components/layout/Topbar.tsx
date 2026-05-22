"use client";

import { usePathname } from "next/navigation";
import { Search, Bell, ShieldCheck } from "lucide-react";
import { getCurrentNavItem } from "./navigation";

export function Topbar() {
  const pathname = usePathname();
  const currentPage = getCurrentNavItem(pathname).topbarLabel;

  return (
    <header className="h-16 bg-[#0a1322]/80 backdrop-blur-md border-b border-[#1a2c4d] flex items-center justify-between px-6 sticky top-0 z-10">
      <div className="flex items-center gap-3 text-sm text-slate-400">
        <span className="px-2.5 py-1 rounded bg-[#111d33] text-xs font-mono border border-[#1a2c4d] text-[#00e5ff]">SYS-OP</span>
        <span className="text-slate-600">/</span>
        <span className="text-white font-medium">{currentPage}</span>
      </div>
      
      <div className="flex items-center gap-6">
        <div className="relative group">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-[#00e5ff] transition-colors" />
          <input 
            type="text" 
            placeholder="Search Equipment ID or Alarm Code..." 
            className="bg-[#050b14] border border-[#1a2c4d] rounded-full pl-9 pr-4 py-1.5 text-sm w-80 text-slate-300 focus:outline-none focus:border-[#00e5ff] focus:ring-1 focus:ring-[#00e5ff] transition-all placeholder:text-slate-600"
          />
        </div>
        
        <div className="flex items-center gap-4 border-l border-[#1a2c4d] pl-6">
          <div className="flex items-center gap-2 px-3 py-1 bg-[#00cc66]/10 text-[#00cc66] border border-[#00cc66]/30 rounded-full text-xs font-medium shadow-[0_0_8px_rgba(0,204,102,0.15)]">
            <ShieldCheck className="w-3.5 h-3.5" />
            Agent Core Active
          </div>
          <button className="relative p-2 text-slate-400 hover:text-white hover:bg-[#111d33] rounded-full transition-all">
            <Bell className="w-5 h-5" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-[#ffaa00] rounded-full border border-[#0a1322] shadow-[0_0_5px_rgba(255,170,0,0.5)]"></span>
          </button>
        </div>
      </div>
    </header>
  );
}
