"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ComponentType } from "react";
import { Activity, LayoutDashboard, ShieldAlert, CheckSquare, FileText, Settings, Factory, History } from "lucide-react";
import { isNavItemActive, NAV_ITEMS, NAV_SECTIONS, type NavItemId } from "./navigation";

const icons: Record<NavItemId, ComponentType<{ className?: string }>> = {
  dashboard: LayoutDashboard,
  equipment: Activity,
  "active-incidents": ShieldAlert,
  checklists: CheckSquare,
  approvals: FileText,
  "audit-console": History,
  settings: Settings,
};

const iconHoverClass: Record<NavItemId, string> = {
  dashboard: "",
  equipment: "group-hover:text-[#00e5ff]",
  "active-incidents": "group-hover:text-[#ff3366]",
  checklists: "group-hover:text-[#00cc66]",
  approvals: "group-hover:text-[#ffaa00]",
  "audit-console": "group-hover:text-[#00e5ff]",
  settings: "",
};

const activeLinkClass = "flex items-center gap-3 px-3 py-2.5 bg-[#111d33] text-[#00e5ff] rounded-md border border-[#1a2c4d] shadow-[0_0_10px_rgba(0,229,255,0.1)] transition-all hover:bg-[#1a2c4d]";
const inactiveLinkClass = "flex items-center gap-3 px-3 py-2.5 hover:bg-[#111d33] text-slate-400 hover:text-slate-200 rounded-md transition-colors group";

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside data-testid="app-sidebar" className="w-64 border-r border-[#1a2c4d] bg-[#0a1322] flex flex-col h-screen fixed left-0 top-0 text-slate-300 z-20">
      <div className="h-16 flex items-center px-6 border-b border-[#1a2c4d] bg-[#050b14]/50">
        <Factory className="w-6 h-6 text-[#00e5ff] mr-3" />
        <span className="font-bold tracking-widest text-white text-lg drop-shadow-[0_0_8px_rgba(0,229,255,0.4)]">FABMIND</span>
      </div>
      
      <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
        {NAV_SECTIONS.map((section) => (
          <div key={section.id}>
            <div className={`text-xs font-semibold text-slate-500 mb-4 px-2 tracking-wider ${section.id === "diagnosis" ? "" : "mt-8"}`}>
              {section.label}
            </div>
            <div className="space-y-2">
              {NAV_ITEMS.filter((item) => item.section === section.id).map((item) => {
                const isActive = isNavItemActive(item, pathname);
                const Icon = icons[item.id];

                return (
                  <Link
                    key={item.id}
                    href={item.href}
                    data-testid={item.testId}
                    aria-current={isActive ? "page" : undefined}
                    className={isActive ? activeLinkClass : inactiveLinkClass}
                  >
                    {item.badge ? (
                      <>
                        <div className="flex items-center gap-3 flex-1">
                          <Icon className={`w-4 h-4 ${isActive ? "" : `${iconHoverClass[item.id]} transition-colors`}`} />
                          <span className="font-medium text-sm">{item.label}</span>
                        </div>
                        <span className="bg-[#ffaa00] text-black text-[10px] font-bold px-1.5 py-0.5 rounded shadow-[0_0_8px_rgba(255,170,0,0.4)]">{item.badge}</span>
                      </>
                    ) : (
                      <>
                        <Icon className={`w-4 h-4 ${isActive ? "" : `${iconHoverClass[item.id]} transition-colors`}`} />
                        <span className="font-medium text-sm">{item.label}</span>
                      </>
                    )}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
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
