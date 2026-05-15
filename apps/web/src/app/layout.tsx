import type { Metadata } from 'next';
import './globals.css';
import { Sidebar } from '@/components/layout/Sidebar';
import { Topbar } from '@/components/layout/Topbar';

export const metadata: Metadata = {
  title: 'FabMind Agent - Operations Center',
  description: 'Evidence-first troubleshooting platform for Load Port / FOUP Clamp equipment.'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body className="bg-[#050b14] text-slate-300 font-sans min-h-screen">
        <Sidebar />
        <div className="pl-64 flex flex-col min-h-screen bg-[#050b14]">
          <Topbar />
          <main className="flex-1 p-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
