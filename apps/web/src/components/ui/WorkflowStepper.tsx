import { CheckCircle2, ChevronRight, Circle } from "lucide-react";
import Link from "next/link";

export type WorkflowStep = 'DASHBOARD' | 'DIAGNOSIS' | 'CHECKLIST' | 'REPORT' | 'AUDIT';

const steps = [
  { id: 'DASHBOARD', label: 'Dashboard', href: '/' },
  { id: 'DIAGNOSIS', label: 'Diagnosis', href: '/diagnosis-sessions/LP-01-SESSION' },
  { id: 'CHECKLIST', label: 'Checklist', href: '/checklist-runs/RUN-LP-01' },
  { id: 'REPORT', label: 'Report & Approval', href: '/report-drafts/RPT-LP-01' },
  { id: 'AUDIT', label: 'Audit Log', href: '/audit-events' }
];

export function WorkflowStepper({ currentStep }: { currentStep: WorkflowStep }) {
  const currentIndex = steps.findIndex(s => s.id === currentStep);

  return (
    <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none w-full max-w-full">
      {steps.map((step, index) => {
        const isPast = index < currentIndex;
        const isCurrent = index === currentIndex;
        
        return (
          <div key={step.id} className="flex items-center gap-2 shrink-0">
            <Link 
              href={step.href} 
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
                isCurrent 
                  ? 'bg-[#00e5ff]/10 text-[#00e5ff] border border-[#00e5ff]/30 shadow-[0_0_10px_rgba(0,229,255,0.1)]' 
                  : isPast
                  ? 'text-slate-400 hover:text-white bg-slate-800/50 hover:bg-slate-800 border border-transparent'
                  : 'text-slate-600 border border-transparent'
              }`}
            >
              {isPast ? (
                <CheckCircle2 className="w-3.5 h-3.5 text-[#00cc66]" />
              ) : isCurrent ? (
                <div className="w-2 h-2 rounded-full bg-[#00e5ff] animate-pulse" />
              ) : (
                <Circle className="w-3 h-3 text-slate-700" />
              )}
              {step.label}
            </Link>
            {index < steps.length - 1 && (
              <ChevronRight className="w-3.5 h-3.5 text-slate-700 shrink-0" />
            )}
          </div>
        );
      })}
    </div>
  );
}
